import boto3
import json
import requests
from pprint import pprint
from auth_utilities import get_access_token_from_athlete_id
from flask import Blueprint, make_response, request, jsonify
from decimal import Decimal
from urllib.parse import quote
from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor

data_controller_bp = Blueprint('data_controller', __name__)


class RateLimitError(Exception):
    pass


@data_controller_bp.route('/srg/activityStream/<entry_id>', methods=['GET'])
def route_get_activity_stream(entry_id):
    return get_activity_stream(entry_id)


def get_activity_stream(entry_id):
    srg_athlete_id = request.args.get('srg_athlete_id')
    access_token = get_access_token_from_athlete_id(srg_athlete_id)
    activity_stream = get_activity_stream_req(entry_id, access_token)
    return activity_stream


def get_activity_stream_req(entry_id, access_token):
    url = f"https://www.strava.com/api/v3/activities/{entry_id}/streams?keys=latlng&key_by_type=true"
    r = requests.get(
        url, headers={"Authorization": f"Bearer { access_token }"}
    )
    r = r.json()
    return r


@data_controller_bp.route('/srg/getUserSettings', methods=['GET'])
def route_get_user_settings():
    try:
        return get_user_settings()
    except Exception as e:
        error_message = str(e)
        response = make_response(jsonify({'error': error_message}), 500)
        return response


def get_user_settings():
    srg_athlete_id = request.args.get('srg_athlete_id')
    return get_user_settings_req(srg_athlete_id)


def get_user_settings_req(athlete_id):
    dynamodb = boto3.resource('dynamodb')
    tokens_table = dynamodb.Table('srg-token-table')
    response = tokens_table.get_item(
        Key={
            'athleteId': athlete_id
        },
    )
    user_settings_only = {
        "darkMode": response['Item']['darkMode'],
        "defaultSport": response['Item']['defaultSport'],
        "defaultFormat": response['Item']['defaultFormat'],
        'defaultDate': response['Item']['defaultDate']
    }
    return user_settings_only


@data_controller_bp.route('/srg/saveUserSettings', methods=['POST'])
def route_save_user_settings():
    return save_user_settings()


def save_user_settings():
    srg_athlete_id = request.args.get('srg_athlete_id')
    if request.is_json:
        json_data = request.get_json()
        default_sport = json_data['defaultSport']
        default_format = json_data['defaultFormat']
        default_date = json_data['defaultDate']
        dark_mode = json_data['darkMode']
        save_user_settings_req(srg_athlete_id, default_sport,
                               default_format, default_date, dark_mode)
        return jsonify({'status': 'success', 'message': 'Saved User Settings'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid JSON payload'})


def save_user_settings_req(srg_athlete_id, default_sport, default_format, default_date, dark_mode):
    dynamodb = boto3.resource('dynamodb')
    key = {'athleteId': srg_athlete_id}
    update_expression = 'SET #defaultSportAttr = :defaultSportValue, #defaultFormatAttr = :defaultFormatValue, #defaultDateAttr = :defaultDateValue, #darkModeAttr = :darkModeValue'
    expression_attribute_names = {
        '#defaultSportAttr': 'defaultSport',
        '#defaultFormatAttr': 'defaultFormat',
        '#defaultDateAttr': 'defaultDate',
        '#darkModeAttr': 'darkMode'
    }
    expression_attribute_values = {
        ':defaultSportValue': default_sport,
        ':defaultFormatValue': default_format,
        ':defaultDateValue': default_date,
        ':darkModeValue': dark_mode
    }
    table = dynamodb.Table('srg-token-table')
    table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names, ExpressionAttributeValues=expression_attribute_values
    )
    return 'ok'


@data_controller_bp.route('/srg/entryKudos/<entryId>', methods=["GET"])
def route_fetch_entry_kudoers(entryId):
    return fetch_entry_kudoers(entryId)


def update_cached_kudos_comments(srg_athlete_id, entry_id, kudos, comments):
    kudos_len = len(kudos)
    comment_len = len(comments)

    dynamodb = boto3.resource('dynamodb')
    table_name = 'srg-activities-table'
    table = dynamodb.Table(table_name)
    key = {'athleteId': srg_athlete_id, 'activityId': entry_id}
    update_expression = 'SET #kudosCountAttr = :kudosCountValue, #commentCountAttr = :commentCountValue'
    expression_attribute_names = {
        '#kudosCountAttr': 'kudos_count',
        '#commentCountAttr': 'comment_count'
    }
    expression_attribute_values = {
        ':kudosCountValue': kudos_len,
        ':commentCountValue': comment_len
    }
    table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names, ExpressionAttributeValues=expression_attribute_values
    )
    return 'dynamo updated'


