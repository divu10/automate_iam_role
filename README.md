# AWS Automated IAM Role and EventBridge Rule Creation for Child Accounts

## Overview
This documentation provides a detailed explanation of the implementation for automating the creation of IAM roles and EventBridge rules in newly added child accounts within an AWS Organization. The solution ensures that the necessary IAM roles and EventBridge rules are automatically created in any new child account, eliminating the need for manual intervention.

The solution consists of three main components:

1. **Lambda Function (```lambda function.py```)**: The core function that triggers when a new child account is added to the organization. It assumes a role in the child account and creates the required IAM roles and EventBridge rules.
2. **EventBridge Module (`eventbridge.py`)**: Handles the creation of EventBridge rules and the associated IAM role for cross-account event delivery.
3. **IAM Role Module (`iam_role.py`)**: Handles the creation of an IAM role with tagging permissions for various AWS services.

---

## Architecture
The solution works as follows:

1. **Event Trigger**: When a new child account is added to the AWS Organization, an event is generated in the parent account.
2. **Lambda Function Execution**: The Lambda function is triggered by the event. It extracts the new child account ID from the event and assumes the `OrganizationAccountAccessRole` in the child account.
3. **IAM Role Creation**: The Lambda function creates an IAM role in the child account with permissions to manage tags for various AWS services.
4. **EventBridge Rule Creation**: The Lambda function creates an EventBridge rule in the child account to monitor specific AWS API calls and forwards events to the parent account's default event bus.
5. **Cross-Account Event Delivery**: The EventBridge rule in the child account uses an IAM role to send events to the parent account's event bus.

---

## Code Explanation
### 1. Lambda Function (`lambda_function.py`)
The Lambda function is the entry point of the solution. It performs the following tasks:

- **Event Handling**: The function is triggered by an event from AWS Organizations when a new child account is added. It extracts the account ID from the event.
- **Role Assumption**: The function assumes the `OrganizationAccountAccessRole` in the child account using AWS STS (Security Token Service).
- **IAM Role Creation**: The function calls the `create_iam_role` function from the `iam_role.py` module to create an IAM role in the child account with tagging permissions.
- **EventBridge Rule Creation**: The function calls the `create_eventbridge_target_role` and `create_eventbridge_rule` functions from the `eventbridge.py` module to create an EventBridge rule and the associated IAM role in the child account.

#### Key Functions:
- `assume_role_in_child(account_id, role_name)`: Assumes the `OrganizationAccountAccessRole` in the child account.
- `lambda_handler(event, context)`: The main Lambda handler function that processes the event and orchestrates the creation of IAM roles and EventBridge rules.

---

### 2. EventBridge Module (`eventbridge.py`)
This module handles the creation of EventBridge rules and the associated IAM role for cross-account event delivery.

#### Key Components:
- `EVENT_RULE_NAME`: The name of the EventBridge rule.
- `EVENT_BUS_TARGET_ROLE_NAME`: The name of the IAM role used by EventBridge to send events to the parent account's event bus.
- `EVENT_PATTERN`: The event pattern that triggers the EventBridge rule. It monitors specific AWS API calls (e.g., `RunInstances`, `CreateVpc`, etc.) from various AWS services.
- `EVENT_BUS_TARGET_POLICY`: The IAM policy that allows EventBridge to send events to the parent account's event bus.

#### Key Functions:
- `create_eventbridge_target_role(child_session)`: Creates an IAM role in the child account that allows EventBridge to send events to the parent account's event bus.
- `create_eventbridge_rule(child_session, event_bus_target_role_arn)`: Creates an EventBridge rule in the child account and adds a target to the parent account's default event bus.

---

### 3. IAM Role Module (`iam_role.py`)
This module handles the creation of an IAM role in the child account with permissions to manage tags for various AWS services.

#### Key Components:
- `IAM_ROLE_NAME`: The name of the IAM role.
- `IAM_TRUST_POLICY`: The trust policy that allows the parent account to assume the role in the child account.
- `IAM_PERMISSION_POLICY`: The IAM policy that grants permissions to manage tags for various AWS services (e.g., EC2, S3, Lambda, etc.).

#### Key Functions:
- `create_iam_role(child_session)`: Creates an IAM role in the child account with the specified trust and permission policies.

---

## Prerequisites
Before deploying the solution, ensure the following:

1. **AWS Organization**: The solution assumes that you have an AWS Organization set up with a parent account and child accounts.
2. **IAM Role in Child Accounts**: Each child account must have the `OrganizationAccountAccessRole` IAM role, which is automatically created when the account is added to the organization.
3. **Lambda Execution Role**: The Lambda function must have permissions to assume roles in child accounts and create IAM roles and EventBridge rules.

