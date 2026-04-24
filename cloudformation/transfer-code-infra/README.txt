cat README.txt 

# Validate Template
# ---------------------
aws cloudformation validate-template --template-body file://cfn_transfer_stack.yml

# Create Template
# ---------------------
aws cloudformation create-stack --stack-name uatsftpd-stack --capabilities CAPABILITY_NAMED_IAM --template-body file://cfn_transfer_stack.yml

# Update Template
# ---------------------
aws cloudformation update-stack --stack-name uatsftpd-stack --capabilities CAPABILITY_NAMED_IAM --template-body file://cfn_transfer_stack.yml

# Delete Cloudformation Stacks
# ------------------------------
aws cloudformation delete-stack --stack-name uatsftpd-stack













# Delete S3 Bucket Contents
-------------------------------
aws s3 rb s3://transferprod-ucheonyekwuluje.com/ --force
aws s3 rb s3://infracid-transfer-ip-allowlist/ --force


aws s3api delete-objects --bucket infracid-transfer-ip-allowlist --delete "$(aws s3api list-object-versions --bucket infracid-transfer-ip-allowlist --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"

aws s3api delete-objects --bucket infracid-transfer-ip-allowlist --delete "$(aws s3api list-object-versions --bucket infracid-transfer-ip-allowlist --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}')"





ssh-keygen -b 2048 -t rsa -f ~/.ssh/id_rsa_user -q -N "" -C sftpd-user-key
>>

cat ~/.ssh/id_rsa_user
>>

cat ~/.ssh/id_rsa_user.pub 
>>




aws transfer start-file-transfer --connector-id [c-id] --send-file-paths "/[bucket]/file.txt" --remote-directory-path "/incoming"


# Server Name
----------------------------------
server: transferprod.ucheonyekwuluje.com


# Test SFTP
----------------------------------
sftp -i ~/.ssh/id_rsa_tstark uchetest@transferuat1.operations.infracid.com          [Fail]
sftp -i ~/.ssh/id_rsa_user user1@transferprod.ucheonyekwuluje.com      [Pass]


# List Transfer Server
----------------------------------
aws transfer list-servers
>>
{
    "Servers": [
        {
            "Arn": "arn:aws:transfer:us-east-1:922271878465:server/s-15ec9a85fcb44b90a",
            "Domain": "S3",
            "IdentityProviderType": "SERVICE_MANAGED",
            "EndpointType": "PUBLIC",
            "ServerId": "s-15ec9a85fcb44b90a",
            "State": "ONLINE",
            "UserCount": 2
        }
    ]
}



aws transfer list-users --server-id s-15ec9a85fcb44b90a
aws transfer describe-user --user-name user1 --server-id s-15ec9a85fcb44b90a

aws transfer describe-user --user-name tstark --server-id s-15ec9a85fcb44b90a | jq .User.UserName
aws transfer describe-user --user-name tstark --server-id s-15ec9a85fcb44b90a | jq .User.SshPublicKeys
aws transfer describe-user --user-name tstark --server-id s-15ec9a85fcb44b90a | jq .User.SshPublicKeys[0]


# Transfer File
------------------------------------------
aws transfer start-file-transfer --connector-id s-15ec9a85fcb44b90a --send-file-paths "/transferprod-ucheonyekwuluje.com/home/uche1/file.txt" --remote-directory-path "/incoming"
















# Validate Template
# ---------------------
aws cloudformation validate-template --template-body file://cfn_s3bucket.yml

# Create Template
# ---------------------
aws cloudformation create-stack --stack-name s3ops-stack --capabilities CAPABILITY_NAMED_IAM --template-body file://cfn_s3bucket.yml

# Update Template
# ---------------------
aws cloudformation update-stack --stack-name s3ops-stack --capabilities CAPABILITY_NAMED_IAM --template-body file://cfn_s3bucket.yml

# Delete Cloudformation Stacks
# ------------------------------
aws cloudformation delete-stack --stack-name s3ops-stack







# Delete S3 Bucket Contents
-------------------------------
aws s3 ls
>>
2026-04-20 14:40:48 infracid-transfer-ip-allowlist
2026-04-12 13:38:08 infralabs-terraform-tfstate
2026-04-20 14:40:48 transferprod-ucheonyekwuluje.com


