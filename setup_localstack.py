#!/usr/bin/env python
"""
Setup script for creating DynamoDB tables in LocalStack
"""
import os
from aws_config import get_dynamodb_resource

# Ensure we're using LocalStack
os.environ['USE_LOCALSTACK'] = 'true'
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'


def create_tables():
    dynamodb = get_dynamodb_resource()

    print("Creating DynamoDB tables in LocalStack...")

    # Create token table
    try:
        token_table = dynamodb.create_table(
            TableName='srg-token-table',
            KeySchema=[
                {'AttributeName': 'athleteId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'athleteId', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("✓ Created srg-token-table")
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print("✓ srg-token-table already exists")

    # Create activities table
    try:
        activities_table = dynamodb.create_table(
            TableName='srg-activities-table',
            KeySchema=[
                {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                {'AttributeName': 'activityId', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'athleteId', 'AttributeType': 'S'},
                {'AttributeName': 'activityId', 'AttributeType': 'S'},
                {'AttributeName': 'type', 'AttributeType': 'S'},
                {'AttributeName': 'start_date', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'athleteId-type-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'type', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'athleteId-startDate-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'start_date', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("✓ Created srg-activities-table")
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print("✓ srg-activities-table already exists")

    print("\nTables created successfully!")

    # List all tables
    client = dynamodb.meta.client
    tables = client.list_tables()
    print(f"\nAvailable tables: {tables['TableNames']}")


if __name__ == '__main__':
    create_tables()
