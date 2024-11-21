#!/usr/bin/env python3
import boto3
from troposphere import ec2, Tags, ImportValue, Template, Ref

client = boto3.client('ec2', region_name='us-east-1')
cfn_template = boto3.client('cloudformation', region_name='us-east-1')

EC2_KEYPAIR = "infracidlabs-key"
EC2_INSTANCE_TYPE = "t2.small"
UBUNTU_AMI_ID = "ami-0866a3c8686eaeeba"

# Create object that will generate our template
t = Template()

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
       print('No vpcs found')


def get_subnet_id(vpc_name, subnet_name):
    """ Get Subnet ID """
    subnet_name = f"{vpc_name}-{subnet_name}"
    response = client.describe_subnets(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    subnet_name,
                ]
            }
        ]
    )
    resp_val = response['Subnets'][0]['SubnetId']
    if resp_val:
       return resp_val 
    else:
       print('Subnet Not Found')


def get_security_group_id(security_group_name):
    """ Get Security Group ID """
    response = client.describe_security_groups(
        Filters=[
          { 
            'Name': 'tag:Name', 'Values': [security_group_name] 
          }
        ]
    )
    resp_sg_val = response['SecurityGroups'][0]['GroupId']
    if resp_sg_val:
       return resp_sg_val
    else:
       print('Security Group Not Found')







if __name__ == '__main__':
    public_nodes = 2
    private_nodes = 3
    vpc_name = "dev"
    public_subnet_name = "PublicSubnet1"
    private_subnet_name = "PrivateSubnet1"
    security_group_name = "base-sg"
    vpc_id = get_vpc_id(vpc_name)
    public_subnet_id = get_subnet_id(vpc_name, public_subnet_name)
    private_subnet_id = get_subnet_id(vpc_name, private_subnet_name)
    security_group_id = get_security_group_id(security_group_name) 
    print(f"VPC ID => {vpc_id}")
    print(f"Public Subnet ID => {public_subnet_id}")
    print(f"Private Subnet ID => {private_subnet_id}")
    print(f"Security Group ID => {security_group_id}")

    for i in range(public_nodes):
        instance = ec2.Instance(
            "pubsvr0{}".format(str(i)),
            ImageId=UBUNTU_AMI_ID,
            #UserData=Base64(Join("", userData)),
            InstanceType=EC2_INSTANCE_TYPE,
            KeyName=EC2_KEYPAIR,
            SecurityGroupIds=[security_group_id],
            SubnetId=public_subnet_id,
            Tags=Tags(
              Name=f"pub-svr0{i}",
              Environment=vpc_name,
            ),
        )
        t.add_resource(instance)

    for i in range(private_nodes):
        instance = ec2.Instance(
            "privsvr0{}".format(str(i)),
            ImageId=UBUNTU_AMI_ID,
            #UserData=Base64(Join("", userData)),
            InstanceType=EC2_INSTANCE_TYPE,
            KeyName=EC2_KEYPAIR,
            SecurityGroupIds=[security_group_id],
            SubnetId=private_subnet_id,
            Tags=Tags(
              Name=f"priv-svr0{i}",
              Environment=vpc_name,
            ),
        )
        t.add_resource(instance)


    print(t.to_yaml())

    stack_name = "dev-ec2-stack"
    cfn_template.create_stack(
        StackName=stack_name,
        TemplateBody=t.to_yaml()
    )
    waiter = cfn_template.get_waiter("stack_create_complete")
    waiter.wait(
        StackName=stack_name
    )
