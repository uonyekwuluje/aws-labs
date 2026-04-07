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