def fetch_entry_kudoers(entry_id):
    srg_athlete_id = request.args.get('srg_athlete_id')
    access_token = get_access_token_from_athlete_id(srg_athlete_id)
    comments = fetch_entry_comments_req(entry_id, access_token)
    kudos = fetch_entry_kudoers_req(entry_id, access_token)
    update_cached_kudos_comments(srg_athlete_id, entry_id, kudos, comments)
    return {'comments': comments, 'kudos': kudos}


def fetch_entry_kudoers_req(entry_id, access_token):
    url = f"https://www.strava.com/api/v3/activities/{entry_id}/kudos"
    r = requests.get(
        url, headers={"Authorization": f"Bearer { access_token }"})
    r = r.json()
    return r


def fetch_entry_comments_req(entry_id, access_token):
    url = f"https://www.strava.com/api/v3/activities/{entry_id}/comments"
    r = requests.get(
        url, headers={"Authorization": f"Bearer { access_token }"})
    r = r.json()
    return r


@data_controller_bp.route('/srg/generalIndividualEntry/<athlete_id>/<activity_id>', methods=['GET'])
def route_fetch_general_individual_entry(athlete_id, activity_id):
    return fetch_general_individual_entry(athlete_id, activity_id)


def fetch_general_individual_entry(athlete_id, activity_id):
    dynamodb = boto3.resource('dynamodb')
    activities_table = dynamodb.Table('srg-activities-table')
    response = activities_table.query(
        KeyConditionExpression="#athlete_id = :athlete_id AND #activity_id = :activity_id",
        ExpressionAttributeNames={
            '#athlete_id': 'athleteId',
            "#activity_id": "activityId",
        },
        ExpressionAttributeValues={
            ':athlete_id': athlete_id,
            ":activity_id": activity_id,
        }
    )
    response = response['Items'][0]
    new_response = {**response,
                    "id": int(response.get('activityId')),
                    "best_efforts": json.loads(response.get('bestEfforts')),
                    "segment_efforts": json.loads(response.get('segmentEfforts')),
                    "gear": {
                        "name": response.get('gearName')
                    },
                    "map": {
                        "polyline": response.get('mapPolyline')
                    },
                    "laps": json.loads(response.get("laps")),
                    "device_name": response.get('deviceName'),
                    "photos": {
                        "count": 1,
                        "primary": {
                            "urls": {
                                "600": response.get('primaryPhotoUrl')
                            }
                        }}
                    }
    keys_to_exclude = [
        'mapPolyline',
        'primaryPhotoUrl',
        'bestEfforts',
        'deviceName',
        'gearName',
        'segmentEfforts'
    ]
    new_response_filtered = {
        key: value for key, value in new_response.items() if key not in keys_to_exclude}

    return new_response_filtered


@data_controller_bp.route('/srg/individualEntry/<entryId>', methods=["GET"])
def route_fetch_individual_entry(entryId):
    return fetch_individual_entry(entryId)


def fetch_individual_entry_req(entryId, access_token):
    url = f"https://www.strava.com/api/v3/activities/{entryId}?include_all_efforts=true"
    r = requests.get(
        url, headers={"Authorization": f"Bearer { access_token }"})
    r = r.json()
    return r


def fetch_individual_entry(entry_id):
    try:
        srg_athlete_id = request.args.get('srg_athlete_id')
        access_token = get_access_token_from_athlete_id(srg_athlete_id)
        data = fetch_individual_entry_req(entry_id, access_token)
        upload_individual_entry_data_to_db(data, srg_athlete_id, entry_id)
        return data
    except Exception as e:
        print("Exception")
        return ('<html><style>body { background-color: ivory }</style><div>Individual Entry Fetch Error:</div> <p>%s</p></html>' % e)


