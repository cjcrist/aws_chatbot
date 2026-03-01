#!/usr/bin/env bash
set -euo pipefail

export AWS_REGION="${AWS_REGION:-us-east-1}"

echo "==> Seeding LocalStack resources..."

# -----------------------------
# S3 buckets
# -----------------------------
awslocal s3api create-bucket --bucket public-bucket >/dev/null
awslocal s3api create-bucket --bucket public-bucket-2 >/dev/null
awslocal s3api create-bucket --bucket public-bucket-3 >/dev/null
awslocal s3api create-bucket --bucket private-bucket >/dev/null
awslocal s3api create-bucket --bucket private-bucket-2 >/dev/null
awslocal s3api create-bucket --bucket private-bucket-3 >/dev/null
awslocal s3api create-bucket --bucket data-bucket >/dev/null

echo "menu: tacos" > /tmp/menu.txt
echo "orders,amount\n1,42\n2,18" > /tmp/orders.csv
echo '{"hello":"world"}' > /tmp/data.json

awslocal s3 cp /tmp/menu.txt s3://data-bucket/menu.txt >/dev/null
awslocal s3 cp /tmp/orders.csv s3://data-bucket/orders.csv >/dev/null
awslocal s3 cp /tmp/data.json s3://data-bucket/data.json >/dev/null

awslocal s3api put-bucket-policy \
  --bucket public-bucket \
  --policy file:///etc/localstack/init/ready.d/public-bucket-policy.json

awslocal s3api put-bucket-acl --bucket public-bucket --acl public-read

awslocal s3api put-bucket-policy \
  --bucket public-bucket-2 \
  --policy '{"Version":"2012-10-17","Statement":[{"Sid":"AllowPublicRead","Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::public-bucket-2/*"}]}'
awslocal s3api put-bucket-acl --bucket public-bucket-2 --acl public-read

awslocal s3api put-bucket-policy \
  --bucket public-bucket-3 \
  --policy '{"Version":"2012-10-17","Statement":[{"Sid":"AllowPublicRead","Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::public-bucket-3/*"}]}'
awslocal s3api put-bucket-acl --bucket public-bucket-3 --acl public-read

# -----------------------------
# IAM users, groups, policies
# -----------------------------
awslocal iam create-user --user-name alice >/dev/null || true
awslocal iam create-user --user-name bob >/dev/null || true

awslocal iam create-group --group-name Admins >/dev/null || true
awslocal iam create-group --group-name Auditors >/dev/null || true

ADMIN_ARN=$(awslocal iam create-policy \
  --policy-name AdminAccess \
  --policy-document file:///etc/localstack/init/ready.d/AdminAccess.json \
  --query 'Policy.Arn' --output text 2>/dev/null || true)

READONLY_ARN=$(awslocal iam create-policy \
  --policy-name ReadOnlyAccess \
  --policy-document file:///etc/localstack/init/ready.d/ReadOnlyAccess.json \
  --query 'Policy.Arn' --output text 2>/dev/null || true)

# If policies already exist (persistence enabled), fetch them
if [[ -z "${ADMIN_ARN:-}" || "${ADMIN_ARN:-}" == "None" ]]; then
  ADMIN_ARN=$(awslocal iam list-policies --scope Local \
    --query "Policies[?PolicyName=='AdminAccess'].Arn | [0]" --output text)
fi

if [[ -z "${READONLY_ARN:-}" || "${READONLY_ARN:-}" == "None" ]]; then
  READONLY_ARN=$(awslocal iam list-policies --scope Local \
    --query "Policies[?PolicyName=='ReadOnlyAccess'].Arn | [0]" --output text)
fi

awslocal iam attach-group-policy --group-name Admins --policy-arn "$ADMIN_ARN" >/dev/null || true
awslocal iam attach-group-policy --group-name Auditors --policy-arn "$READONLY_ARN" >/dev/null || true

awslocal iam add-user-to-group --user-name alice --group-name Admins >/dev/null || true
awslocal iam add-user-to-group --user-name bob --group-name Auditors >/dev/null || true

# -----------------------------
# EC2 minimal setup
# -----------------------------
VPC_ID=$(awslocal ec2 create-vpc --cidr-block 10.0.0.0/16 --query 'Vpc.VpcId' --output text)
SUBNET_ID=$(awslocal ec2 create-subnet --vpc-id "$VPC_ID" --cidr-block 10.0.1.0/24 --query 'Subnet.SubnetId' --output text)

SG_ID=$(awslocal ec2 create-security-group \
  --group-name aws-chatbot-sg \
  --description "aws chatbot sg" \
  --vpc-id "$VPC_ID" \
  --query 'GroupId' --output text)

INSTANCE_ID=$(awslocal ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.micro \
  --subnet-id "$SUBNET_ID" \
  --security-group-ids "$SG_ID" \
  --query 'Instances[0].InstanceId' --output text)

PRIVATE_IP=$(awslocal ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)

echo "==> Seed complete."
echo "==> Buckets: public-bucket, public-bucket-2, public-bucket-3, private-bucket, private-bucket-2, private-bucket-3, data-bucket"
echo "==> Users: alice (Admins), bob (Auditors)"
echo "==> Policies: AdminAccess, ReadOnlyAccess"
echo "==> EC2 Private IP: $PRIVATE_IP"
