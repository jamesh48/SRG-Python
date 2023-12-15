import boto3
import json
import pytest
from pprint import pprint
from auth_utilities import fetch_tokens
from moto import mock_dynamodb
from unittest import mock
from data_utilities import fetch_all_activities_strava_req, fetch_all_activities_req, fetch_individual_entry_req

def create_token_table():
  dynamodb = boto3.resource('dynamodb')
  table_name = 'srg-token-table'
  table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': 'athleteId','KeyType': 'HASH'}],
        AttributeDefinitions=[{ 'AttributeName': 'athleteId','AttributeType': 'S' }],
        BillingMode='PAY_PER_REQUEST'
      )
  return table, dynamodb

def create_activities_table():
  dynamodb = boto3.resource('dynamodb')
  table_name = 'srg-activities-table'
  table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
                   {'AttributeName': 'athleteId','KeyType': 'HASH'},
                   {'AttributeName': 'activityId', 'KeyType': 'RANGE'}
                  ],
        AttributeDefinitions=[
                   { 'AttributeName': 'athleteId','AttributeType': 'S' },
                   {'AttributeName': 'activityId', 'AttributeType': 'S'}
                  ],
        BillingMode='PAY_PER_REQUEST'
      )
  return table, dynamodb

def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data
    # Individual Entry Test
    if args[0].startswith('https://www.strava.com/api/v3/activities/12345'):
        return MockResponse({"resource_state": 3, "athlete": {"id": 19812306, "resource_state": 1}, "name": "Stroke & Stride 5k", "distance": 5000.0, "moving_time": 1405, "elapsed_time": 1405, "total_elevation_gain": 0, "type": "Run", "sport_type": "Run", "workout_type": 1, "id": 1624305483, "start_date": "2018-06-08T00:25:00Z", "start_date_local": "2018-06-07T18:25:00Z", "timezone": "(GMT-07:00) America/Denver", "utc_offset": -21600.0, "location_city": None, "location_state": None, "location_country": None, "achievement_count": 0, "kudos_count": 2, "comment_count": 0, "athlete_count": 1, "photo_count": 0, "map": {"id": "a1624305483", "polyline": "", "resource_state": 3, "summary_polyline": ""}, "trainer": False, "commute": False, "manual": True, "private": False, "visibility": "everyone", "flagged": False, "gear_id": None, "start_latlng": [], "end_latlng": [], "average_speed": 3.559, "max_speed": 0, "has_heartrate": False, "heartrate_opt_out": False, "display_hide_heartrate_option": False, "upload_id": None, "external_id": None, "from_accepted_tag": False, "pr_count": 0, "total_photo_count": 1, "has_kudoed": False, "description": "Started the race exhausted from swim, then gradually picked up pace. @2 miles an older gentleman passed me and I picked up my pace significantly to keep up with him. Then at 2.75 miles I passed him and another to move into 10th overall for the finish! \u263a\ufe0f", "calories": 599.1, "perceived_exertion": None, "prefer_perceived_exertion": None, "segment_efforts": [], "best_efforts": [], "photos": {"primary": {"unique_id": "3FA4773C-86B1-492A-8122-91BF3D05634E", "urls": {"600": "https://dgtzuqphqg23d.cloudfront.net/ssx2yKOO58Aoy0NLjnNfij-Zg7-k1cD_mRt9rg_3z7I-576x768.jpg", "100": "https://dgtzuqphqg23d.cloudfront.net/ssx2yKOO58Aoy0NLjnNfij-Zg7-k1cD_mRt9rg_3z7I-96x128.jpg"}, "source": 1, "media_type": 1}, "use_primary_photo": True, "count": 1}, "stats_visibility": [{"type": "heart_rate", "visibility": "everyone"}, {"type": "pace", "visibility": "everyone"}, {"type": "power", "visibility": "everyone"}, {"type": "speed", "visibility": "everyone"}, {"type": "calories", "visibility": "everyone"}], "hide_from_home": False, "embed_token": "dd83f2799477813c25480d6693ee24d3c171e5b0", "similar_activities": {"effort_count": 0, "average_speed": 0, "min_average_speed": 0, "mid_average_speed": 0, "max_average_speed": 0, "pr_rank": None, "frequency_milestone": None, "trend": {"speeds": [], "current_activity_index": None, "min_speed": 0, "mid_speed": 0, "max_speed": 0, "direction": 0}, "resource_state": 2}, "available_zones": []}, 200)
    # All Activities Test
    elif args[0].startswith('https://www.strava.com/api/v3/activities'):
        return MockResponse([{
    "resource_state": 2,
    "athlete": { "id": 19812306, "resource_state": 1 },
    "name": "Morning Swim",
    "distance": 1897.4,
    "moving_time": 2522,
    "elapsed_time": 2522,
    "total_elevation_gain": 0,
    "type": "Swim",
    "sport_type": "Swim",
    "id": 10295631901,
    "start_date": "2023-11-27T15:46:41Z",
    "start_date_local": "2023-11-27T08:46:41Z",
    "timezone": "(GMT-07:00) America/Boise",
    "utc_offset": -25200.0,
    "location_city": None,
    "location_state": None,
    "location_country": "United States",
    "achievement_count": 0,
    "kudos_count": 1,
    "comment_count": 0,
    "athlete_count": 1,
    "photo_count": 0,
    "map": { "id": "a10295631901", "summary_polyline": "", "resource_state": 2 },
    "trainer": True,
    "commute": False,
    "manual": False,
    "private": False,
    "visibility": "everyone",
    "flagged": False,
    "gear_id": None,
    "start_latlng": [],
    "end_latlng": [],
    "average_speed": 0.752,
    "max_speed": 4.572,
    "has_heartrate": True,
    "average_heartrate": 146.6,
    "max_heartrate": 190.0,
    "heartrate_opt_out": False,
    "display_hide_heartrate_option": True,
    "elev_high": 0.0,
    "elev_low": 0.0,
    "upload_id": 11023354664,
    "upload_id_str": "11023354664",
    "external_id": "5730D4C3-C345-4140-8F86-A797250DD200.fit",
    "from_accepted_tag": False,
    "pr_count": 0,
    "total_photo_count": 0,
    "has_kudoed": False
  }], 200)

    return MockResponse(None, 404)

@mock.patch('requests.get', side_effect=mocked_requests_get)
def test_fetch_all_activities(self):
    all_activities = fetch_all_activities_strava_req('123456789', 1)
    print(all_activities[0])
    assert "resource_state" in all_activities[0]

@mock.patch('requests.get', side_effect=mocked_requests_get)
def test_fetch_individual_entry(self):
    individual_entry = fetch_individual_entry_req('12345', '24680')
    individual_entry = json.loads(individual_entry)
    assert "resource_state" in individual_entry


@mock_dynamodb
def test_fetch_all_activities():
    table, dynamodb = create_activities_table()
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
def test_fetch_tokens():
    table, dynamodb = create_token_table()
    table.put_item(
       Item={
       'athleteId': '123456789',
       'accessToken': '13579',
       'refreshToken': '24680'
       }
    )
    tokens = fetch_tokens('123456789', dynamodb)

    assert "athleteId" in tokens
    assert "accessToken" in tokens
    assert "refreshToken" in tokens
