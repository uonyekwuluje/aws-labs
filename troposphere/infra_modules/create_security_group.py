from troposphere import ec2, Template, Ref, Tags, GetAtt, Output, Export, Sub, ImportValue, Base64, Join
import boto3
from botocore.exceptions import ClientError
from infra_modules import return_vpc_component_ids

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
def create_update_security_group_template(vpc_name, stack_name):
    required_status = "CREATE_COMPLETE"
    if stack_exists(stack_name, required_status):
        print(f"{stack_name} Exists. Updating Now")
        generate_sg_cfn_template(vpc_name, stack_name, stack_action="update")
    else:
        print(f"{stack_name} Does Not Exist. Creating Now")
        generate_sg_cfn_template(vpc_name, stack_name, stack_action="create")



# Create Security Groups
def generate_sg_cfn_template(vpc_name, stack_name, stack_action):
    try:
        print("Creating Security Groups")

        # Create Bastion Security Group (AWS::EC2::SecurityGroup)
        bastion_sg_cfn = ec2.SecurityGroup('BastionSecurityGroup')
        bastion_sg_cfn.GroupDescription = "Bastion Security Group"
        bastion_sg_cfn.VpcId = return_vpc_component_ids.get_vpc_id(vpc_name)
        bastion_sg_cfn.Tags = Tags(Name=f"{vpc_name}-bastion-sg", sg_type="bastion")

        # Create Bastion Security Group Ingress (AWS::EC2::SecurityGroupIngress)
        bastion_sg_ingress_cfn = ec2.SecurityGroupIngress('BastionSecurityGroupIngress',
              Description="Bastion SG Ingress", IpProtocol="tcp", FromPort=22, 
              ToPort=22,CidrIp="0.0.0.0/0", GroupId=Ref(bastion_sg_cfn)
        )
    
        # Create MongoDB Security Group (AWS::EC2::SecurityGroup)
        mongodb_sg_cfn = ec2.SecurityGroup('MongoDBSecurityGroup')
        mongodb_sg_cfn.GroupDescription = "MongoDB Security Group"
        mongodb_sg_cfn.VpcId = return_vpc_component_ids.get_vpc_id(vpc_name)
        mongodb_sg_cfn.Tags = Tags(Name=f"{vpc_name}-mongodb-sg", sg_type="mongodb")

        # Create MongoDB Security Group Ingress (AWS::EC2::SecurityGroupIngress)
        mongodb_bastion_sg_ingress_cfn = ec2.SecurityGroupIngress('MongoDBBastionSecurityGroupIngress',
            Description="Mongodb Bastion SG Ingress", IpProtocol="tcp", FromPort=22, 
            ToPort=22,CidrIp="0.0.0.0/0", GroupId=Ref(mongodb_sg_cfn)
        )
 
        mongodb_sg_ingress_cfn = ec2.SecurityGroupIngress('MongoSecurityGroupIngress',
            Description="Mongodb SG Ingress", IpProtocol="tcp", FromPort=27016,
            ToPort=27020,CidrIp="0.0.0.0/0", GroupId=Ref(mongodb_sg_cfn)
        )


        # Create Kubernetes Security Group (AWS::EC2::SecurityGroup)
        kubernetes_sg_cfn = ec2.SecurityGroup('KubernetesDBSecurityGroup')
        kubernetes_sg_cfn.GroupDescription = "Kubernetes Security Group"
        kubernetes_sg_cfn.VpcId = return_vpc_component_ids.get_vpc_id(vpc_name)
        kubernetes_sg_cfn.Tags = Tags(Name=f"{vpc_name}-kubernetes-sg",
                                      sg_type="kubernetes")

        # Create Kubernetes Security Group Ingress (AWS::EC2::SecurityGroupIngress)
        kubernetes_bastion_sg_ingress_cfn = ec2.SecurityGroupIngress('KubernetesBastionSecurityGroupIngress',
            Description="Kubernetes Bastion SG Ingress", IpProtocol="tcp", FromPort=22, 
            ToPort=22,CidrIp="0.0.0.0/0", GroupId=Ref(kubernetes_sg_cfn)
        )

        kubernetes_node_port_sg_ingress_cfn = ec2.SecurityGroupIngress('KubernetesNodePortSecurityGroupIngress',
            Description="Kubernetes Node Port SG Ingress", IpProtocol="tcp", FromPort=30000,
            ToPort=32767,CidrIp="0.0.0.0/0", GroupId=Ref(kubernetes_sg_cfn)
        )

        kubernetes_api_server_sg_ingress_cfn =  ec2.SecurityGroupIngress('KubernetesApiServerSecurityGroupIngress',
            Description="Kubernetes API Server SG Ingress", IpProtocol="tcp", FromPort=6443,
            ToPort=6443,CidrIp="0.0.0.0/0", GroupId=Ref(kubernetes_sg_cfn)
        )

        kubernetes_etcd_server_sg_ingress_cfn =  ec2.SecurityGroupIngress('KubernetesEtcdServerSecurityGroupIngress',
            Description="Kubernetes ETCD Server API SG Ingress", IpProtocol="tcp", FromPort=2379,
            ToPort=2382,CidrIp="0.0.0.0/0", GroupId=Ref(kubernetes_sg_cfn)
        )

        kubernetes_kubelet_api_sg_ingress_cfn =  ec2.SecurityGroupIngress('KubernetesKubeletApiSecurityGroupIngress',
            Description="Kubernetes Kubelet API SG Ingress", IpProtocol="tcp", FromPort=10250,
            ToPort=10260,CidrIp="0.0.0.0/0", GroupId=Ref(kubernetes_sg_cfn)
        )

        kubernetes_http_sg_ingress_cfn =  ec2.SecurityGroupIngress('KubernetesHttpServerSecurityGroupIngress',
            Description="Kubernetes HTTP SG Ingress", IpProtocol="tcp", FromPort=80,
            ToPort=80,CidrIp="0.0.0.0/0", GroupId=Ref(kubernetes_sg_cfn)
        )

        kubernetes_https_sg_ingress_cfn =  ec2.SecurityGroupIngress('KubernetesHttpsServerSecurityGroupIngress',
            Description="Kubernetes HTTPS SG Ingress", IpProtocol="tcp", FromPort=443,
            ToPort=443,CidrIp="0.0.0.0/0", GroupId=Ref(kubernetes_sg_cfn)
        )

        kubernetes_rancher_api_sg_ingress_cfn =  ec2.SecurityGroupIngress('KubernetesRancherApiSecurityGroupIngress',
            Description="Kubernetes Rancher API SG Ingress", IpProtocol="tcp", FromPort=9345,
            ToPort=9345,CidrIp="0.0.0.0/0", GroupId=Ref(kubernetes_sg_cfn)
        )

        kubernetes_rancher_udp_sg_ingress_cfn =  ec2.SecurityGroupIngress('KubernetesRancherUdpSecurityGroupIngress',
            Description="Kubernetes Rancher UDP SG Ingress", IpProtocol="tcp", FromPort=8472,
            ToPort=8472,CidrIp="0.0.0.0/0", GroupId=Ref(kubernetes_sg_cfn)
        )


        # Output Security Groups
        output_bastion_sg_id = Output('outputBastionSG', Value=Ref(bastion_sg_cfn), Export=Export('Infrastructure-BastionSg'))
        output_mongodb_sg_id = Output('outputMongodbSG', Value=Ref(mongodb_sg_cfn), Export=Export('Infrastructure-MongodbSg'))
        output_kubernetes_sg_id = Output('outputKubernetes', Value=Ref(kubernetes_sg_cfn), Export=Export('Infrastructure-KubernetesSg'))

        # ================================== #
        # Add objects to template            #
        # ================================== # 
        t.add_resource(bastion_sg_cfn)
        t.add_resource(bastion_sg_ingress_cfn)
        t.add_resource(mongodb_sg_cfn)
        t.add_resource(mongodb_bastion_sg_ingress_cfn)
        t.add_resource(mongodb_sg_ingress_cfn)
        t.add_resource(kubernetes_sg_cfn)
        t.add_resource(kubernetes_bastion_sg_ingress_cfn)
        t.add_resource(kubernetes_node_port_sg_ingress_cfn)
        t.add_resource(kubernetes_api_server_sg_ingress_cfn)
        t.add_resource(kubernetes_etcd_server_sg_ingress_cfn)
        t.add_resource(kubernetes_kubelet_api_sg_ingress_cfn)
        t.add_resource(kubernetes_http_sg_ingress_cfn)
        t.add_resource(kubernetes_https_sg_ingress_cfn)
        t.add_resource(kubernetes_rancher_api_sg_ingress_cfn)
        t.add_resource(kubernetes_rancher_udp_sg_ingress_cfn)
        t.add_output(output_bastion_sg_id)
        t.add_output(output_mongodb_sg_id)
        t.add_output(output_kubernetes_sg_id)
 
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