def upload_individual_entry_data_to_db(data, srg_athlete_id, entry_id):
    # data section #
    activity_description = data.get('description', '')
    best_efforts = json.dumps(data.get('best_efforts', []))
    device_name = data.get('device_name', '')
    gear_name = data.get('gear', {}).get('name', '')
    laps = json.dumps(data.get('laps', []))
    map_polyline = data.get('map', {}).get('polyline', '')
    primary_photo_url = data.get('photos', {}).get('primary', {})
    if primary_photo_url is not None:
        primary_photo_url = primary_photo_url.get('urls', {}).get('600', '')
    else:
        primary_photo_url = ''
    segment_efforts = json.dumps(data.get('segment_efforts', []))
    # data captured in memory#

    dynamodb = boto3.resource('dynamodb')
    table_name = 'srg-activities-table'
    table = dynamodb.Table(table_name)
    key = {'athleteId': srg_athlete_id, 'activityId': entry_id}

    update_expression = 'SET #indActivityHasBeenCachedAttr = :indActivityHasBeenCachedValue, #primaryPhotoAttr = :primaryPhotoValue, #activityDescriptionAttr = :activityDescriptionValue, #deviceNameAttr = :deviceNameValue, #gearNameAttr = :gearNameValue, #mapPolylineAttr = :mapPolylineValue, #lapsAttr = :lapsValue, #bestEffortsAttr = :bestEffortsValue, #segmentEffortsAttr = :segmentEffortsValue'

    expression_attribute_names = {
        '#indActivityHasBeenCachedAttr': 'individualActivityCached',
        '#primaryPhotoAttr': 'primaryPhotoUrl',
        '#activityDescriptionAttr': 'description',
        '#deviceNameAttr': 'deviceName',
        '#gearNameAttr': 'gearName',
        '#lapsAttr': 'laps',
        '#mapPolylineAttr': 'mapPolyline',
        '#bestEffortsAttr': 'bestEfforts',
        '#segmentEffortsAttr': 'segmentEfforts'
    }

    expression_attribute_values = {
        ':indActivityHasBeenCachedValue': True,
        ':primaryPhotoValue': primary_photo_url,
        ':activityDescriptionValue': activity_description,
        ':deviceNameValue': device_name,
        ':gearNameValue': gear_name,
        ':lapsValue': laps,
        ':mapPolylineValue': map_polyline,
        ':bestEffortsValue': best_efforts,
        ':segmentEffortsValue': segment_efforts
    }
    table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names, ExpressionAttributeValues=expression_attribute_values
    )
    return 'ok'


####### All Activities #######
@data_controller_bp.route('/srg/allActivities', methods=["GET"])
def route_fetch_all_activities():
    try:
        return fetch_all_activities()
    except Exception as e:
        print(
            "Exception when calling ActivitiesApi -> getLoggedInAthleteActivities: %s\n" % e)
        return ('Fetch All Activities Error: %s\n' % e)


def fetch_all_activities_strava_req(access_token, page):
    url = "https://www.strava.com/api/v3/activities"
    r = requests.get(
        url,
        headers={"Authorization": f"Bearer { access_token }"},
        params={'page': page, 'per_page': 200}
    )
    r = r.json()

    if len(r) == 200:
        return r + fetch_all_activities_strava_req(access_token, page + 1)
    return r


def fetch_all_activities_req(srg_athlete_id):
    dynamodb = boto3.resource('dynamodb')
    activities_table = dynamodb.Table('srg-activities-table')
    response = activities_table.query(
        KeyConditionExpression="#athlete_id = :athlete_id",
        ExpressionAttributeNames={
            "#athlete_id": "athleteId",
        },
        ExpressionAttributeValues={
            ":athlete_id": srg_athlete_id,
        }
    )
    return response['Items']


def fetch_all_activities():
    srg_athlete_id = request.args.get('srg_athlete_id')
    r = fetch_all_activities_req(srg_athlete_id)
    return r

###### Get Logged In User ######


@data_controller_bp.route('/srg/getLoggedInUser', methods=["GET"])
def route_get_logged_in_user():
    try:
        return get_logged_in_user()
    except RateLimitError as e:
        error_message = str(e)
        response = make_response(jsonify({'error': error_message}), 429)
        return response
    except Exception as e:
        error_message = str(e)
        response = make_response(jsonify({'error': error_message}), 500)
        return response


def get_logged_in_user():
    srg_athlete_id = request.args.get('srg_athlete_id')
    access_token = get_access_token_from_athlete_id(srg_athlete_id)
    r = get_logged_in_user_req(access_token)
    return json.dumps(r)


def get_logged_in_user_req(access_token):
    url = "https://www.strava.com/api/v3/athlete"
    r = requests.get(
        url + '?access_token=' + access_token,
        params={'scope': 'profile:read_all'}
    )
    r_json = r.json()
    if 'errors' in r_json and any(error.get('code') == 'exceeded' for error in r_json['errors']):
        print('X-RateLimit-Limit')
        pprint(r.headers.get('X-RateLimit-Limit'))
        print('X-RateLimit-Usage')
        pprint(r.headers.get('X-RateLimit-Usage'))
        raise RateLimitError('Rate Limit Exceeded')
    return r_json

###### Get Logged In Users Stats ######


