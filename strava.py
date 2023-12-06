from __future__ import print_function
import os
import json
import requests
from pprint import pprint
from dotenv import load_dotenv, find_dotenv
from flask import Flask, redirect, request
load_dotenv(find_dotenv())
# https://medium.com/swlh/using-python-to-connect-to-stravas-api-and-analyse-your-activities-dummies-guide-5f49727aac86

app = Flask(__name__)


@app.route('/individualEntry/<entryId>', methods=["GET"])
def individualEntry(entryId):
    try:
        with open('strava_tokens.json') as json_file:
            strava_tokens = json.load(json_file)
        access_token = strava_tokens['access_token']
        url = "https://www.strava.com/api/v3/activities/" + \
            entryId + "include_all_efforts=true"
        r = requests.get(url + '?access_token=' + access_token)
        r = r.json()
        return json.dumps(r)
    except Exception as e:
        print("Exception")
        return ('<html><style>body { background-color: blue }</style><div>Individual Entry Fetch Error:</div> %s</html>' % e)


@app.route('/allActivities', methods=["GET"])
def data():
    try:
        with open('strava_tokens.json') as json_file:
            strava_tokens = json.load(json_file)
        # List Athlete Activities
        url = "https://www.strava.com/api/v3/activities"
        access_token = strava_tokens['access_token']
        r = requests.get(url + '?access_token=' + access_token)
        r = r.json()
        return json.dumps(r)
    except Exception as e:
        print(
            "Exception when calling ActivitiesApi->getLoggedInAthleteActivities: %s\n" % e)
        return 'Fetch All Activities Error'


@app.route('/auth', methods=["GET"])
def auth():
    client_id = os.environ.get("strava_client_id")
    url = "http://www.strava.com/oauth/authorize?client_id=" + client_id + \
        "&response_type=code&redirect_uri=http://127.0.0.1:5000/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all"
    return redirect(url, code=302)


@app.route('/exchange_token', methods=["GET"])
def exchange_token():
    code = request.args.get('code')
    try:
        client_id = os.environ.get("strava_client_id")
        client_secret = os.environ.get("strava_client_secret")
        response = requests.post(url='https://www.strava.com/oauth/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        })
        strava_tokens = response.json()
        with open('strava_tokens.json', 'w') as outfile:
            json.dump(strava_tokens, outfile)
        with open('strava_tokens.json') as check:
            data = json.load(check)
        print(data)
        return 'authenticated'
    except Exception as e:
        return 'authentication error'


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000)
