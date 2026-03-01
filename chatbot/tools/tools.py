from langchain.tools import tool

from ..aws import ec2
from ..aws import iam
from ..aws import s3
from ..aws import session


@tool("get_s3_buckets_and_policies", description="Get S3 buckets with policy and ACL details", return_direct=False)
def get_s3_buckets_and_policies():
    """Get S3 buckets and access-related details so the model can determine exposure."""
    client = session.get_client("s3")
    return s3.list_buckets_with_access(client)


@tool("list_s3_bucket_items",
      description="List objects in an S3 bucket with optional prefix and pagination token",
      return_direct=False)
def list_s3_bucket_items(bucket, prefix="", token="", max_keys=1000):
    """List objects in an S3 bucket with optional prefix and pagination token."""
    client = session.get_client("s3")
    next_token = token or None
    return s3.list_items(client, bucket, prefix=prefix, next_token=next_token, max_keys=max_keys)


@tool("get_ec2_instance_size_by_ip",
      description="Get EC2 instance type by private or public IP address",
      return_direct=False)
def get_ec2_instance_size_by_ip(ip_address):
    """Get EC2 instance type by private or public IP address."""
    client = session.get_client("ec2")
    instance = ec2.get_instance_by_ip(client, ip_address)
    return ec2.summarize_instance(instance)


@tool("get_iam_user_permissions",
      description="Get IAM user permissions from user and group policy attachments",
      return_direct=False)
def get_iam_user_permissions(user_name):
    """Get IAM user permissions from user and group policy attachments."""
    client = session.get_client("iam")
    return iam.get_user_permissions(client, user_name)


tools = [
    get_s3_buckets_and_policies,
    list_s3_bucket_items,
    get_ec2_instance_size_by_ip,
    get_iam_user_permissions,
]
