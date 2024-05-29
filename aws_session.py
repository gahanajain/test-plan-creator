import boto3
from botocore.exceptions import ClientError
from datetime import datetime

def assume_role(role_arn, external_id):
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    sts_client = boto3.client('sts')
    try:
        assumed_role_object = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"TestPlanCreatorSession{timestamp_str}",
            ExternalId=external_id
        )
        return assumed_role_object['Credentials']
    except ClientError as e:
        print(f"Error assuming role: {e}")
        return None
