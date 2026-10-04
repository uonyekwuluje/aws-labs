# Login
pulumi login --local

# Preview Stack
pulumi preview --stack infralabs-stack

# Create Stack 
pulumi up --stack infralabs-stack

# Get Stack Output
pulumi stack output --stack infralabs-stack

# Destroy Stack
pulumi down --stack infralabs-stack
