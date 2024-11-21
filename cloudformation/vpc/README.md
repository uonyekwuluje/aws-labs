# Cloudformation create VPC
Cloudformation template to create a VPC stack

## Create/Manage VPC Stack
```
# Validate VPC Template
# ---------------------
aws cloudformation validate-template --template-body file://vpc.yaml

# Create Template
# ---------------------
aws cloudformation create-stack --stack-name dev-vpc-stack --template-body file://vpc.yaml

# Update Template
# ---------------------
aws cloudformation update-stack --stack-name dev-vpc-stack --template-body file://vpc.yaml}

# List Stack Outputs
# ------------------------------
aws cloudformation describe-stacks --stack-name dev-vpc-stack
aws cloudformation describe-stacks --stack-name dev-vpc-stack | jq .Stacks[].Outputs

# Delete Cloudformation Stacks
# ------------------------------
aws cloudformation delete-stack --stack-name dev-vpc-stack
```

