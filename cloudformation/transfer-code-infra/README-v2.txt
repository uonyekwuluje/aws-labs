# Copy Addresses
--------------------------------------------------
aws s3 cp local-user1.txt s3://infracid-transfer-ip-allowlist/user1.txt
aws s3 cp user2.txt s3://infracid-transfer-ip-allowlist/user2.txt
aws s3 cp user3.txt s3://infracid-transfer-ip-allowlist/user3.txt
aws s3 cp user4.txt s3://infracid-transfer-ip-allowlist/user4.txt

# Delete S3 Object
aws s3 rm s3://infracid-transfer-ip-allowlist/user1.txt

vim user1.txt
>>
172.18.5.40/32
11.10.10.3/32
192.168.1.4/32

vim user2.txt
>>
24.38.90.90/32
17.2.60.3/32
10.0.0.3/32

vim user3.txt
>>
19.68.10.40/32
50.67.87.93/32

vim user4.txt
>>
193.68.10.40/32
150.167.87.93/32
177.2.69.30/32
190.50.60.43/32





./s3testops.py adduser-ip-addresses-s3 --username user1 --ip-addresses 12.8.10.160,120.45.56.12,168.4.78.12
>>
Add IP Address for user user1
IP Addresses ['12.8.10.160', '120.45.56.12', '168.4.78.12'] for user user1 added

./s3testops.py list-ip-addresses
>>
--- user1.txt ---
{'Cidr': '12.8.10.160/32', 'Description': 'user1.txt ssh rule'}
{'Cidr': '120.45.56.12/32', 'Description': 'user1.txt ssh rule'}
{'Cidr': '168.4.78.12/32', 'Description': 'user1.txt ssh rule'}

./s3testops.py removeuser-ip-addresses-s3 --username user1 --ip-address 90.67.30.92


