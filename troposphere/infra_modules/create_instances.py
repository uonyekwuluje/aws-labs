#!/usr/bin/env python3
import boto3
from troposphere import ec2, Tags, ImportValue, Template, Ref, Base64, Join, route53, GetAtt, Output, Export, Sub
import troposphere.ec2 as ec2

from troposphere.route53 import RecordSetType
from infra_modules import return_vpc_component_ids


client = boto3.client('ec2', region_name='us-east-1')
cfn_template = boto3.client('cloudformation', region_name='us-east-1')

EC2_KEYPAIR = "infracidlabs-key"

# Create object that will generate our template
t = Template()

# Create or update ec2 instance stack
def create_update_instance_template(vpc_name, stack_name, hostedzone_name, aws_build_region, ec2_instance_db):
    required_status = "CREATE_COMPLETE"
    if return_vpc_component_ids.stack_exists(stack_name, required_status):
        print(f"{stack_name} Exists. Updating Now")
        generate_instance_cfn_template(vpc_name, stack_name, hostedzone_name,
                                       aws_build_region, ec2_instance_db, stack_action="update")
    else:
        print(f"{stack_name} Does Not Exist. Creating Now")
        generate_instance_cfn_template(vpc_name, stack_name, hostedzone_name, aws_build_region,
                                       ec2_instance_db, stack_action="create")



# Generate EC2 Template and create stack
def generate_instance_cfn_template(vpc_name, stack_name, hostedzone_name, vpc_region,
                                   ec2_instance_db, stack_action):
    try:
        #security_group_id = return_vpc_component_ids.get_security_group_id(f"{vpc_name}", "bastion-sg")
        security_group_id = return_vpc_component_ids.get_security_group_id(f"{vpc_name}", "kubernetes-sg")
        route53_zone_id = return_vpc_component_ids.get_hosted_zone_id(f"{vpc_name}", f"{hostedzone_name}", f"{vpc_region}")
        for instance in ec2_instance_db:
            print(f"VPC Name => {vpc_name}")
            print(f"VPC ID   => {return_vpc_component_ids.get_vpc_id(vpc_name)}")
            print(f"Instance Name => {instance[0]}")
            print(f"Instance FQDN => {instance[0]}.{vpc_name}.{hostedzone_name}")
            print(f"Instance Type => {instance[1]}")
            print(f"Subnet ID     => {return_vpc_component_ids.get_subnet_id(vpc_name, instance[2])}")
            print(f"Instance Keypair => {EC2_KEYPAIR}")
            print(f"AMI Instance ID => {instance[3]}")
            print(f"Instance Storage => {instance[4]}")
            print(f"Instance Security Group => {security_group_id}")
            print(f"Private Hosted Zone ID  => {route53_zone_id}")
            print("\n")

            block_device = ec2.BlockDeviceMapping(
                DeviceName="/dev/xvda",  
                Ebs=ec2.EBSBlockDevice(
                    VolumeSize=int(f"{instance[4]}"),      
                    VolumeType="gp3",    
                    DeleteOnTermination=True
                )
            )

            serverName = f"{instance[0]}"
            instance = ec2.Instance(
                serverName,
                ImageId=f"{instance[3]}",
                UserData=Base64(Join('', [
                  "#!/bin/bash\n"
                  "sudo hostnamectl set-hostname ",serverName,"\n"
                ])),
                InstanceType=f"{instance[1]}",
                KeyName=f"{EC2_KEYPAIR}",
                SecurityGroupIds=[security_group_id],
                SubnetId=f"{return_vpc_component_ids.get_subnet_id(vpc_name, instance[2])}",
                BlockDeviceMappings=[block_device],
                Tags=Tags(
                  Name=serverName,
                  Environment=vpc_name,
                ),
            )
            t.add_resource(instance)

            # Set Private DNS 
            instance_record = RecordSetType(
               f"{serverName}PrivateDNSRecord",
               HostedZoneName=Join("", [vpc_name,".", hostedzone_name, "."]),
               Comment=f"DNS name for {serverName}.",
               Name=Join(
                    "", [serverName, ".", vpc_name, ".", hostedzone_name, "."]
               ),
               Type="A",
               TTL="900",
               ResourceRecords=[GetAtt(serverName, "PrivateIp")],
            ) 
            t.add_resource(instance_record)


        # Print Cloudformation Template
        print(t.to_yaml())

        if stack_action == "create":
            print(f"Creating {stack_name} stack")
            cfn_template.create_stack(
                StackName=stack_name,
                TemplateBody=t.to_yaml()
            )
            waiter = cfn_template.get_waiter("stack_create_complete")
            waiter.wait(
                StackName=stack_name
            )
            print(f"{stack_name} stack creation complete")
        elif stack_action == "update":
            print(f"Updating {stack_name} stack")
            cfn_template.update_stack(
                StackName=stack_name,
                TemplateBody=t.to_yaml()
            )
            waiter = cfn_template.get_waiter("stack_update_complete")
            waiter.wait(
                StackName=stack_name
            )
            print(f"{stack_name} stack update complete")
    except Exception as e:
        print(f"An error occurred: {e}")
