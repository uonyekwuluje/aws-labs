#!/usr/bin/env python3
import click
from enum import Enum
from functools import lru_cache
from copy import copy
import sys
import yaml
from tabulate import tabulate
import boto3

import csv
import json
import logging
import os
import re
import ipaddress
from datetime import datetime, timedelta

from botocore.exceptions import ClientError

transfer_s3_bucket = 'infracid-transfer-ip-allowlist'

s3 = boto3.client('s3')
ec2 = boto3.client('ec2')

tag_key = "trfstate"
tag_value_current = "current"
tag_value_previous = "previous"

# key: sftpd_transfer_sg  value:prod-transfer-sg
tag_value_transfer_sg = "prod-transfer-sg"

# Validate IP Address
def is_valid_ipv4_address(address: str) -> bool:
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        pass


    try:
        ipaddress.ip_network(address, strict=False)
        if '/' in address:
            return True
    except ValueError:
        pass

    return False


# Add IP Addresses to user file in S3 bucket
def _add_ip_entry(username, ip_cidr):
    print(f"Add IP Address for user {username}")
    s3_file_object_name = f"{username}.txt"
    local_file = f"local-{username}.txt"
    ip_cidr_address = f"{ip_cidr}/32"

    values = set()

    # Validate IP Address
    #print(is_valid_ipv4_address(ip_cidr))
    if not is_valid_ipv4_address(ip_cidr_address):
        print(f"{ip_cidr_address} is not a valid address")
        return

    # Create Local File
    with open(local_file, "w") as f:
        f.write(f"{ip_cidr_address}\n")

    # Download S3 Object
    s3.download_file(transfer_s3_bucket, s3_file_object_name, s3_file_object_name)

    with open(local_file, "r") as f1:
        for line in f1:
            values.add(line.strip())

    with open(s3_file_object_name, "r") as f2:
        for line in f2:
            values.add(line.strip())

    with open(s3_file_object_name, "w") as out:
        for v in sorted(values):
            out.write(v + "\n")

    # Upload file to S3
    s3.upload_file(s3_file_object_name, transfer_s3_bucket, s3_file_object_name)
    print(f"IP Addresses {ip_cidr_address} for user {username} added")



# Remove IP Address from user files in S3 bucket
def _remove_ip_entry(username, ip_cidr):
    print(f"Remove IP Address {ip_cidr}")
    s3_file_object_name = f"{username}.txt"
    ip_cidr_address = f"{ip_cidr}/32"

    # Download S3 Object
    s3.download_file(transfer_s3_bucket, s3_file_object_name, s3_file_object_name)

    with open(s3_file_object_name) as f1:
        cleaned = [
                line.strip() + "\n"
                for line in f1
                if line.strip() and line.strip() != ip_cidr_address
                ]        

    with open(s3_file_object_name, "w") as out:
        out.writelines(cleaned)

    # Upload Updated file to S3
    s3.upload_file(s3_file_object_name, transfer_s3_bucket, s3_file_object_name)


# List IP Addresses of users in S3 bucket
def _list_ip_addresses():
    response = s3.list_objects_v2(Bucket=transfer_s3_bucket)

    for obj in response.get('Contents', []):
        key = obj['Key']
        print(f"\n--- {key} ---")

        file_obj = s3.get_object(Bucket=transfer_s3_bucket, Key=key)
        for line in file_obj['Body'].iter_lines():
            print({'Cidr': f"{line.decode('utf-8')}", 'Description': f"{key} ssh rule"})




# Add IP Addresse Entries to Prefixlist 
def _add_addresses_to_prefixlist():
    response = s3.list_objects_v2(Bucket=transfer_s3_bucket)

    entries_list = list()

    # Get current Prefixlist ID
    current_prefix_list_id = get_current_prefixlist_id()

    # Need current version for modification
    pl = ec2.describe_managed_prefix_lists(
        PrefixListIds=[current_prefix_list_id]
    )['PrefixLists'][0]

    current_version = pl['Version']

    print(f"Adding Entries to {current_prefix_list_id}. Version Number => {current_version}")
    for obj in response.get('Contents', []):
        key = obj['Key']
        print(f"\n--- {key} ---")

        file_obj = s3.get_object(Bucket=transfer_s3_bucket, Key=key)
        for line in file_obj['Body'].iter_lines():
            entries_list.append({'Cidr': f"{line.decode('utf-8')}", 'Description': f"{key} ssh rule"})

    # Append entries & update managed prefix list
    response = ec2.modify_managed_prefix_list(
        PrefixListId=current_prefix_list_id,
        CurrentVersion=current_version,
        AddEntries=entries_list
    )








# Remove All IP Entries in PrefixList
def _remove_addresses_in_prefixlist():
    # Get current Prefixlist ID
    current_prefix_list_id = get_current_prefixlist_id()

    # Step 1: Get current version and entries
    response = ec2.get_managed_prefix_list_entries(
        PrefixListId=current_prefix_list_id
    )

    entries = response['Entries']

    if not entries:
        print("No entries to delete.")
        return

    # Need current version for modification
    pl = ec2.describe_managed_prefix_lists(
        PrefixListIds=[current_prefix_list_id]
    )['PrefixLists'][0]

    current_version = pl['Version']

    print(f"Removing Entries {current_prefix_list_id}. Version Number => {current_version}")
    # Step 2: Remove entries in batches (max 100 per request)
    batch_size = 100
    for i in range(0, len(entries), batch_size):
        batch = entries[i:i + batch_size]

        remove_entries = [
            {
                'Cidr': e['Cidr']
            }
            for e in batch
        ]

        print(f"Removing batch {i // batch_size + 1}...")
        ec2.modify_managed_prefix_list(
            PrefixListId=current_prefix_list_id,
            CurrentVersion=current_version,
            RemoveEntries=remove_entries
        )

        # Version increments after each modify call
        current_version += 1

    print("All entries removed.")





