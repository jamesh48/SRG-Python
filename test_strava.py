import boto3
import json
import pytest
from pprint import pprint
from auth_utilities import fetch_tokens, upsert_tokens
from moto import mock_dynamodb
from unittest import mock
from data_utilities import fetch_all_activities_strava_req, fetch_all_activities_req, fetch_individual_entry_req, destroy_user_req, update_one_activity_req, put_activity_update_req, fetch_entry_kudoers_req


def create_token_table():
    dynamodb = boto3.resource('dynamodb')
    table_name = 'srg-token-table'
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': 'athleteId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[
            {'AttributeName': 'athleteId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    return table


def create_activities_table():
    dynamodb = boto3.resource('dynamodb')
    table_name = 'srg-activities-table'
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'athleteId', 'KeyType': 'HASH'},
            {'AttributeName': 'activityId', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'athleteId', 'AttributeType': 'S'},
            {'AttributeName': 'activityId', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    return table


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data
    # Entry Kudos Test
    if args[0].startswith('https://www.strava.com/api/v3/activities/12345/kudos'):
        with open('testing_fixtures/fetch_entry_kudos.json', 'r') as file:
            mock_data = json.load(file)
        return MockResponse(mock_data, 200)
    elif args[0].startswith('https://www.strava.com/api/v3/activities/12345?name=testname&description=testdescription'):
        with open('testing_fixtures/update_one_activity_strava.json', 'r') as file:
            mock_data = json.load(file)
        return MockResponse(mock_data, 200)
    # Individual Entry Test
    elif args[0].startswith('https://www.strava.com/api/v3/activities/12345'):
        with open('testing_fixtures/fetch_individual_entry_strava.json', 'r') as file:
            mock_data = json.load(file)
        return MockResponse(mock_data, 200)
    # All Activities Test
    elif args[0].startswith('https://www.strava.com/api/v3/activities'):
        with open('testing_fixtures/fetch_all_activities_strava.json', 'r') as file:
            mock_data = json.load(file)
        return MockResponse(mock_data, 200)

    return MockResponse(None, 404)


@mock.patch('requests.get', side_effect=mocked_requests_get)
def test_fetch_all_strava_activities(self):
    all_activities = fetch_all_activities_strava_req('123456789', 1)
    assert "resource_state" in all_activities[0]


@mock.patch('requests.get', side_effect=mocked_requests_get)
def test_fetch_individual_entry_from_strava(self):
    individual_entry = fetch_individual_entry_req('12345', '24680')
    individual_entry = json.loads(individual_entry)
    assert "resource_state" in individual_entry

@mock.patch('requests.get', side_effect=mocked_requests_get)
def test_fetch_kudoers(self):
    kudoers = fetch_entry_kudoers_req('12345', '54321')
    assert len(kudoers) == 2
    assert kudoers[0]['firstname'] == 'Joe'
    assert kudoers[1]['firstname'] == 'Gordon'

@mock.patch('requests.put', side_effect=mocked_requests_get)
def test_update_entry_in_strava(self):
    test = put_activity_update_req(
        access_token='accessToken',
        entry_id='12345',
        name="testname",
        description="testdescription"
    )
    assert 'achievement_count' in test

###### Tests! ######


@mock_dynamodb
def test_upsert_tokens():
    table = create_token_table()
    table.put_item(
        Item={
            'athleteId': '123456789',
            'accessToken': '13579',
            'refreshToken': '24680',
            'expiresAt': '1702926029'
        }
    )
    upsert_tokens(tokens={
        'athlete_id': '123456789',
        'access_token': '24680',
        'refresh_token': '13579',
        'expires_at': '1702926653'
    })

    r = table.scan()
    r = r['Items'][0]
    assert r['athleteId'] == '123456789'
    assert r['accessToken'] == '24680'
    assert r['refreshToken'] == '13579'
    assert r['expiresAt'] == '1702926653'


@mock_dynamodb
def test_fetch_all_activities_same_user():
    table = create_activities_table()
    table.put_item(
        Item={
            'athleteId': '123456789',
            'activityId': '987654321'
        }
    )

    table.put_item(
        Item={
            'athleteId': '123456789',
            'activityId': '123456789'
        }
    )
    activities = fetch_all_activities_req('123456789')

    # Assertions
    assert len(activities) == 2
    assert 'activityId' in activities[0]
    assert 'activityId' in activities[1]
    assert activities[0]['activityId'] != activities[1]['activityId']


@mock_dynamodb
def test_fetch_all_activities_different_users():
    table = create_activities_table()
    table.put_item(
        Item={
            'athleteId': '123456789',
            'activityId': '987654321'
        }
    )

    table.put_item(
        Item={
            'athleteId': '987654321',
            'activityId': '123456789'
        }
    )
    user_one_activities = fetch_all_activities_req('123456789')
    user_two_activities = fetch_all_activities_req('987654321')

    # Assertions
    assert len(user_one_activities) == 1
    assert 'activityId' in user_one_activities[0]

    assert len(user_two_activities) == 1
    assert 'activityId' in user_two_activities[0]


@mock_dynamodb
def test_fetch_tokens():
    table = create_token_table()
    table.put_item(
        Item={
            'athleteId': '123456789',
            'accessToken': '13579',
            'refreshToken': '24680'
        }
    )
    tokens = fetch_tokens('123456789')

    assert "athleteId" in tokens
    assert "accessToken" in tokens
    assert "refreshToken" in tokens


@mock_dynamodb
def test_destroy_user():
    table = create_activities_table()
    table.put_item(
        Item={
            'athleteId': '123456789',
            'activityId': '987654321'
        }
    )

    table.put_item(
        Item={
            'athleteId': '123456789',
            'activityId': '123456789'
        }
    )

    activities = table.scan()
    activities = activities['Items']
    assert len(activities) == 2
    response = destroy_user_req('123456789')
    activities = table.scan()
    activities = activities['Items']
    assert len(activities) == 0


@mock_dynamodb
def test_update_one_activity():
    table = create_activities_table()
    table.put_item(
        Item={
            'athleteId': '123456789',
            'activityId': '987654321',
            'name': 'Activity Name to Change',
            'location_city': 'Atlantis'
        }
    )
    activities = table.scan()
    activities = activities['Items']
    assert len(activities) == 1
    assert 'athleteId' in activities[0]
    assert 'location_city' in activities[0]
    assert activities[0]['name'] == 'Activity Name to Change'
    update_one_activity_req(
        '123456789',
        '987654321',
        'Activity Name has Changed!'
    )
    activities = table.scan()
    activities = activities['Items']
    assert 'athleteId' in activities[0]
    assert 'location_city' in activities[0]
    assert activities[0]['location_city'] == 'Atlantis'
    assert activities[0]['name'] == 'Activity Name has Changed!'
