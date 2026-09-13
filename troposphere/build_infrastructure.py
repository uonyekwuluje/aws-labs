#!/usr/bin/env python3
import click
from enum import Enum
from functools import lru_cache
from copy import copy
import sys
import yaml
from tabulate import tabulate
import boto3

from troposphere import Template, GetAtt
from troposphere import route53
from troposphere import ec2

from infra_modules import create_vpc, create_instances, create_security_group

OCTET_ADDRESS = {
    "stg": "10.21",
    "dev": "10.22",
    "uit": "10.23",
    "prod": "10.24",
}

private_hosted_zone = "infralabs.io"
aws_build_region = "us-east-1"

ubuntu24_ami_id = "ami-0e2c8caa4b6378d8c"
ubuntu26_ami_id = "ami-0b6d9d3d33ba97d99"

INSTANCE_CONFIG_DB = [
    ["bastion", "t2.medium", "publicSubnet1a", ubuntu24_ami_id, "40"],
    ["rancher", "t2.large", "publicSubnet1b", ubuntu26_ami_id, "40"],
    ["kubemaster", "t3.large", "privateSubnet1a", ubuntu26_ami_id, "100"],
    ["kubenode01", "t3.large", "privateSubnet1a", ubuntu26_ami_id, "100"],
    ["kubenode02", "t3.large", "privateSubnet1b", ubuntu26_ami_id, "100"],
    ["kubenode03", "t3.large", "privateSubnet1b", ubuntu26_ami_id, "100"]
]


@click.group(invoke_without_command=True, chain=True)
def cli():
    pass


# Delete Stacks
@cli.command()
@click.option('-v', '--vpc_name', required=True,
              help="The VPC Name")
@click.option('-r', '--region', default='us-east-1',
              help="AWS VPC Region")
def delete_stack(vpc_name, region):
    stack_names = [f"{vpc_name}-ec2-stack", f"{vpc_name}-security-group-stack", f"{vpc_name}-vpc-stack"]
    vpc_name = vpc_name.lower()
    cf_resource = boto3.resource('cloudformation', region_name=region)
    for current_stack in stack_names:
        print(f'Deleting stack, {current_stack} in region, {region}')

        # Delete the stack
        stack = cf_resource.Stack(current_stack)
        stack.delete()

        # Wait for stack deletion to complete
        waiter = boto3.client('cloudformation').get_waiter('stack_delete_complete')
        waiter.wait(StackName=current_stack)

        print(f"Stack {current_stack} deleted successfully from region {region}")


# Create VPC Stack
@cli.command()
@click.option('-v', '--vpc_name', default='dev',
              help="The VPC Name")
@click.option('-r', '--region', default='us-east-1',
              help="AWS VPC Region")
def create_update_vpc_stack(vpc_name, region):
    vpc_name = vpc_name.lower()
    stack_name = f"{vpc_name}-vpc-stack"
    hostedzone_name = f"{vpc_name}.{private_hosted_zone}"
    create_vpc.create_update_cfn_template(vpc_name, region, hostedzone_name, stack_name, OCTET_ADDRESS[vpc_name])


# Create Security Groups
@cli.command()
@click.option('-v', '--vpc_name', default='dev',
              help="The VPC Name")
def create_security_group_stack(vpc_name):
    stack_name = f"{vpc_name}-security-group-stack"
    create_security_group.create_update_security_group_template(vpc_name, stack_name)


# Create Instances
@cli.command()
@click.option('-v', '--vpc_name', default='dev',
              help="The VPC Name")
def create_instance_stack(vpc_name):
    stack_name = f"{vpc_name}-ec2-stack"
    create_instances.create_update_instance_template(vpc_name, stack_name,
                                                     private_hosted_zone,
                                                     aws_build_region,
                                                     INSTANCE_CONFIG_DB)


if __name__ == '__main__':
    cli()