# Get Prefixlist ID for current
def get_current_prefixlist_id():
    response = ec2.describe_managed_prefix_lists(
        Filters=[
            {
                'Name': f'tag:{tag_key}',
                'Values': [tag_value_current]
            }
        ]
    )

    # Extract PrefixListId
    for pl in response['PrefixLists']:
        #print(f"Prefix List Name: {pl['PrefixListName']}, ID: {pl['PrefixListId']}")
        return pl['PrefixListId']


# Get Prefixlist IDs
def get_prefix_list_ids_by_tag(tag_key):
    paginator = ec2.get_paginator('describe_managed_prefix_lists')
    prefix_list_ids = []

    response_iterator = paginator.paginate(
        Filters = [
            {
                'Name': 'tag-key',
                'Values': [tag_key]
            }
        ]
    ) 
    for page in response_iterator:
        for pl in page.get('PrefixLists', []):
            prefix_list_ids.append(pl['PrefixListId'])
            #print(pl)
    return prefix_list_ids


# Get current prefixlist resource tags
def get_current_tags(prefix_list_id):
    response = ec2.describe_managed_prefix_lists(
        PrefixListIds=[prefix_list_id]
    )
    tags = response["PrefixLists"][0].get("Tags", [])
    return {t["Key"]: t["Value"] for t in tags}


# Return Toggled Tag Values
def toggle(value):
    if value == tag_value_current:
        return tag_value_previous
    else:
        return tag_value_current

# Update and swap tags
def update_tags(prefix_list_id):
    current_tags = get_current_tags(prefix_list_id)

    current_value = current_tags.get(tag_key, tag_value_current)  # default if missing
    new_value = toggle(current_value)

    current_tags[tag_key] = new_value

    tag_list = [{"Key": k, "Value": v} for k, v in current_tags.items() if not k.lower().startswith('aws:')]

    ec2.create_tags(
        Resources=[prefix_list_id],
        Tags=tag_list
    )
    print(f"{prefix_list_id}: {current_value} -> {new_value}")





# Change/Swap PrefixList Tags 
def _update_prefixlist():
    prefix_list_ids = get_prefix_list_ids_by_tag(tag_key)

    for pl_id in prefix_list_ids:
        update_tags(pl_id)


   


def _security_group_update():
    print("==============================")
    print("Security Group Sync Operations")
    print("==============================")

    # Update/Change prefixlist 
    _update_prefixlist()

    # Remove IP Address from Current Prefix List
    _remove_addresses_in_prefixlist()

    # Add IP Addresses to Current Prefix List
    _add_addresses_to_prefixlist()

    # Get Security Group ID [tag_value_transfer_sg = "prod-transfer-sg"]
    response = ec2.describe_security_groups(
        Filters=[
          {
            'Name': 'tag:sftpd_transfer_sg',
            'Values': [tag_value_transfer_sg]
          }
        ]
    )
    sg_ids = [sg['GroupId'] for sg in response['SecurityGroups']]
    if len(sg_ids) == 1:
        sg_ids = "".join(sg_ids)

    current_prefix_list_id = get_current_prefixlist_id()

    print(f"Security Group ID => {sg_ids}")
    print(f"Prefix List ID    => {current_prefix_list_id}")

    try:
        response = ec2.describe_security_groups(GroupIds=[sg_ids])
        sg = response['SecurityGroups'][0]

        # Revoke All Ingress Rules In Security Group
        if sg['IpPermissions']:
            ec2.revoke_security_group_ingress(
                GroupId=sg_ids,
                IpPermissions=sg['IpPermissions']
            )

        # Create Security Group
        ec2.authorize_security_group_ingress(
            GroupId=sg_ids,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'PrefixListIds': [
                        {
                            'Description': 'SSH Access with Prefix List',
                            'PrefixListId': current_prefix_list_id
                        },
                    ]                
                }
            ]
        )
    except ClientError as e:
        print(f"Error: {e}")
        # Create Security Group
        ec2.authorize_security_group_ingress(
            GroupId=sg_ids,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'PrefixListIds': [
                        {
                            'Description': 'SSH Access with Prefix List',
                            'PrefixListId': current_prefix_list_id
                        },
                    ]
                }
            ]
        )













@click.group(invoke_without_command=True, chain=True)
def cli():
    pass


# Add IP Entry to allow list bucket
@cli.command()
@click.option("-u", "--username", required=True)
@click.option("-i", "--ip-cidr", required=True)
def adduser_ip_addresses_s3(username, ip_cidr):
    """Save User IP Addresses"""
    _add_ip_entry(
        username,
        ip_cidr,
    )
    logging.info(f"IP Addresses for user {username} added")


# Remove IP Entry from allow list
@cli.command()
@click.option("-u", "--username", required=True)
@click.option("-i", "--ip-cidr", required=True)
def removeuser_ip_addresses_s3(username, ip_cidr):
    """Save User IP Addresses"""
    _remove_ip_entry(
        username,
        ip_cidr,
    )
    logging.info(f"{ip_cidr} IP Address Removed")


# List All Addresses from Allow List
@cli.command()
def list_ip_addresses():
    """List IP Addresses"""
    _list_ip_addresses()


# Delete/Reset All Addresses from Allow List
@cli.command()
def delete_ip_addresses():
    """List IP Addresses"""
    _delete_ip_addresses()


# Prefix List Operations
@cli.command()
def prefixlist_ops():
    """PrefixList Operations"""
    _update_prefixlist()

# Synchronize and update Transfer Security Group
@cli.command()
def security_group_syncops():
    """Synchronize and update security group"""
    _security_group_update()








if __name__ == '__main__':
    cli()
