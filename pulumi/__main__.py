import pulumi
import pulumi_aws as aws


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

config = pulumi.Config()

aws_region = config.get("aws:region") or "us-east-1"

# AMI for Amazon Linux 2023
ami_id = config.get("ami_id") or "ami-0b6d9d3d33ba97d99"

# Use an existing EC2 key pair.
key_name: str = "infracidlabs-key"


# ---------------------------------------------------------
# Availability Zones
# ---------------------------------------------------------

azs = aws.get_availability_zones(
    state="available"
)

az1 = azs.names[0]
az2 = azs.names[1]


# ---------------------------------------------------------
# VPC
# ---------------------------------------------------------

vpc = aws.ec2.Vpc(
    "main-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,

    tags={
        "Name": "pulumi-vpc",
    },
)


# ---------------------------------------------------------
# Internet Gateway
# ---------------------------------------------------------

internet_gateway = aws.ec2.InternetGateway(
    "internet-gateway",

    vpc_id=vpc.id,

    tags={
        "Name": "pulumi-igw",
    },
)


# ---------------------------------------------------------
# Public Subnets
# ---------------------------------------------------------

public_subnet_1 = aws.ec2.Subnet(
    "public-subnet-1",

    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone=az1,

    # Instances launched here receive public IPv4 addresses
    # by default.
    map_public_ip_on_launch=True,

    tags={
        "Name": "public-subnet-1",
        "Tier": "public",
    },
)


public_subnet_2 = aws.ec2.Subnet(
    "public-subnet-2",

    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone=az2,

    map_public_ip_on_launch=True,

    tags={
        "Name": "public-subnet-2",
        "Tier": "public",
    },
)


# ---------------------------------------------------------
# Private Subnets
# ---------------------------------------------------------

private_subnet_1 = aws.ec2.Subnet(
    "private-subnet-1",

    vpc_id=vpc.id,
    cidr_block="10.0.11.0/24",
    availability_zone=az1,

    map_public_ip_on_launch=False,

    tags={
        "Name": "private-subnet-1",
        "Tier": "private",
    },
)


private_subnet_2 = aws.ec2.Subnet(
    "private-subnet-2",

    vpc_id=vpc.id,
    cidr_block="10.0.12.0/24",
    availability_zone=az2,

    map_public_ip_on_launch=False,

    tags={
        "Name": "private-subnet-2",
        "Tier": "private",
    },
)


# ---------------------------------------------------------
# Public Route Table
# ---------------------------------------------------------

public_route_table = aws.ec2.RouteTable(
    "public-route-table",

    vpc_id=vpc.id,

    tags={
        "Name": "public-route-table",
    },
)


# Route public traffic through Internet Gateway
public_route = aws.ec2.Route(
    "public-internet-route",

    route_table_id=public_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=internet_gateway.id,
)


# Associate public subnets with public route table
aws.ec2.RouteTableAssociation(
    "public-subnet-1-association",

    subnet_id=public_subnet_1.id,
    route_table_id=public_route_table.id,
)


aws.ec2.RouteTableAssociation(
    "public-subnet-2-association",

    subnet_id=public_subnet_2.id,
    route_table_id=public_route_table.id,
)


# ---------------------------------------------------------
# Elastic IP for NAT Gateway
# ---------------------------------------------------------

nat_eip = aws.ec2.Eip(
    "nat-eip",

    domain="vpc",

    tags={
        "Name": "pulumi-nat-eip",
    },
)


# ---------------------------------------------------------
# NAT Gateway
# ---------------------------------------------------------

# NAT Gateway is placed in the public subnet.
nat_gateway = aws.ec2.NatGateway(
    "nat-gateway",

    allocation_id=nat_eip.id,
    subnet_id=public_subnet_1.id,

    tags={
        "Name": "pulumi-nat-gateway",
    },

    opts=pulumi.ResourceOptions(
        depends_on=[internet_gateway]
    ),
)


# ---------------------------------------------------------
# Private Route Table
# ---------------------------------------------------------

private_route_table = aws.ec2.RouteTable(
    "private-route-table",

    vpc_id=vpc.id,

    tags={
        "Name": "private-route-table",
    },
)


# Private subnet outbound internet traffic goes
# through the NAT Gateway.
private_route = aws.ec2.Route(
    "private-nat-route",

    route_table_id=private_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    nat_gateway_id=nat_gateway.id,
)


# Associate private subnets with private route table
aws.ec2.RouteTableAssociation(
    "private-subnet-1-association",

    subnet_id=private_subnet_1.id,
    route_table_id=private_route_table.id,
)


aws.ec2.RouteTableAssociation(
    "private-subnet-2-association",

    subnet_id=private_subnet_2.id,
    route_table_id=private_route_table.id,
)


# ---------------------------------------------------------
# Security Group - Public Instance
# ---------------------------------------------------------

public_sg = aws.ec2.SecurityGroup(
    "public-instance-sg",

    name="public-instance-sg",
    description="Security group for public EC2 instance",
    vpc_id=vpc.id,

    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],
            description="SSH",
        ),
    ],

    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound traffic",
        ),
    ],

    tags={
        "Name": "public-instance-sg",
    },
)


# ---------------------------------------------------------
# Security Group - Private Instance
# ---------------------------------------------------------

private_sg = aws.ec2.SecurityGroup(
    "private-instance-sg",

    name="private-instance-sg",
    description="Security group for private EC2 instance",
    vpc_id=vpc.id,

    # SSH is allowed only from the public instance's
    # security group.
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            security_groups=[public_sg.id],
            description="SSH from public instance",
        ),
    ],

    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound traffic",
        ),
    ],

    tags={
        "Name": "private-instance-sg",
    },
)


# ---------------------------------------------------------
# Public EC2 Instance
# ---------------------------------------------------------

public_instance = aws.ec2.Instance(
    "public-instance",

    ami=ami_id,
    instance_type="t3.micro",

    subnet_id=public_subnet_1.id,

    vpc_security_group_ids=[
        public_sg.id,
    ],

    key_name=key_name,

    associate_public_ip_address=True,

    tags={
        "Name": "public-instance",
    },
)


# ---------------------------------------------------------
# Private EC2 Instance
# ---------------------------------------------------------

private_instance = aws.ec2.Instance(
    "private-instance",

    ami=ami_id,
    instance_type="t3.micro",

    subnet_id=private_subnet_1.id,

    vpc_security_group_ids=[
        private_sg.id,
    ],

    key_name=key_name,

    # Explicitly prevent a public IP.
    associate_public_ip_address=False,

    tags={
        "Name": "private-instance",
    },
)


# ---------------------------------------------------------
# Outputs
# ---------------------------------------------------------

pulumi.export("vpc_id", vpc.id)

pulumi.export(
    "availability_zones",
    pulumi.Output.all(az1, az2),
)

pulumi.export(
    "public_subnet_ids",
    [public_subnet_1.id, public_subnet_2.id],
)

pulumi.export(
    "private_subnet_ids",
    [private_subnet_1.id, private_subnet_2.id],
)

pulumi.export(
    "public_instance_id",
    public_instance.id,
)

pulumi.export(
    "public_instance_public_ip",
    public_instance.public_ip,
)

pulumi.export(
    "private_instance_id",
    private_instance.id,
)

pulumi.export(
    "private_instance_private_ip",
    private_instance.private_ip,
)
