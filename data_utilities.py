import boto3
import json
import requests
from auth_utilities import get_access_token_from_athlete_id
from flask import Blueprint

data_controller_bp = Blueprint('data_controller', __name__)


@data_controller_bp.route('/srg/individualEntry/<entryId>', methods=["GET"])
def route_fetch_individual_entry(entryId):
    return fetch_individual_entry(entryId)


def fetch_individual_entry_req(entryId, access_token):
    url = f"https://www.strava.com/api/v3/activities/{entryId}?include_all_efforts=true"
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"})
    r = r.json()
    return json.dumps(r)


def fetch_individual_entry(entryId):
    try:
        access_token = get_access_token_from_athlete_id()
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
      print("Exception when calling ActivitiesApi -> getLoggedInAthleteActivities: %s\n" % e)
      return ('Fetch All Activities Error: %s\n' % e)

def fetch_all_activities_req(access_token, page):
    url = "https://www.strava.com/api/v3/activities"
    r = requests.get(url + '?access_token=' + access_token, params={ 'page': page, 'per_page': 200 })
    r = r.json()

    if len(r) == 200:
      return r + fetch_all_activities_req(access_token, page + 1)
    return r


def fetch_all_activities():
  access_token = get_access_token_from_athlete_id()
  r = fetch_all_activities_req(access_token, 1)
  return json.dumps(r)

###### Get Logged In User ######
@data_controller_bp.route('/srg/getLoggedInUser', methods=["GET"])
def route_get_logged_in_user():
   try:
      return get_logged_in_user()
   except Exception as e:
      print(e)
      return 'error'

def get_logged_in_user():
   access_token = get_access_token_from_athlete_id()
   r = get_logged_in_user_req(access_token)
   return json.dumps(r)

def get_logged_in_user_req(access_token):
  url = "https://www.strava.com/api/v3/athlete"
  r = requests.get(url + '?access_token=' + access_token, params={'scope': 'activity:read_all'})
  r = r.json()
  return r



