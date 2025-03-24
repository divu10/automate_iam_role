import json
import boto3
from eventbridge import create_eventbridge_target_role, create_eventbridge_rule
from iam_role import create_iam_role

ORG_ROLE_NAME = "OrganizationAccountAccessRole"

def assume_role_in_child(account_id, role_name):
    """Assumes the OrganizationAccountAccessRole in the child account."""
    sts_client = boto3.client("sts")
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    
    try:
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="AssumedRoleSession"
        )
        credentials = assumed_role["Credentials"]
        return credentials
    except Exception as e:
        print(f"Error assuming role in child account {account_id}: {e}")
        return None

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    try:
        # Extract the new account ID from the event
        account_id = event.get("detail", {}).get("userIdentity", {}).get("accountId", "")

        if not account_id:
            print("No account ID found in event.")
            return {"status": "Failed", "error": "No account ID found"}

        # Assume role in the child account
        credentials = assume_role_in_child(account_id, ORG_ROLE_NAME)
        if not credentials:
            return {"status": "Failed", "error": "Failed to assume role in child account"}

        # Create a session using the assumed role credentials
        child_session = boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"]
        )

        # Create IAM role for EventBridge target
        event_bus_target_role_arn = create_eventbridge_target_role(child_session)
        if not event_bus_target_role_arn:
            return {"status": "Failed", "error": "Failed to create IAM role for EventBridge target"}

        # Create EventBridge rule in the child account
        create_eventbridge_rule(child_session, event_bus_target_role_arn)

        # Create IAM role in the child account
        create_iam_role(child_session)

        return {"status": "Success", "account_id": account_id}

    except Exception as e:
        print(f"Error processing event: {e}")
        return {"status": "Failed", "error": str(e)}