@data_controller_bp.route('/srg/getAthleteStats/<athleteId>', methods=["GET"])
def route_get_athlete_stats(athleteId):
    try:
        return fetch_athlete_stats(athleteId)
    except Exception as e:
        error_message = str(e)
        response = make_response(jsonify({'error': error_message}), 500)
        return response


def fetch_athlete_stats(athleteId):
    access_token = get_access_token_from_athlete_id(athleteId)
    r = fetch_athlete_stats_req(athleteId, access_token)
    return json.dumps(r)


def fetch_athlete_stats_req(athleteId, access_token):
    url = 'https://www.strava.com/api/v3/athletes/' + athleteId + '/stats/'
    r = requests.get(url + '?access_token=' + access_token)
    r = r.json()
    return r

###### Add All Activities ######


@data_controller_bp.route('/srg/addAllActivities', methods=["POST"])
def route_add_all_activities():
    return add_all_activities()


def add_all_activities():
    srg_athlete_id = request.args.get('srg_athlete_id')
    access_token = get_access_token_from_athlete_id(srg_athlete_id)
    activities_to_return = add_all_activities_req(access_token)
    return activities_to_return


def update_or_insert_item(entry, activities_table):
    item = {
        'athleteId': str(entry['athlete']['id']),
        'activityId': str(entry['id']),
        'name': entry['name'],
        'type': entry['type'],
        'start_date': entry['start_date'],
        'distance': Decimal(str(entry['distance'])),
        'moving_time': entry['moving_time'],
        'elapsed_time': entry['elapsed_time'],
        'average_speed': Decimal(str(entry['average_speed'])),
        'max_speed': Decimal(str(entry['max_speed'])),
        'elev_high': Decimal(str(entry['elev_high'])) if 'elev_high' in entry else None,
        'elev_low': Decimal(str(entry['elev_low'])) if 'elev_low' in entry else None,
        'total_elevation_gain': Decimal(str(entry['total_elevation_gain'])),
        'average_heartrate': Decimal(str(entry['average_heartrate'])) if 'average_heartrate' in entry else None,
        'max_heartrate': Decimal(str(entry['max_heartrate'])) if 'max_heartrate' in entry else None,
        'location_city': entry['location_city'],
        'location_state': entry['location_state'],
        'location_country': entry['location_country'],
        'achievement_count': entry['achievement_count'],
        'kudos_count': entry['kudos_count'],
        'comment_count': entry['comment_count'],
        'pr_count': entry['pr_count']
    }

    try:
        activities_table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(athleteId) AND attribute_not_exists(activityId)'
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            activities_table.update_item(
                Key={
                    'athleteId': str(item['athleteId']),
                    'activityId': str(item['activityId']),
                },
                UpdateExpression='SET ' +
                ', '.join([f"#{key} = :{key}" for key in item.keys()
                          if key not in ['athleteId', 'activityId']]),
                ExpressionAttributeNames={
                    f"#{key}": key for key in item.keys() if key not in ['athleteId', 'activityId']
                },
                ExpressionAttributeValues={
                    f":{key}": value for key, value in item.items() if key not in ['athleteId', 'activityId']
                }
            )
        else:
            print(f"Error during put_item: {e}")


def add_all_activities_req(access_token):
    activities_to_add = fetch_all_activities_strava_req(access_token, 1)
    # Sort and Filter Activities
    activities_to_add = sorted(activities_to_add, key=lambda x: (
        x['distance'] / x['moving_time']) if x['moving_time'] != 0 else float('-inf'), reverse=True)

    activities_to_add = list(filter(lambda x: x['type'] in [
                             "Walk", "Swim", "Run", "Ride"], activities_to_add))

    dynamodb = boto3.resource('dynamodb')
    activities_table = dynamodb.Table('srg-activities-table')

    with ThreadPoolExecutor(max_workers=10) as executor:
        def update_function(entry): return update_or_insert_item(
            entry, activities_table)
        executor.map(update_function, activities_to_add)

    print("Update or insert items completed successfully.")
    return activities_to_add

###### Destroy User ######


@data_controller_bp.route('/srg/destroyUser', methods=["GET"])
def route_destroy_user():
    try:
        return destroy_user()
    except Exception as e:
        return ('<html><style>body { background-color: ivory }</style><div>Destroy User Error</div> <p>%s</p></html>' % e)


def destroy_user():
    srg_athlete_id = request.args.get('srg_athlete_id')
    destroy_user_req(srg_athlete_id)
    destroy_user_tokens_req(srg_athlete_id)
    return jsonify({'status': 'success', 'message': 'User Deleted'})


