## Cloudformation Commands
Cloudformation commands for creating new environment

```
export INFRA_S3_BUCKETNAME="infralabs"
export INFRA_AWS_REGION="us-east-1"
export INFRA_STACKNAME="labsinfra"
```

Create S3 Bucket
```
aws s3api create-bucket --bucket ${INFRA_S3_BUCKETNAME} --region ${INFRA_AWS_REGION}
```

Delete S3 Bucket
```
aws s3api delete-bucket --bucket ${INFRA_S3_BUCKETNAME} --region ${INFRA_AWS_REGION}
```

Delete Bucket Contents
```
aws s3 rm --recursive s3://${INFRA_S3_BUCKETNAME}/
```

Delete Bucket and Contents
```
aws s3 rb s3://${INFRA_S3_BUCKETNAME}/ --force
```

Upload Template Contents
```
aws s3 cp main.yaml s3://${INFRA_S3_BUCKETNAME}/
aws s3 cp cfn_vpc.yaml s3://${INFRA_S3_BUCKETNAME}/
aws s3 cp cfn_ec2_priv_instances.yaml s3://${INFRA_S3_BUCKETNAME}/
aws s3 cp cfn_ec2_pub_instances.yaml s3://${INFRA_S3_BUCKETNAME}/
aws s3 cp cfn_eks_cluster.yml s3://${INFRA_S3_BUCKETNAME}/
```

Validate VPC Template
```
aws cloudformation validate-template \
--template-url https://${INFRA_S3_BUCKETNAME}.s3.amazonaws.com/main.yaml
```

Create Template
```
aws cloudformation create-stack \
--region ${INFRA_AWS_REGION} \
--capabilities CAPABILITY_NAMED_IAM \
--stack-name ${INFRA_STACKNAME} \
--parameters \
   ParameterKey=DomainName,ParameterValue=ctrlabs \
   ParameterKey=BucketName,ParameterValue=infralabs \
   ParameterKey=KeyName,ParameterValue=infracidlabs \
   ParameterKey=VPCName,ParameterValue=prod \
--template-url https://${INFRA_S3_BUCKETNAME}.s3.amazonaws.com/main.yaml 
```

Update Template
```
aws cloudformation update-stack \
--region ${INFRA_AWS_REGION} \
--capabilities CAPABILITY_NAMED_IAM \
--stack-name ${INFRA_STACKNAME} \
--parameters \
   ParameterKey=DomainName,ParameterValue=ctrlabs \
   ParameterKey=BucketName,ParameterValue=infralabs \
   ParameterKey=KeyName,ParameterValue=infracidlabs \
   ParameterKey=VPCName,ParameterValue=prod \
--template-url https://${INFRA_S3_BUCKETNAME}.s3.amazonaws.com/main.yaml 
```

Print Output
```
aws cloudformation describe-stack-resources \
  --stack-name ${INFRA_STACKNAME} \
  --region ${INFRA_AWS_REGION} \
  --output table


aws cloudformation describe-stacks \
  --stack-name ${INFRA_STACKNAME} \
  --region ${INFRA_AWS_REGION} \
  --query "Stacks[0].Outputs" \
  --output table
```


Delete Cloudformation Stacks
```
aws cloudformation delete-stack --stack-name ${INFRA_STACKNAME} --region ${INFRA_AWS_REGION}
```

Get Config
```
aws eks --region us-east-1 update-kubeconfig --name dev1eks01
```

Test Config
```
kubectl get nodes
```
