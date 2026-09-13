import boto3
from botocore.exceptions import ClientError

client = boto3.client('ec2')
route53 = boto3.client("route53")
cfn_template = boto3.client('cloudformation')


def get_vpc_id(vpc_name):
    """ Get VPC ID """
    response = client.describe_vpcs(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    vpc_name,
                ]
            }
        ]
    )
    resp = response['Vpcs']
    if resp:
        return resp[0]['VpcId']
    else:
       return f"vpc {vpc_name} not found"


def get_hosted_zone_id(vpc_name, zone_name, vpc_region):
    """ Get the ID of a private hostedzone """
    vpc_id = get_vpc_id(vpc_name)
    hostedzone_name = f"{vpc_name}.{zone_name}"

    response = route53.list_hosted_zones_by_vpc(
        VPCId=vpc_id,
        VPCRegion=vpc_region
    )

    hostedzone_name = hostedzone_name.rstrip(".") + "."

    for zone in response["HostedZoneSummaries"]:
        if zone["Name"] == hostedzone_name:
            return zone["HostedZoneId"]

    return None



def get_subnet_id(vpc_name, subnet_name):
    """ Get Subnet ID """
    subnet_name = f"{vpc_name}-{subnet_name}"
    vpc_id = get_vpc_id(vpc_name)

    response = client.describe_subnets(
        Filters=[
            {"Name": "tag:Name", "Values": [subnet_name]},
            {"Name": "vpc-id", "Values": [vpc_id]},
        ]
    )
    resp_val = response['Subnets'][0]['SubnetId']
    if resp_val:
       return resp_val
    else:
       print('Subnet Not Found')


def get_security_group_id(vpc_name, security_group_name):
    """ Get Security Group ID """
    security_group = f"{vpc_name}-{security_group_name}"
    vpc_id = get_vpc_id(vpc_name)

    response = client.describe_security_groups(
        Filters=[
          {"Name": "tag:Name", "Values": [security_group]},
          {"Name": "vpc-id", "Values": [vpc_id]},
        ]
    )
    resp_sg_val = response['SecurityGroups'][0]['GroupId']
    if resp_sg_val:
       return resp_sg_val
    else:
       print('Security Group Not Found')



def stack_exists(stack_name, required_status):
    try:
        response = cfn_template.describe_stacks(
            StackName=stack_name
        )
    except ClientError:
        return False
    return response['Stacks'][0]['StackStatus'] == required_status
