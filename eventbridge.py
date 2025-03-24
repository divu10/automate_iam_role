import json
import boto3

EVENT_RULE_NAME = "MyEventRule"
EVENT_BUS_TARGET_ROLE_NAME = "EventBridgeTargetRole"

# EventBridge Rule Pattern
EVENT_PATTERN = {
    "detail": {
        "eventName": [
            "RunInstances", "CreateVpc", "CreateSecurityGroup", "CreateSubnet", "CreateFunction20150331", "CreateBucket",
            "CreateDBInstance", "CreateTable", "CreateVolume", "CreateLoadBalancer", "CreateInternetGateway", "CreateNatGateway",
            "AllocateAddress", "CreateVpcEndpoint", "CreateMountTarget", "CreateQueue", "CreateTopic", "CreateKey"
        ],
        "eventSource": [
            "ec2.amazonaws.com", "elasticloadbalancing.amazonaws.com", "s3.amazonaws.com", "rds.amazonaws.com",
            "lambda.amazonaws.com", "dynamodb.amazonaws.com", "elasticfilesystem.amazonaws.com", "fsx.amazonaws.com",
            "elasticache.amazonaws.com", "kms.amazonaws.com", "route53.amazonaws.com"
        ]
    },
    "detail-type": ["AWS API Call via CloudTrail"],
    "source": [
        "aws.ec2", "aws.elasticloadbalancing", "aws.rds", "aws.lambda", "aws.s3", "aws.dynamodb",
        "aws.elasticfilesystem", "aws.fsx", "aws.elasticache", "aws.kms", "aws.route53"
    ]
}

# IAM Role Policy for EventBridge Target
EVENT_BUS_TARGET_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "events:PutEvents",
            "Resource": "arn:aws:events:us-east-1:024848478165:event-bus/default"
        }
    ]
}

def create_eventbridge_target_role(child_session):
    """Creates an IAM role for EventBridge to send events to the root account's default event bus."""
    iam_client = child_session.client("iam")

    try:
        # Create IAM role
        response = iam_client.create_role(
            RoleName=EVENT_BUS_TARGET_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "events.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }),
            Description="Role for EventBridge to send events to the root account's default event bus"
        )
        role_arn = response["Role"]["Arn"]
        print(f"IAM Role Created for EventBridge Target: {role_arn}")

        # Attach inline policy
        iam_client.put_role_policy(
            RoleName=EVENT_BUS_TARGET_ROLE_NAME,
            PolicyName="EventBridgeTargetPolicy",
            PolicyDocument=json.dumps(EVENT_BUS_TARGET_POLICY)
        )
        print("IAM Policy Attached to EventBridge Target Role")

        return role_arn

    except Exception as e:
        print(f"Error creating IAM role for EventBridge target: {e}")
        return None

def create_eventbridge_rule(child_session, event_bus_target_role_arn):
    """Creates an EventBridge rule in the child account and adds a target to the root account's default event bus."""
    events_client = child_session.client("events")
    
    try:
        # Create EventBridge rule
        response = events_client.put_rule(
            Name=EVENT_RULE_NAME,
            EventPattern=json.dumps(EVENT_PATTERN),
            State="ENABLED",
            Description="EventBridge rule for AWS API calls via CloudTrail"
        )
        print(f"EventBridge Rule Created: {response['RuleArn']}")

        # Add target to the rule (default event bus in the root account)
        target_arn = "arn:aws:events:us-east-1:024848478165:event-bus/default"
        events_client.put_targets(
            Rule=EVENT_RULE_NAME,
            Targets=[
                {
                    "Id": "RootAccountDefaultBusTarget",
                    "Arn": target_arn,
                    "RoleArn": event_bus_target_role_arn  # RoleArn is required for cross-account targets
                }
            ]
        )
        print(f"EventBridge Target Added: {target_arn}")

    except Exception as e:
        print(f"Error creating EventBridge rule or adding target: {e}")