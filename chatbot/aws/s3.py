# s3.py

import json
import logging

from botocore.exceptions import ClientError

logger = logging.getLogger("aws.s3")


def list_items(client, bucket, prefix="", next_token=None, max_keys=1000):
    params = {"Bucket": bucket, "Prefix": prefix, "MaxKeys": max_keys}

    if next_token:
        params["ContinuationToken"] = next_token

    response = client.list_objects_v2(**params)
    items = [obj["Key"] for obj in response.get("Contents", [])]

    return {
        "items": items,
        "next_token": response.get("NextContinuationToken"),
        "count": len(items),
        "is_truncated": response.get("IsTruncated", False),
    }


def get_bucket_policy(client, bucket):
    try:
        response = client.get_bucket_policy(Bucket=bucket)
        return json.loads(response.get("Policy", "{}"))
    except ClientError:
        return None


def get_bucket_acl(client, bucket):
    try:
        acl = client.get_bucket_acl(Bucket=bucket)
        return acl.get("Grants", [])
    except ClientError:
        return []


def list_buckets_with_access(client):
    response = client.list_buckets()
    buckets = []

    for bucket in response.get("Buckets", []):
        bucket_name = bucket.get("Name")
        if not bucket_name:
            continue

        buckets.append(
            {
                "name": bucket_name,
                "policy": get_bucket_policy(client, bucket_name),
                "acl_grants": get_bucket_acl(client, bucket_name),
            }
        )

    return {"buckets": buckets}