aws s3 rb s3://infracid-transfer-ip-allowlist/ --force
aws s3 rb s3://infralabs-terraform-tfstate/ --force

aws s3api list-object-versions --bucket infralabs-terraform-tfstate

S3_BUCKET="infracid-transfer-ip-allowlist"

# List all object versions
----------------------------------------
aws s3api list-object-versions \
  --bucket ${S3_BUCKET} \
  --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}'


# Delete all versions
----------------------------------------
aws s3api list-object-versions \
  --bucket ${S3_BUCKET} \
  --output json \
  --query 'Versions[].{Key:Key,VersionId:VersionId}' | \
  jq -c '.[]' | while read -r obj; do
    key=$(echo $obj | jq -r '.Key')
    version=$(echo $obj | jq -r '.VersionId')
    echo "Deleting $key version $version"
    aws s3api delete-object --bucket ${S3_BUCKET} --key "$key" --version-id "$version"
  done


# Delete all delete markers
----------------------------------------
aws s3api list-object-versions \
  --bucket ${S3_BUCKET} \
  --output json \
  --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' | \
  jq -c '.[]' | while read -r obj; do
    key=$(echo $obj | jq -r '.Key')
    version=$(echo $obj | jq -r '.VersionId')
    echo "Deleting marker $key version $version"
    aws s3api delete-object --bucket ${S3_BUCKET} --key "$key" --version-id "$version"
  done

# Delete Bucket
-----------------------------------------
aws s3 rb s3://${S3_BUCKET}/ --force












# Delete S3 Bucket Contents
-------------------------------
aws s3 rb s3://infracid-transfer-ip-allowlist/ --force

aws s3 rm s3://infracid-transfer-ip-allowlist/uche.txt
aws s3 ls s3://infracid-transfer-ip-allowlist/

aws s3 cp uche.txt s3://infracid-transfer-ip-allowlist/uche.txt
aws s3 cp s3://infracid-transfer-ip-allowlist/uche.txt .


./s3ops.py adduser-ip-addresses-s3 --username user1 --ip-cidr 172.18.5.40
./s3ops.py adduser-ip-addresses-s3 --username user1 --ip-cidr 11.10.10.3

./s3ops.py adduser-ip-addresses-s3 --username user2 --ip-cidr 24.38.90.90
./s3ops.py adduser-ip-addresses-s3 --username user2 --ip-cidr 192.168.1.4

./s3ops.py adduser-ip-addresses-s3 --username user3 --ip-cidr 64.68.145.55
./s3ops.py adduser-ip-addresses-s3 --username user3 --ip-cidr 70.87.87.96
>>
Add IP Address for user uche

# Remove IP Address from User File
-------------------------------
./s3ops.py removeuser-ip-addresses-s3 --username user2 --ip-cidr 10.0.0.3
>>
Remove IP Address 172.34.6.7

# List IP Addresses
-------------------------------
./s3ops.py list-ip-addresses
>>

./s3ops.py delete-ip-addresses
>>

# Update/Sync Security Group
------------------------------
./s3ops.py security-group-syncops



# Copy Addresses
--------------------------------------------------
aws s3 cp user1.txt s3://infracid-transfer-ip-allowlist/user1.txt
aws s3 cp user2.txt s3://infracid-transfer-ip-allowlist/user2.txt
aws s3 cp user3.txt s3://infracid-transfer-ip-allowlist/user3.txt


vim user1.txt
>>
172.18.5.40/32
11.10.10.3/32
192.168.1.4/32

vim user2.txt
>>
24.38.90.90/32
17.2.60.3/32
10.0.0.3/24

vim user3.txt
>>
19.68.10.40/32




aws ec2 describe-security-groups \
    --group-ids sg-0b0a902009441cefb




#  `add-ip-entry`
./trasnfer-ops.py adduser-ip-addresses-s3 --username user1 --ip-cidr 12.34.56.7


./s3ops.py adduser-ip-addresses-s3 --username uche --ip-cidr 168.4.6.7/23

cat uche.txt 
>>
10.0.0.3/24
168.4.6.7/23
172.34.6.7
192.168.1.4




































