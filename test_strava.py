import boto3
import json
import pytest
from pprint import pprint
from auth_utilities import fetch_tokens, upsert_tokens, refresh_tokens
from moto import mock_dynamodb
from unittest import mock
from data_utilities import fetch_all_activities_strava_req,                fetch_all_activities_req, fetch_individual_entry_req, upload_individual_entry_data_to_db, destroy_user_req, update_one_activity_req, put_activity_update_req, fetch_entry_kudoers_req, destroy_user_tokens_req, save_user_settings_req, get_user_settings_req, fetch_general_individual_entry


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
    if args and args[0].startswith('https://www.strava.com/api/v3/activities/12345/kudos'):
        with open('testing_fixtures/fetch_entry_kudos.json', 'r') as file:
            mock_data = json.load(file)
        return MockResponse(mock_data, 200)
    elif 'url' in kwargs and kwargs['url'].startswith('https://www.strava.com/api/v3/oauth/token'):
        with open('testing_fixtures/refresh_token_strava.json', 'r') as file:
            mock_data = json.load(file)
        return MockResponse(mock_data, 200)
    elif args and args[0].startswith('https://www.strava.com/api/v3/activities/12345?name=testname&description=testdescription'):
        with open('testing_fixtures/update_one_activity_strava.json', 'r') as file:
            mock_data = json.load(file)
        return MockResponse(mock_data, 200)
    # Individual Entry Test
    elif args and args[0].startswith('https://www.strava.com/api/v3/activities/1624305483'):
        with open('testing_fixtures/fetch_individual_entry_strava.json', 'r') as file:
            mock_data = json.load(file)
        return MockResponse(mock_data, 200)
    # All Activities Test
    elif args and args[0].startswith('https://www.strava.com/api/v3/activities'):
        with open('testing_fixtures/fetch_all_activities_strava.json', 'r') as file:
            mock_data = json.load(file)
        return MockResponse(mock_data, 200)

    return MockResponse(None, 404)


@mock.patch('requests.get', side_effect=mocked_requests_get)
def test_fetch_all_strava_activities(self):
    all_activities = fetch_all_activities_strava_req('123456789', 1)
    assert "resource_state" in all_activities[0]


# Strava Test
@mock.patch('requests.get', side_effect=mocked_requests_get)
def test_fetch_individual_entry_from_strava(self):
    individual_entry = fetch_individual_entry_req('1624305483', '24680')
    assert "resource_state" in individual_entry

# DynamoDB Test


@mock_dynamodb
def test_upload_individual_entry_data_to_db():
    table = create_activities_table()
    table.put_item(
        Item={
            'athleteId': '123456789',
            'activityId': '987654321',
            'name': 'Activity Name to Change',
            'location_city': 'Atlantis'
        }
    )
    upload_individual_entry_data_to_db(
        {
            "description": "New Individual Entry Description",
            "device_name": "Apple Watch Series 5",
            "gear": {
                "name": "Brooks Ghost 13"
            },
            "map": {
                "polyline": "egpsFfr~`SKG_@cAEMAc@JaAJgCAc@Ba@Go@CcBHm@@_@QkCAg@@ULy@AQa@EY?i@EyABs@K_@@]Ao@FYAuA@g@C[Dk@As@?[?kAUo@AG@OFwDA_BFgBEe@DyB?mAHIFCN?LDlAEp@AjA@rACv@@|@ApCBz@CvADfEAvBEhBBv@AvABjACj@BpCCj@@~@CrCBjB?nCClBCx@AlCD~@Cx@Bh@CpBBxFCp@@XDP?ZCx@Bz@ExD@rAEnCB`@@zA?vCBf@HHl@H`BH|AAl@Jh@LnAz@XZf@x@\\z@Nd@b@pBDh@BtAO`B?VQz@Cd@?NNNZH`@Al@Kh@@LBPGHAP?l@Hz@E\\Bz@Pf@R`@^l@~@N^XtBItGBtBAfBBzB@NFFzAKtBHlBIj@BbA?`ADlAA\\@fACl@Bn@An@B|BAr@HNDJ`@FHPHRBf@AVDt@?h@Cp@K~@Eh@BlAEj@?n@EZD\\@r@IzBH~CAJ@z@@TEx@?\\B\\C^@HC|@Br@A`ADdBIdBFnAIZ@n@CHBP@jBCp@F~BJdAF^GZADQLaB?cDDcAAkA@Q@wACkABgEGmA@aBCmABqACa@@g@Fg@GwGByAE{EBi@AqAB{DGuDAcDFiDGoBBmA?o@GiAF{@@s@?cBGsDDmEGmADkCIsB?iAGk@@OQuA]iAU_@MKOOKUSw@Yq@Yw@[k@_AgCWkASc@K_@E_@_@yA[sCEwAFyDA_CHyCEoABMKhF@d@Ez@B`AEvA@xAJpAB|@TpBVnAh@hAZjAp@hBz@fB`@dAXhANV?IKc@M[iAkCm@eAiA_E_@w@SaAGy@OkAMqBEmBDk@EkADoDK{@GMQKKAQ@uAP]@KCeAk@_BU",
            },
            "photos": {
                "primary": {
                    "unique_id": "FE5A6821-DC24-4C0B-8ED8-7D6E3104C72C",
                    "urls": {
                        "100": "https://dgtzuqphqg23d.cloudfront.net/73Kj3WBJvWIHJeP_5aOZxW-L5dP_0StLmh-yNVmu3Ws-128x117.jpg",
                        "600": "https://dgtzuqphqg23d.cloudfront.net/73Kj3WBJvWIHJeP_5aOZxW-L5dP_0StLmh-yNVmu3Ws-768x707.jpg"
                    },
                    "source": 1,
                    "media_type": 1
                },
                "use_primary_photo": True,
                "count": 3
            },
            "laps": []
        }, '123456789', '987654321')
    result = table.scan()
    result = result['Items'][0]
    # Old Data is Persisted
    assert 'description' in result
    assert 'athleteId' in result
    assert 'activityId' in result
    assert 'location_city' in result
    # New Data in Introduced
    assert 'individualActivityCached' in result
    assert 'primaryPhotoUrl' in result
    assert 'deviceName' in result
    assert 'gearName' in result
    assert 'mapPolyline' in result