def destroy_user_tokens_req(srg_athlete_id):
    dynamodb = boto3.resource('dynamodb')
    table_name = 'srg-token-table'
    table = dynamodb.Table(table_name)
    table.delete_item(
        Key={
            'athleteId': srg_athlete_id
        }
    )
    return 'deleted tokens'


def destroy_user_req(srg_athlete_id):
    dynamodb = boto3.resource('dynamodb')
    table_name = 'srg-activities-table'
    table = dynamodb.Table(table_name)

    # Use query to find all items with the specified athleteId
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key(
            'athleteId').eq(srg_athlete_id)
    )

    # Delete each item in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(delete_item, [
                     (item['athleteId'], item['activityId']) for item in response.get('Items', [])])

    return 'deleted activities'


def delete_item(keys):
    dynamodb = boto3.resource('dynamodb')
    table_name = 'srg-activities-table'
    table = dynamodb.Table(table_name)

    table.delete_item(
        Key={
            'athleteId': keys[0],
            'activityId': keys[1]
        }
    )


@data_controller_bp.route("/srg/shoeAlert", methods=['PUT'])
def route_put_shoe_activity_update():
    return put_shoe_activity_update()


def put_shoe_activity_update_req(access_token, entry_id, shoe_id):
    encoded_shoe_id = quote(shoe_id)
    url = f"https://www.strava.com/api/v3/activities/{entry_id}?gear_id={encoded_shoe_id}"
    r = requests.put(
        url, headers={"Authorization": f"Bearer { access_token }"}
    )
    r = r.json()
    print(r)
    return r


def update_shoe_one_activity_req(athleteId, activityId, shoe_id, shoe_name):
    dynamodb = boto3.resource('dynamodb')
    table_name = 'srg-activities-table'
    table = dynamodb.Table(table_name)
    key = {'athleteId': athleteId, 'activityId': activityId}
    update_expression = 'SET #shoeIdAttr = :shoeIdValue, #gearNameAttr = :gearNameValue'
    expression_attribute_names = {
        '#shoeIdAttr': 'shoeId',
        '#gearNameAttr': 'gearName'
    }
    expression_attribute_values = {
        ':shoeIdValue': shoe_id,
        ':gearNameValue': shoe_name
    }
    table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names, ExpressionAttributeValues=expression_attribute_values
    )
    return 'ok'


def put_shoe_activity_update():
    # Query Parameters
    srg_athlete_id = request.args.get('srg_athlete_id')
    entry_id = request.args.get('entry_id')
    shoe_id = request.args.get('shoe_id')
    shoe_name = request.args.get('shoe_name')

    # AccessToken
    access_token = get_access_token_from_athlete_id(srg_athlete_id)
    # Update Strava
    put_shoe_activity_update_req(access_token, entry_id, shoe_id)
    # Update Dynamo
    update_shoe_one_activity_req(srg_athlete_id, entry_id, shoe_id, shoe_name)

    return {'message': 'updated activity with shoe!'}


@data_controller_bp.route("/srg/activityUpdate", methods=['PUT'])
def route_put_activity_update():
    return put_activity_update()


def put_activity_update():
    # Query Parameters
    srg_athlete_id = request.args.get('srg_athlete_id')
    entry_id = request.args.get('entry_id')
    name = request.args.get('name')
    description = request.args.get('description')

    # AccessToken
    access_token = get_access_token_from_athlete_id(srg_athlete_id)
    # Update Strava
    put_activity_update_req(access_token, entry_id, name, description)
    # Update Dynamo
    update_one_activity_req(srg_athlete_id, entry_id, name, description)
    return {'message': 'updated activity!'}


def update_one_activity_req(athleteId, activityId, name, description):
    dynamodb = boto3.resource('dynamodb')
    table_name = 'srg-activities-table'
    table = dynamodb.Table(table_name)
    key = {'athleteId': athleteId, 'activityId': activityId}
    update_expression = 'SET #nameAttr = :nameValue, #descriptionAttr = :descriptionValue'
    expression_attribute_names = {
        '#nameAttr': 'name',
        '#descriptionAttr': 'description'
    }
    expression_attribute_values = {
        ':nameValue': name,
        ':descriptionValue': description
    }
    table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names, ExpressionAttributeValues=expression_attribute_values
    )
    return 'ok'


def put_activity_update_req(access_token, entry_id, name, description):
    encoded_name = quote(name)
    encoded_description = quote(description)
    url = f"https://www.strava.com/api/v3/activities/{entry_id}?name={encoded_name}&description={encoded_description}"
    r = requests.put(
        url, headers={"Authorization": f"Bearer { access_token }"}
    )
    r = r.json()
    return r
