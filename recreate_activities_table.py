#!/usr/bin/env python
"""
Script to recreate the activities table with GSI in LocalStack
"""
import os
from aws_config import get_dynamodb_resource

# Ensure we're using LocalStack
os.environ['USE_LOCALSTACK'] = 'true'
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'


def recreate_activities_table():
    dynamodb = get_dynamodb_resource()
    client = dynamodb.meta.client

    print("Recreating srg-activities-table with GSI...")

    # Delete existing table
    try:
        print("Deleting existing table...")
        client.delete_table(TableName='srg-activities-table')
        print("✓ Deleted srg-activities-table")
    except client.exceptions.ResourceNotFoundException:
        print("✓ Table doesn't exist, creating new one")

    # Create table with GSI
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
        print("✓ Created srg-activities-table with GSIs: athleteId-type-index, athleteId-startDate-index")
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        return

    # Verify the GSI was created
    print("\nVerifying GSI...")
    response = client.describe_table(TableName='srg-activities-table')
    gsis = response['Table'].get('GlobalSecondaryIndexes', [])
    if gsis:
        for gsi in gsis:
            print(f"✓ GSI '{gsi['IndexName']}' created successfully")
    else:
        print("✗ No GSIs found")

    print("\nTable recreation complete!")


if __name__ == '__main__':
    recreate_activities_table()