@mock.patch('requests.get', side_effect=mocked_requests_get)
def test_fetch_kudoers(self):
    kudoers = fetch_entry_kudoers_req('12345', '54321')
    assert len(kudoers) == 2
    assert kudoers[0]['firstname'] == 'Joe'
    assert kudoers[1]['firstname'] == 'Gordon'

###### Tests! ######


@mock.patch('requests.put', side_effect=mocked_requests_get)
def test_update_entry_in_strava(self):
    test = put_activity_update_req(
        access_token='accessToken',
        entry_id='12345',
        name="testname",
        description="testdescription"
    )
    assert 'achievement_count' in test


@mock.patch('requests.post', side_effect=mocked_requests_get)
@mock_dynamodb
def test_refresh_tokens(self):
    table = create_token_table()
    access_token = refresh_tokens('13579', '246810')
    strava_tokens = table.scan()
    assert len(strava_tokens['Items']) == 1
    strava_tokens = strava_tokens['Items'][0]
    assert access_token == "12345"
    assert strava_tokens['accessToken'] == "12345"
    assert strava_tokens['refreshToken'] == "246810"
    assert strava_tokens['expiresAt'] == "10000"


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
    assert len(r['Items']) == 1
    r = r['Items'][0]
    assert r['athleteId'] == '123456789'
    assert r['accessToken'] == '24680'
    assert r['refreshToken'] == '13579'
    assert r['expiresAt'] == '1702926653'


@mock_dynamodb
def test_shared_tokens_and_settings():
    table = create_token_table()
    # Table Starts with User Settings
    table.put_item(
        Item={
            'athleteId': '123456789',
            'accessToken': '13579',
            'refreshToken': '24680',
            'expiresAt': '1702926029',
            'defaultSport': 'Run',
            'defaultFormat': "speedDesc"
        }
    )
    # New Tokens Are Loaded
    upsert_tokens(tokens={
        'athlete_id': '123456789',
        'access_token': '24680',
        'refresh_token': '13579',
        'expires_at': '1702926653'
    })

    # User Settings should Persist
    r = table.scan()
    assert len(r['Items']) == 1
    r = r['Items'][0]
    assert 'defaultSport' in r
    assert 'defaultFormat' in r


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
def test_get_user_settings():
    table = create_token_table()
    table.put_item(Item={
        'athleteId': '123456789',
        'accessToken': '13579',
        'refreshToken': '24680',
        'defaultSport': 'running',
        'defaultDate': 'allTime',
        'defaultFormat': 'speedDesc',
        'darkMode': True
    })

    user_settings = get_user_settings_req('123456789')
    assert 'defaultSport' in user_settings
    assert 'defaultFormat' in user_settings
    assert 'defaultDate' in user_settings
    assert 'darkMode' in user_settings


