import boto3
import json
import requests
from pprint import pprint
from auth_utilities import get_access_token_from_athlete_id
from flask import Blueprint, make_response, request, jsonify
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor

data_controller_bp = Blueprint('data_controller', __name__)


@data_controller_bp.route('/srg/individualEntry/<entryId>', methods=["GET"])
def route_fetch_individual_entry(entryId):
    return fetch_individual_entry(entryId)


def fetch_individual_entry_req(entryId, access_token):
    url = f"https://www.strava.com/api/v3/activities/{entryId}?include_all_efforts=true"
    r = requests.get(
        url, headers={"Authorization": f"Bearer { access_token }"})
    r = r.json()
    return json.dumps(r)


def fetch_individual_entry(entryId):
    try:
        srg_athlete_id = request.args.get('srg_athlete_id')
        access_token = get_access_token_from_athlete_id(srg_athlete_id)
        data = fetch_individual_entry_req(entryId, access_token)
        return data
    except Exception as e:
        print("Exception")
        return ('<html><style>body { background-color: ivory }</style><div>Individual Entry Fetch Error:</div> <p>%s</p></html>' % e)


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
    r = requests.get(url + '?access_token=' + access_token,
                     params={'page': page, 'per_page': 200})
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
    except Exception as e:
        response = make_response(e)
        response.status_code = 500
        return response


def get_logged_in_user():
    srg_athlete_id = request.args.get('srg_athlete_id')
    access_token = get_access_token_from_athlete_id(srg_athlete_id)
    r = get_logged_in_user_req(access_token)
    return json.dumps(r)


def get_logged_in_user_req(access_token):
    url = "https://www.strava.com/api/v3/athlete"
    r = requests.get(url + '?access_token=' + access_token,
                     params={'scope': 'activity:read_all'})
    r = r.json()
    return r

###### Get Logged In Users Stats ######


@data_controller_bp.route('/srg/getAthleteStats/<athleteId>', methods=["GET"])
def route_get_athlete_stats(athleteId):
    return fetch_athlete_stats(athleteId)


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


def add_all_activities_req(access_token):
    activities_to_add = fetch_all_activities_strava_req(access_token, 1)
    # Sort and Filter Activities
    activities_to_add = sorted(activities_to_add, key=lambda x: (
        x['distance'] / x['moving_time']) if x['moving_time'] != 0 else float('-inf'), reverse=True)

    activities_to_add = list(filter(lambda x: x['type'] in [
                             "Walk", "Swim", "Run", "Ride"], activities_to_add))

    # Upload Activities To DynamoDB
    activities_to_add = [
        {
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
        } for entry in activities_to_add
    ]

    dynamodb = boto3.resource('dynamodb')
    activities_table = dynamodb.Table('srg-activities-table')

    with activities_table.batch_writer() as batch:
        for activity in activities_to_add:
            batch.put_item(Item=activity)

    return activities_to_add

###### Destroy User ######


@data_controller_bp.route('/srg/destroyUser', methods=["GET"])
def route_destroy_user():
    return destroy_user()


def destroy_user():
    srg_athlete_id = request.args.get('srg_athlete_id')
    return destroy_user_req(srg_athlete_id)


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
    with ThreadPoolExecutor() as executor:
        executor.map(delete_item, [
                     (item['athleteId'], item['activityId']) for item in response.get('Items', [])])

    return 'deleted'


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
