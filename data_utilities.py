import boto3
import json
import requests
from auth_utilities import get_access_token_from_athlete_id
from flask import Blueprint

data_controller_bp = Blueprint('data_controller', __name__)


@data_controller_bp.route('/individualEntry/<entryId>', methods=["GET"])
def route_fetch_individual_entry(entryId):
    return fetch_individual_entry(entryId)


def fetch_individual_entry(entryId):
    try:
        access_token = get_access_token_from_athlete_id()
        url = "https://www.strava.com/api/v3/activities/" + \
            entryId + "include_all_efforts=true"
        r = requests.get(url + '?access_token=' + access_token)
        r = r.json()
        return json.dumps(r)
    except Exception as e:
        print("Exception")
        return ('<html><style>body { background-color: ivory }</style><div>Individual Entry Fetch Error:</div> <p>%s</p></html>' % e)


@data_controller_bp.route('/allActivities', methods=["GET"])
def route_fetch_all_activities():
    return fetch_all_activities()


def fetch_all_activities():
    try:
        url = "https://www.strava.com/api/v3/activities"
        access_token = get_access_token_from_athlete_id()
        r = requests.get(url + '?access_token=' + access_token)
        r = r.json()
        return json.dumps(r)
    except Exception as e:
        print(
            "Exception when calling ActivitiesApi -> getLoggedInAthleteActivities: %s\n" % e)
        return 'Fetch All Activities Error'
