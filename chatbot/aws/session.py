# session.py

import json
import logging
import os
from datetime import datetime, timezone

import boto3
from dateutil.parser import parse as parse_date
from dateutil.tz import tz

logger = logging.getLogger("aws.session")


def get_sso_credentials():
    sso_dir = os.path.expanduser("~/.aws/sso/cache")
    if not os.path.exists(sso_dir):
        logger.info("SSO credentials not found")
        return None

    for fn in os.listdir(sso_dir):
        fp = os.path.join(sso_dir, fn)
        try:
            with open(fp, "r") as f:
                creds = json.load(f)

            if "accessToken" not in creds or "expiresAt" not in creds:
                continue

            expiration_time = parse_date(creds["expiresAt"])
            if expiration_time.tzinfo is None:
                expiration_time = expiration_time.replace(tzinfo=tz.tzutc())

            if expiration_time > datetime.now(timezone.utc):
                return creds
        except Exception:
            logger.warning(f"Error processing SSO cache file: {fp}. Skipping.")

    logger.info("No valid SSO credentials found")
    return None


def get_session(region=None):
    region_name = region or os.getenv("AWS_REGION") or "us-east-1"
    profile = os.getenv("AWS_PROFILE")

    if profile:
        return boto3.Session(profile_name=profile, region_name=region_name)

    return boto3.Session(region_name=region_name)


def get_client(service_name, region=None):
    use_localstack_value = os.getenv("USE_LOCALSTACK", "false").lower()
    if use_localstack_value not in ("true", "false"):
        raise ValueError("USE_LOCALSTACK must be true or false")
    use_localstack = use_localstack_value == "true"

    session = get_session(region)
    endpoint_url = os.getenv("LOCALSTACK_URL")

    if use_localstack:
        url = endpoint_url or "http://localhost:4566"
        return session.client(
            service_name,
            endpoint_url=url,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        )

    return session.client(service_name)
