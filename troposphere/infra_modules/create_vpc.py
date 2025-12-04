from enum import Enum
from troposphere import Template, Ref, Tags, GetAtt, Output, Export, Sub, Select, Split, Join
from troposphere import ec2, route53

import boto3
import json
from botocore.exceptions import ClientError
import os

# Create a new AWS cloudFormation template
t = Template()

cfn_template = boto3.client('cloudformation')


# Check Stack Status
def stack_exists(stack_name, required_status):
    try:
        response = cfn_template.describe_stacks(
            StackName=stack_name
        )
    except ClientError:
        return False
    return response['Stacks'][0]['StackStatus'] == required_status


# Create or update stack
def create_update_cfn_template(vpc_name, region, hostedzone_name, stack_name, octet_address):
    required_status = "CREATE_COMPLETE"

    if stack_exists(stack_name, required_status):
        print(f"{stack_name} Exists. Updating Now")
        generate_cfn_template(vpc_name, region, hostedzone_name, stack_name, octet_address, stack_action="update")
    else:
        print(f"{stack_name} Does Not Exist. Creating Now")
        generate_cfn_template(vpc_name, region, hostedzone_name, stack_name, octet_address, stack_action="create")




def subnet_creation_association(
    tp,
    vpc_id,
    environment,
    subnet_configs,
    route_table_id
):
    subnets = {}
    associations = {}

    for cfg in subnet_configs:
        name = cfg["name"]

        subnet = tp.add_resource(
            ec2.Subnet(
                name,
                VpcId = vpc_id,
                CidrBlock = cfg["cidr"],
                AvailabilityZone = cfg.get("az"),
                MapPublicIpOnLaunch = cfg["is_public_ip"],
                Tags = [
                    {"Key": "Name", "Value": f"{environment}-{name}"},
                    {"Key": "subnet_type", "Value": cfg["subnet_type"]}
                ]    
            )
        )

        subnets[name] = subnet

        assoc = tp.add_resource(
           ec2.SubnetRouteTableAssociation(
               cfg["route_table"],
               SubnetId = Ref(subnet),
               RouteTableId = route_table_id
           )      
        )        

        associations[name] = assoc