@mock_dynamodb
def test_save_user_settings():
    table = create_token_table()
    table.put_item(Item={
        'athleteId': '123456789',
        'accessToken': '13579',
        'refreshToken': '24680'
    })

    save_user_settings_req('123456789', 'running',
                           'speedDesc', 'allTime', True)

    tokens = table.scan()
    assert tokens['Items'][0]
    assert 'darkMode' in tokens['Items'][0]
    assert 'defaultFormat' in tokens['Items'][0]
    assert 'defaultSport' in tokens['Items'][0]
    assert 'defaultDate' in tokens['Items'][0]
    assert 'athleteId' in tokens['Items'][0]


@mock_dynamodb
def test_destroy_user_tokens():
    table = create_token_table()
    table.put_item(Item={
        'athleteId': '123456789',
        'accessToken': '13579',
        'refreshToken': '24680'
    })
    destroy_user_tokens_req('123456789')
    activities = table.scan()
    assert not activities['Items']


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
        'Activity Name has Changed!',
        'Activity Description has Changed!'
    )
    activities = table.scan()
    activities = activities['Items']
    assert 'athleteId' in activities[0]
    assert 'location_city' in activities[0]
    assert activities[0]['location_city'] == 'Atlantis'
    assert activities[0]['name'] == 'Activity Name has Changed!'


@mock_dynamodb
def test_fetch_shared_activity():
    table = create_activities_table()
    table.put_item(
        Item={
            'athleteId': '123456789',
            'activityId': '987654321',
            'name': 'Activity Name',
            'location_city': 'Atlantis',
            'individualActivityCached': True,
            'primaryPhotoUrl': 'https://dgtzuqphqg23d.cloudfront.net/73Kj3WBJvWIHJeP_5aOZxW-L5dP_0StLmh-yNVmu3Ws-768x707.jpg', 'description': 'New Individual Entry Description',
            'deviceName': 'Apple Watch Series 5',
            'gearName': 'Brooks Ghost 13',
            'laps': '[]',
            'bestEfforts': '[]',
            'segmentEfforts': '[]',
            'mapPolyline': 'egpsFfr~`SKG_@cAEMAc@JaAJgCAc@Ba@Go@CcBHm@@_@QkCAg@@ULy@AQa@EY?i@EyABs@K_@@]Ao@FYAuA@g@C[Dk@As@?[?kAUo@AG@OFwDA_BFgBEe@DyB?mAHIFCN?LDlAEp@AjA@rACv@@|@ApCBz@CvADfEAvBEhBBv@AvABjACj@BpCCj@@~@CrCBjB?nCClBCx@AlCD~@Cx@Bh@CpBBxFCp@@XDP?ZCx@Bz@ExD@rAEnCB`@@zA?vCBf@HHl@H`BH|AAl@Jh@LnAz@XZf@x@\\z@Nd@b@pBDh@BtAO`B?VQz@Cd@?NNNZH`@Al@Kh@@LBPGHAP?l@Hz@E\\Bz@Pf@R`@^l@~@N^XtBItGBtBAfBBzB@NFFzAKtBHlBIj@BbA?`ADlAA\\@fACl@Bn@An@B|BAr@HNDJ`@FHPHRBf@AVDt@?h@Cp@K~@Eh@BlAEj@?n@EZD\\@r@IzBH~CAJ@z@@TEx@?\\B\\C^@HC|@Br@A`ADdBIdBFnAIZ@n@CHBP@jBCp@F~BJdAF^GZADQLaB?cDDcAAkA@Q@wACkABgEGmA@aBCmABqACa@@g@Fg@GwGByAE{EBi@AqAB{DGuDAcDFiDGoBBmA?o@GiAF{@@s@?cBGsDDmEGmADkCIsB?iAGk@@OQuA]iAU_@MKOOKUSw@Yq@Yw@[k@_AgCWkASc@K_@E_@_@yA[sCEwAFyDA_CHyCEoABMKhF@d@Ez@B`AEvA@xAJpAB|@TpBVnAh@hAZjAp@hBz@fB`@dAXhANV?IKc@M[iAkCm@eAiA_E_@w@SaAGy@OkAMqBEmBDk@EkADoDK{@GMQKKAQ@uAP]@KCeAk@_BU'
        }
    )
    response = fetch_general_individual_entry('123456789', '987654321')
    assert 'athleteId' in response
    assert 'activityId' in response
    assert '600' in response.get('photos').get('primary').get('urls')
    assert 'name' in response.get('gear')
    assert 'device_name' in response
    assert 'polyline' in response.get('map')
    assert 'description' in response
    #
    assert not 'mapPolyline' in response
