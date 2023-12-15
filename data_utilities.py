import boto3
import json
import requests
from pprint import pprint
from auth_utilities import get_access_token_from_athlete_id
from flask import Blueprint, make_response, request, jsonify

data_controller_bp = Blueprint('data_controller', __name__)


@data_controller_bp.route('/srg/individualEntry/<entryId>', methods=["GET"])
def route_fetch_individual_entry(entryId):
    return fetch_individual_entry(entryId)


def fetch_individual_entry_req(entryId, access_token):
    url = f"https://www.strava.com/api/v3/activities/{entryId}?include_all_efforts=true"
    r = requests.get(url, headers={"Authorization": f"Bearer { access_token }"})
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
  srg_athlete_id = request.args.get('srg_athlete_id')
  access_token = get_access_token_from_athlete_id(srg_athlete_id)
  r = fetch_all_activities_req(access_token, 1)
  return json.dumps(r)

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
  r = requests.get(url + '?access_token=' + access_token, params={ 'scope': 'activity:read_all' })
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



