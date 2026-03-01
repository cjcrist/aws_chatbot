# iam.py

import logging

from botocore.exceptions import ClientError

logger = logging.getLogger("aws.iam")


def list_users(client, marker=None, max_items=100):
    params = {"MaxItems": max_items}
    if marker:
        params["Marker"] = marker

    try:
        response = client.list_users(**params)
        users = []
        for user in response.get("Users", []):
            users.append(
                {
                    "user_name": user.get("UserName"),
                    "arn": user.get("Arn"),
                    "create_date": user.get("CreateDate").isoformat() if user.get("CreateDate") else None,
                }
            )

        return {
            "users": users,
            "count": len(users),
            "is_truncated": response.get("IsTruncated", False),
            "next_token": response.get("Marker"),
        }
    except ClientError as e:
        return {"users": [], "count": 0, "is_truncated": False, "next_token": None, "error": str(e)}


def get_user_permissions(client, user_name):
    data = {
        "user_name": user_name,
        "attached_user_policies": [],
        "inline_user_policies": [],
        "groups": [],
        "group_attached_policies": {},
        "group_inline_policies": {},
    }

    try:
        user_policies = client.list_attached_user_policies(UserName=user_name)
        data["attached_user_policies"] = [policy["PolicyName"] for policy in user_policies.get("AttachedPolicies", [])]

        inline_user_policies = client.list_user_policies(UserName=user_name)
        data["inline_user_policies"] = inline_user_policies.get("PolicyNames", [])

        groups = client.list_groups_for_user(UserName=user_name)
        group_names = [group["GroupName"] for group in groups.get("Groups", [])]
        data["groups"] = group_names

        for group_name in group_names:
            attached = client.list_attached_group_policies(GroupName=group_name)
            data["group_attached_policies"][group_name] = [
                policy["PolicyName"] for policy in attached.get("AttachedPolicies", [])
            ]

            inline = client.list_group_policies(GroupName=group_name)
            data["group_inline_policies"][group_name] = inline.get("PolicyNames", [])

        return data
    except ClientError as e:
        return {"user_name": user_name, "error": str(e)}
