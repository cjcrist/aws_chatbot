# iam.py

import logging

from botocore.exceptions import ClientError

logger = logging.getLogger("aws.iam")


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