# List Managed Prefix List
----------------------------------------------
aws ec2 describe-managed-prefix-lists | jq
aws ec2 describe-managed-prefix-lists | jq .PrefixLists[].PrefixListName
aws ec2 describe-managed-prefix-lists --prefix-list-ids pl-077c0ce2e42800133
>>
{
    "PrefixLists": [
        {
            "PrefixListId": "pl-077c0ce2e42800133",
            "AddressFamily": "IPv4",
            "State": "create-complete",
            "PrefixListArn": "arn:aws:ec2:us-east-1:922271878465:prefix-list/pl-077c0ce2e42800133",
            "PrefixListName": "TransferPrefixList",
            "MaxEntries": 30,
            "Version": 1,
            "Tags": [],
            "OwnerId": "922271878465"
        }
    ]
}
>>



# Create the Managed Prefix List
----------------------------------------------
aws ec2 create-managed-prefix-list \
  --max-entries 30 \
  --address-family IPv4 \
  --prefix-list-name TransferPrefixList
>>
{
    "PrefixList": {
        "PrefixListId": "pl-077c0ce2e42800133",
        "AddressFamily": "IPv4",
        "State": "create-in-progress",
        "PrefixListArn": "arn:aws:ec2:us-east-1:922271878465:prefix-list/pl-077c0ce2e42800133",
        "PrefixListName": "TransferPrefixList",
        "MaxEntries": 30,
        "Version": 1,
        "Tags": [],
        "OwnerId": "922271878465"
    }
}



# Delete Managed Prefix List
---------------------------------------------
aws ec2 delete-managed-prefix-list --prefix-list-id pl-077c0ce2e42800133
>>
{
    "PrefixList": {
        "PrefixListId": "pl-077c0ce2e42800133",
        "AddressFamily": "IPv4",
        "State": "delete-in-progress",
        "PrefixListArn": "arn:aws:ec2:us-east-1:922271878465:prefix-list/pl-071edcb6531e891bd",
        "PrefixListName": "TransferPrefixList",
        "MaxEntries": 1000,
        "Version": 4,
        "OwnerId": "922271878465"
    }
}



# Add Multiple IP Addresses (CIDR blocks)
--------------------------------------------
aws ec2 modify-managed-prefix-list \
  --prefix-list-id pl-077c0ce2e42800133 \
  --current-version 1 \
  --add-entries \
    Cidr=192.168.1.0/24,Description="Office Network" \
    Cidr=10.0.0.0/16,Description="VPC Network" \
    Cidr=203.0.113.5/32,Description="Single IP"
>>
{
    "PrefixList": {
        "PrefixListId": "pl-077c0ce2e42800133",
        "AddressFamily": "IPv4",
        "State": "modify-in-progress",
        "PrefixListArn": "arn:aws:ec2:us-east-1:922271878465:prefix-list/pl-071edcb6531e891bd",
        "PrefixListName": "UchePrefixList",
        "MaxEntries": 1000,
        "Version": 1,
        "OwnerId": "922271878465"
    }
}


aws ec2 modify-managed-prefix-list \
  --prefix-list-id pl-077c0ce2e42800133 \
  --current-version 2 \
  --add-entries \
    Cidr=24.183.176.100/32,Description="Home Lab Instance"
>>
{
    "PrefixList": {
        "PrefixListId": "pl-077c0ce2e42800133",
        "AddressFamily": "IPv4",
        "State": "modify-in-progress",
        "PrefixListArn": "arn:aws:ec2:us-east-1:922271878465:prefix-list/pl-071edcb6531e891bd",
        "PrefixListName": "UchePrefixList",
        "MaxEntries": 1000,
        "Version": 2,
        "OwnerId": "922271878465"
    }
}

# Remove All Entries
----------------------------------------------
# Set your Prefix List ID
PL_ID="pl-077c0ce2e42800133"

# Get current version
VERSION=$(aws ec2 describe-managed-prefix-lists --prefix-list-ids $PL_ID --query 'PrefixLists[0].Version' --output text)

# Get all CIDRs and format them for the CLI
CIDRS=$(aws ec2 get-managed-prefix-list-entries --prefix-list-id $PL_ID --query 'Entries[].Cidr' --output text)
REMOVE_ARGS=$(echo $CIDRS | sed 's/\([^ ]*\)/Cidr=\1/g')

# Execute the removal
aws ec2 modify-managed-prefix-list --prefix-list-id $PL_ID --current-version $VERSION --remove-entries $REMOVE_ARGS

