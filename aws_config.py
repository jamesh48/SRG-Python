import boto3
import os
from dotenv import load_dotenv

load_dotenv()


def get_dynamodb_resource():
    """
    Returns a boto3 DynamoDB resource configured for either LocalStack or AWS.
    """
    use_localstack = os.getenv('USE_LOCALSTACK', 'false').lower() == 'true'

    if use_localstack:
        localstack_endpoint = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
        return boto3.resource(
            'dynamodb',
            endpoint_url=localstack_endpoint,
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'test'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'test')
        )
    else:
        # Production: use default AWS configuration
        return boto3.resource('dynamodb')
