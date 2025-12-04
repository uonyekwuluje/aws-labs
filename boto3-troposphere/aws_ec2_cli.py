import re
import sys
from functools import lru_cache

import boto3
import click
from botocore.exceptions import ClientError
from dateutil import parser
from tabulate import tabulate


@lru_cache
def get_all_ec2_instance_types():
    """List All Instance Types in given Region"""
    all_instance_types = set()
    describe_args = {}
    while True:
        response = boto3.client("ec2").describe_instance_types(**describe_args)
        for r in response["InstanceTypes"]:
            types = r["InstanceType"]
            all_instance_types.update(types.split("|"))
        if "NextToken" not in response:
            break
        describe_args["NextToken"] = response["NextToken"]
    return all_instance_types


if __name__ == '__main__':
    print(get_all_ec2_instance_types())
