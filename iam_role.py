import json
import boto3

IAM_ROLE_NAME = "Dev-tag-role"

# IAM Trust Policy
IAM_TRUST_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "arn:aws:iam::024848478165:root"},
            "Action": "sts:AssumeRole",
            "Condition": {}
        }
    ]
}

# IAM Permission Policy with tagging permissions for specified services
IAM_PERMISSION_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "TaggingPermissions",
            "Effect": "Allow",
            "Action": [
                "ec2:CreateTags",
                "ec2:DescribeInstances",
                "ec2:DescribeVpcs",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeNatGateways",
                "ec2:DescribeVpcEndpoints",
                "ec2:DescribeVolumes",
                "s3:PutBucketTagging",
                "s3:GetBucketTagging",
                "lambda:TagResource",
                "lambda:GetFunction",
                "elasticfilesystem:CreateTags",
                "elasticfilesystem:DescribeFileSystems",
                "fsx:TagResource",
                "fsx:DescribeFileSystems",
                "elasticloadbalancing:AddTags",
                "elasticloadbalancing:DescribeLoadBalancers",
                "route53:ChangeTagsForResource",
                "route53:ListTagsForResource",
                "rds:AddTagsToResource",
                "rds:DescribeDBInstances",
                "dynamodb:TagResource",
                "dynamodb:DescribeTable",
                "elasticache:AddTagsToResource",
                "elasticache:DescribeCacheClusters",
                "kms:TagResource",
                "kms:ListResourceTags"
            ],
            "Resource": "*"
        }
    ]
}

def create_iam_role(child_session):
    """Creates an IAM role in the child account."""
    iam_client = child_session.client("iam")

    try:
        # Create IAM role
        response = iam_client.create_role(
            RoleName=IAM_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(IAM_TRUST_POLICY),
            Description="Dev-tag-role for managing AWS resource tags"
        )
        role_arn = response["Role"]["Arn"]
        print(f"IAM Role Created: {role_arn}")

        # Attach inline policy
        iam_client.put_role_policy(
            RoleName=IAM_ROLE_NAME,
            PolicyName="DevTagRolePolicy",
            PolicyDocument=json.dumps(IAM_PERMISSION_POLICY)
        )
        print("IAM Policy Attached to Role")

    except Exception as e:
        print(f"Error creating IAM role: {e}")