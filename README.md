# Amazon Web Services Labs
Collection of code and config snippets

# Install AWS CLI Tool
Install the latest cli tool
```
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```
Log into the AWS Console and generate your `Access Key` and `Secret Key` then configure your CLI.
```
mkdir ~/.aws

vim ~/.aws/config 
>>
[default]
region=us-east-1
output=json

vim ~/.aws/credentials
>> 
[default]
aws_access_key_id="xxxxxxxxxxxxxxxxx"
aws_secret_access_key="xxxxxxxxx"
```
