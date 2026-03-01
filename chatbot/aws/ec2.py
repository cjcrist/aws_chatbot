# ec2.py
import logging

logger = logging.getLogger("aws.ec2")

def get_instance_by_ip(client, ip_address):
    response = client.describe_instances(
        Filters=[{"Name": "private-ip-address", "Values": [ip_address]}]
    )
    instances = _instances_from_response(response)
    if instances:
        return instances[0]

    response = client.describe_instances(
        Filters=[{"Name": "ip-address", "Values": [ip_address]}]
    )
    instances = _instances_from_response(response)
    if instances:
        return instances[0]

    return None


def _instances_from_response(response):
    instances = []
    for reservation in response.get("Reservations", []):
        instances.extend(reservation.get("Instances", []))
    return instances


def summarize_instance(instance):
    if not instance:
        return {"found": False}

    return {
        "found": True,
        "instance_id": instance.get("InstanceId"),
        "instance_type": instance.get("InstanceType"),
        "private_ip": instance.get("PrivateIpAddress"),
        "public_ip": instance.get("PublicIpAddress"),
        "state": instance.get("State", {}).get("Name"),
    }