# Generate stack and perform action
def generate_cfn_template(vpc_name, region, hostedzone_name, stack_name, octet_address, stack_action):
    try:
        # Get Basic IDs
        ref_stack_id = Ref("AWS::StackId")
        ref_region = Ref("AWS::Region")
        ref_stack_name = Ref("AWS::StackName")

        # =========================================== #
        # Create VPC, InternetGateway and Attachment  #
        # =========================================== #
        # Create a VPC (AWS::EC2::VPC)
        vpc_cfn = ec2.VPC('VPC')
        vpc_cfn.CidrBlock = f"{octet_address}.0.0/16"
        vpc_cfn.EnableDnsSupport = True
        vpc_cfn.EnableDnsHostnames = True
        vpc_cfn.Tags = Tags({"Name": vpc_name})
        t.add_resource(vpc_cfn)

        # Create the InternetGateway (AWS::EC2::InternetGateway)
        vpc_igw_cfn = ec2.InternetGateway('InternetGateway')
        vpc_igw_cfn.Tags = Tags({"Name": f"{vpc_name}-InternetGateway"})
        t.add_resource(vpc_igw_cfn)

        # Create the VPCGatewayAttachment (AWS::EC2::VPCGatewayAttachment)
        vpc_gtwattachement_cfn = ec2.VPCGatewayAttachment('VPCGatewayAttachment')
        vpc_gtwattachement_cfn.DependsOn = [vpc_cfn.title, vpc_igw_cfn.title]
        vpc_gtwattachement_cfn.VpcId = Ref(vpc_cfn)
        vpc_gtwattachement_cfn.InternetGatewayId= Ref(vpc_igw_cfn)
        t.add_resource(vpc_gtwattachement_cfn)



        # ====================================================== #
        # Create Public Subnets .{1-10}.0/24                     #
        # ====================================================== #
        # Create Public Routetable (AWS::EC2::RouteTable)
        vpc_public_routetable_cfn = ec2.RouteTable('PublicRouteTable')
        vpc_public_routetable_cfn.VpcId = Ref(vpc_cfn)
        vpc_public_routetable_cfn.Tags = Tags({"Name": f"{vpc_name}-PublicRouteTable"})
        t.add_resource(vpc_public_routetable_cfn)

        # Create Public Route (AWS::EC2::Route)
        vpc_public_route_cfn = ec2.Route('PublicInternetTrafficRoute')
        vpc_public_route_cfn.DependsOn = "VPCGatewayAttachment"
        vpc_public_route_cfn.RouteTableId = Ref(vpc_public_routetable_cfn)
        vpc_public_route_cfn.DestinationCidrBlock = "0.0.0.0/0"
        vpc_public_route_cfn.GatewayId = Ref(vpc_igw_cfn)
        t.add_resource(vpc_public_route_cfn)

        # Public Subnet Maps
        public_subnet_configs = [
            {"name": "PublicWebSubnet1a", "cidr": f"{octet_address}.1.0/24", "az": "us-east-1a", "subnet_type": "public_web", 
             "route_table": "PublicRouteTableAssociationWeb1a", "is_public_ip": "True"},
            {"name": "PublicSvcSubnet1b", "cidr": f"{octet_address}.2.0/24", "az": "us-east-1b", "subnet_type": "public_svc", 
             "route_table": "PublicRouteTableAssociationSvc1b", "is_public_ip": "True"}
        ]

        subnet_creation_association(
            t,
            vpc_id = Ref(vpc_cfn),
            environment = vpc_name,
            subnet_configs = public_subnet_configs,
            route_table_id = Ref(vpc_public_routetable_cfn),
        )




        # ======================================== #
        # Create Public Subnet for EIP             #
        # ======================================== #
        # Create Public Subnet (AWS::EC2::Subnet) PublicEIPSubnet1b
        vpc_pubeip_subnet_cfn = ec2.Subnet('PublicEIPSubnet1b')
        vpc_pubeip_subnet_cfn.DependsOn = "VPC"
        vpc_pubeip_subnet_cfn.VpcId = Ref(vpc_cfn)
        vpc_pubeip_subnet_cfn.AvailabilityZone = "us-east-1b"
        vpc_pubeip_subnet_cfn.MapPublicIpOnLaunch = True
        vpc_pubeip_subnet_cfn.CidrBlock = f"{octet_address}.30.0/24"
        vpc_pubeip_subnet_cfn.Tags = Tags({"Name": f"{vpc_name}-PublicEIPSubnet1c", "subnet_type": "public_eip"})
        t.add_resource(vpc_pubeip_subnet_cfn)

        # Create Public Subnet One RouteTable Association (AWS::EC2::SubnetRouteTableAssociation)
        vpc_pubeip_subnet_routetable_association_cfn = ec2.SubnetRouteTableAssociation('PublicSubnetEIPRouteTableAssociation')
        vpc_pubeip_subnet_routetable_association_cfn.RouteTableId = Ref(vpc_public_routetable_cfn)
        vpc_pubeip_subnet_routetable_association_cfn.SubnetId = Ref(vpc_pubeip_subnet_cfn)
        t.add_resource(vpc_pubeip_subnet_routetable_association_cfn)





        # ==================================================== #
        # Create Private Subnets .{11-20}.0/24                 #
        # ==================================================== #
        # Create EIP for NatGateway (AWS::EC2::EIP)
        vpc_eip_natgateway_cfn = ec2.EIP('EIPforNatGateway')
        vpc_eip_natgateway_cfn.DependsOn = "VPCGatewayAttachment" 
        vpc_eip_natgateway_cfn.Domain = "vpc"
        vpc_eip_natgateway_cfn.Tags = Tags(Name=f"{vpc_name}-EIPNatGateway")
        t.add_resource(vpc_eip_natgateway_cfn)

        # Create Nat Gateway (AWS::EC2::NatGateway)
        vpc_natgateway_cfn = ec2.NatGateway('NatGateway')
        vpc_natgateway_cfn.AllocationId = GetAtt(vpc_eip_natgateway_cfn, 'AllocationId')
        vpc_natgateway_cfn.SubnetId = Ref(vpc_pubeip_subnet_cfn)
        vpc_natgateway_cfn.Tags = Tags(Name=f"{vpc_name}-NatGateway")
        t.add_resource(vpc_natgateway_cfn)

        # Create Private Routetable (AWS::EC2::RouteTable)
        vpc_private_routetable_cfn = ec2.RouteTable('PrivateRouteTable')
        vpc_private_routetable_cfn.VpcId = Ref(vpc_cfn)
        vpc_private_routetable_cfn.Tags = Tags(Name=f"{vpc_name}-privateroutetable")
        t.add_resource(vpc_private_routetable_cfn) 

        # Create Private Route (AWS::EC2::Route)
        vpc_private_route_cfn = ec2.Route('PrivateRoute')
        vpc_private_route_cfn.DependsOn = "VPCGatewayAttachment"
        vpc_private_route_cfn.RouteTableId = Ref(vpc_private_routetable_cfn)
        vpc_private_route_cfn.DestinationCidrBlock = "0.0.0.0/0"
        vpc_private_route_cfn.NatGatewayId = Ref(vpc_natgateway_cfn)
        t.add_resource(vpc_private_route_cfn)

        # Private Subnet Maps
        private_subnet_configs = [
            {"name": "PrivateDbSubnet1a", "cidr": f"{octet_address}.11.0/24", "az": "us-east-1a", "subnet_type": "private_db",
             "route_table": "PrivateRouteTableAssociationDb1a", "is_public_ip": "False"},
            {"name": "PrivateSvcSubnet1b", "cidr": f"{octet_address}.12.0/24", "az": "us-east-1b", "subnet_type": "private_svc",
             "route_table": "PrivateRouteTableAssociationSvc1b", "is_public_ip": "False"}
        ]

        subnet_creation_association(
            t,
            vpc_id = Ref(vpc_cfn),
            environment = vpc_name,
            subnet_configs = private_subnet_configs,
            route_table_id = Ref(vpc_private_routetable_cfn),
        )

        # ========================================== #
        # Create Private HostedZone                  #
        # ========================================== #
        # Create Private Hosted Zone (AWS::Route53::HostedZone)
        vpc_private_hostedzone_cfn = route53.HostedZone('PrivateHostedZone')
        vpc_private_hostedzone_cfn.Name = hostedzone_name
        vpc_private_hostedzone_cfn.HostedZoneConfig = route53.HostedZoneConfiguration(
                Comment=f"Private Hosted Zone for [{hostedzone_name}]")
        vpc_private_hostedzone_cfn.HostedZoneTags = Tags(Name=f"{hostedzone_name}")
        vpc_private_hostedzone_cfn.VPCs = [route53.HostedZoneVPCs(VPCId=Ref(vpc_cfn), VPCRegion=Ref("AWS::Region"))]
        t.add_resource(vpc_private_hostedzone_cfn)



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
