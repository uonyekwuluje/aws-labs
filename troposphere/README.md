# Python Requirements
Install pip packages
```
pip3 install -r requirements.txt
```

## Resource Links
* [EC2 Links](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-instance.html)
* [Troposphere](https://github.com/cloudtools/troposphere/blob/main/examples/EC2InstanceSample.py)
* [Quick Cheatsheet](https://blog.spikeseed.cloud/easy-infrastructure-as-code-with-troposphere/)

## Build commands
* Create VPC `./build_infrastructure.py create-update-vpc-stack --vpc_name stg`
* Create Security Group `./build_infrastructure.py create-security-group-stack --vpc_name stg`
* Create Instances `./build_infrastructure.py create-instance-stack --vpc_name stg`
* Delete Stack `./build_infrastructure.py delete-stack --vpc_name stg`