---

## Deployment Steps
1. **Create the Lambda Function:**
   - Create a Lambda function in the parent account .
   - Configure the Lambda function to trigger on AWS Organizations events (e.g., `CreateAccountResult`).

2. **Set Up Permissions:**
   - Ensure the Lambda execution role has the necessary permissions to assume roles in child accounts and create IAM roles and EventBridge rules.

## IAM ROLE -Trust Relationships
```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
```
## IAM ROLE - Policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:us-east-1:024848478165:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudtrail:CreateTrail",
                "cloudtrail:StartLogging",
                "cloudtrail:StopLogging",
                "cloudtrail:DescribeTrails",
                "cloudtrail:DeleteTrail"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "sts:assumeRole",
            "Resource": "arn:aws:iam::*:role/OrganizationAccountAccessRole"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:us-east-1:024848478165:log-group:/aws/lambda/LambdaFunctiontoAssumeRole:*"
            ]
        },
        {
            "Sid": "Statement1",
            "Effect": "Allow",
            "Action": [
                "events:PutEvents"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```
## EventBridge Rule - To trigger lambda function
```json
{
  "detail": {
    "eventName": ["RunInstances", "CreateVpc", "CreateSecurityGroup", "CreateSubnet", "CreateFunction20150331", "CreateBucket", "CreateDBInstance", "CreateTable", "CreateVolume", "CreateLoadBalancer", "CreateInternetGateway", "CreateNatGateway", "AllocateAddress", "CreateVpcEndpoint", "CreateTransitGateway", "CreateMountTarget", "CreateDomain", "CreateQueue", "CreateTopic", "CreateKey", "CreateCluster", "CreateClusterV2", "CreateNotebookInstance", "PutMetricAlarm", "CreateLogGroup", "CreateBroker", "CreateNamespace", "CreateWorkgroup", "CreateProcessingJob", "CreateEndpoint", "CreateModel", "CreateLabelingJob", "CreateTrainingJob", "CreateTransformJob", "CreateUserProfile", "CreateWorkteam"],
    "eventSource": ["ec2.amazonaws.com", "elasticloadbalancing.amazonaws.com", "s3.amazonaws.com", "rds.amazonaws.com", "lambda.amazonaws.com", "dynamodb.amazonaws.com", "elasticfilesystem.amazonaws.com", "es.amazonaws.com", "sqs.amazonaws.com", "sns.amazonaws.com", "kms.amazonaws.com", "redshift.amazonaws.com", "redshift-serverless.amazonaws.com", "sagemaker.amazonaws.com", "ecs.amazonaws.com", "monitoring.amazonaws.com", "logs.amazonaws.com", "kafka.amazonaws.com", "amazonmq.amazonaws.com"]
  },
  "detail-type": ["AWS API Call via CloudTrail"],
  "source": ["aws.ec2", "aws.elasticloadbalancing", "aws.rds", "aws.lambda", "aws.s3", "aws.dynamodb", "aws.elasticfilesystem", "aws.es", "aws.sqs", "aws.sns", "aws.kms", "aws.ecs", "aws.redshift", "aws.redshift-serverless", "aws.sagemaker", "aws.monitoring", "aws.logs", "aws.kafka", "aws.amazonmq"]
}
```

### Target
The target of the EventBridge rule is both the Lambda functions that will be triggered when the specified events occur.


3. **Test the Solution:**
   - Add a new child account to the organization and verify that the IAM role and EventBridge rule are automatically created in the child account.

---

## Error Handling
The solution includes basic error handling to log and return errors if any step fails. For example:
- If the Lambda function fails to assume the role in the child account, it logs the error and returns a failure status.
- If the IAM role or EventBridge rule creation fails, the error is logged, and the function returns a failure status.

---
## LOGS

IAM Role Created for EventBridge Target: arn:aws:iam::676206943909:role/EventBridgeTargetRole
IAM Policy Attached to EventBridge Target Role
EventBridge Rule Created: arn:aws:events:us-east-1:676206943909:rule/MyEventRule
EventBridge Target Added: arn:aws:events:us-east-1:024848478165:event-bus/default
IAM Role Created: arn:aws:iam::676206943909:role/Dev-tag-role
IAM Policy Attached to Role

Bucket created: finalterstgas in Account: 676206943909
Buckets in account 676206943909: ['finalterstgas']
Tagging bucket finalterstgas in account 676206943909
Successfully tagged bucket: finalterstgas


## Conclusion
This solution automates the creation of IAM roles and EventBridge rules in newly added child accounts within an AWS Organization. By eliminating the need for manual intervention, it ensures that tagging permissions and event monitoring are consistently applied across all child accounts.

