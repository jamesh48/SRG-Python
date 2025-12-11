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
                {'AttributeName': 'start_date', 'AttributeType': 'S'},
                {'AttributeName': 'has_achievements', 'AttributeType': 'S'},
                {'AttributeName': 'type_achievements', 'AttributeType': 'S'},
                # Composite sort keys (type#achievements#sortable_value)
                {'AttributeName': 'type_ach_speed_desc', 'AttributeType': 'S'},
                {'AttributeName': 'type_ach_speed_asc', 'AttributeType': 'S'},
                {'AttributeName': 'type_ach_distance_desc', 'AttributeType': 'S'},
                {'AttributeName': 'type_ach_distance_asc', 'AttributeType': 'S'},
                {'AttributeName': 'type_ach_duration_desc', 'AttributeType': 'S'},
                {'AttributeName': 'type_ach_duration_asc', 'AttributeType': 'S'},
                {'AttributeName': 'type_ach_elevation_desc', 'AttributeType': 'S'},
                {'AttributeName': 'type_ach_elevation_asc', 'AttributeType': 'S'},
                {'AttributeName': 'type_ach_achievement_desc', 'AttributeType': 'S'},
                {'AttributeName': 'type_ach_achievement_asc', 'AttributeType': 'S'}
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
                },
                {
                    'IndexName': 'athleteId-hasAchievements-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'has_achievements', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'athleteId-typeAchievements-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'type_achievements', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'athleteId-typeAchSpeedDesc-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'type_ach_speed_desc', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'athleteId-typeAchSpeedAsc-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'type_ach_speed_asc', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'athleteId-typeAchDistanceDesc-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'type_ach_distance_desc', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'athleteId-typeAchDistanceAsc-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'type_ach_distance_asc', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'athleteId-typeAchDurationDesc-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'type_ach_duration_desc', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'athleteId-typeAchDurationAsc-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'type_ach_duration_asc', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'athleteId-typeAchElevationDesc-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'type_ach_elevation_desc', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'athleteId-typeAchElevationAsc-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'type_ach_elevation_asc', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'athleteId-typeAchAchievementDesc-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'type_ach_achievement_desc', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'athleteId-typeAchAchievementAsc-index',
                    'KeySchema': [
                        {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
                        {'AttributeName': 'type_ach_achievement_asc', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("✓ Created srg-activities-table with all GSIs including composite sort key indexes")
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
