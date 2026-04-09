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
prefix_list_id = 'pl-077c0ce2e42800133'

s3 = boto3.client('s3')
ec2 = boto3.client('ec2')


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


# Add IP Addresses to Allowed List
def _add_ip_entry(username, ip_cidr):
    print(f"Add IP Address for user {username}")
    s3_file_object_name = f"{username}.txt"
    local_file = f"local-{username}.txt"

    values = set()

    # Validate IP Address
    #print(is_valid_ipv4_address(ip_cidr))
    if not is_valid_ipv4_address(ip_cidr):
        print(f"{ip_cidr} is not a valid address")
        return

    # Create Local File
    with open(local_file, "w") as f:
        f.write(f"{ip_cidr}\n")

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
    print(f"IP Addresses {ip_cidr} for user {username} added")



# Remove IP Address from Allowed List
def _remove_ip_entry(username, ip_cidr):
    print(f"Remove IP Address {ip_cidr}")
    s3_file_object_name = f"{username}.txt"

    # Download S3 Object
    s3.download_file(transfer_s3_bucket, s3_file_object_name, s3_file_object_name)

    with open(s3_file_object_name) as f1:
        cleaned = [
                line.strip() + "\n"
                for line in f1
                if line.strip() and line.strip() != ip_cidr
                ]        

    with open(s3_file_object_name, "w") as out:
        out.writelines(cleaned)

    # Upload Updated file to S3
    s3.upload_file(s3_file_object_name, transfer_s3_bucket, s3_file_object_name)


# List IP Addresses from List
def _list_ip_addresses():
    response = s3.list_objects_v2(Bucket=transfer_s3_bucket)

    entries_list = list()

    # Need current version for modification
    pl = ec2.describe_managed_prefix_lists(
        PrefixListIds=[prefix_list_id]
    )['PrefixLists'][0]

    current_version = pl['Version']


    for obj in response.get('Contents', []):
        key = obj['Key']
        print(f"\n--- {key} ---")

        # Get object content
        #file_obj = s3.get_object(Bucket=transfer_s3_bucket, Key=key)
        #content = file_obj['Body'].read().decode('utf-8')
        #print(content)

        file_obj = s3.get_object(Bucket=transfer_s3_bucket, Key=key)
        for line in file_obj['Body'].iter_lines():
            entries_list.append({'Cidr': f"{line.decode('utf-8')}", 'Description': f"{key} ssh rule"})

    #print(entries_list)
    # Append entries & update managed prefix list
    response = ec2.modify_managed_prefix_list(
        PrefixListId=prefix_list_id,
        CurrentVersion=current_version,
        AddEntries=entries_list
    )
    #print(response)

# Delete IP Address List
def _delete_ip_addresses():
    ## ================ Test Code Path ============== #
    #response = ec2.describe_managed_prefix_lists(
    #    PrefixListIds=[prefix_list_id]
    #)

    ##print(response)
    #print(response['PrefixLists'][0]['PrefixListId'])
    #print(response['PrefixLists'][0]['Version'])
    ## ================================================ #

    # Step 1: Get current version and entries
    response = ec2.get_managed_prefix_list_entries(
        PrefixListId=prefix_list_id
    )

    entries = response['Entries']

    if not entries:
        print("No entries to delete.")
        return

    # Need current version for modification
    pl = ec2.describe_managed_prefix_lists(
        PrefixListIds=[prefix_list_id]
    )['PrefixLists'][0]

    current_version = pl['Version']

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
            PrefixListId=prefix_list_id,
            CurrentVersion=current_version,
            RemoveEntries=remove_entries
        )

        # Version increments after each modify call
        current_version += 1

    print("All entries removed.")








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






if __name__ == '__main__':
    cli()
