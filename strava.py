from __future__ import print_function
import os
import json
import requests
from pprint import pprint
from dotenv import load_dotenv, find_dotenv
from flask import Flask, redirect, request, make_response
import boto3
from botocore.exceptions import ClientError

load_dotenv(find_dotenv())
# https://medium.com/swlh/using-python-to-connect-to-stravas-api-and-analyse-your-activities-dummies-guide-5f49727aac86

app = Flask(__name__)


def fetch_tokens(athlete_id, dynamodb=None):
    dynamodb = boto3.resource('dynamodb')
    tokens_table = dynamodb.Table('srg-token-table')
    try:
        response = tokens_table.get_item(
            Key={
                'athleteId': athlete_id
            },
        )
    except ClientError as e:
        print(e.response['No item found'])
    else:
        return response['Item']


def upsert_tokens(athlete_id, tokens, dynamodb=None):
    try:
        dynamodb = boto3.resource('dynamodb')
        tokens_table = dynamodb.Table('srg-token-table')
        response = tokens_table.put_item(
            Item={
                "athleteId": athlete_id,
                "accessToken": tokens['access_token'],
                "refreshToken": tokens['refresh_token']
            }
        )

        return response
    except Exception as e:
        pprint(e)
        return e


def get_access_token_from_athlete_id():
    athlete_id = request.cookies.get('srg_athlete_id')
    tokens = fetch_tokens(athlete_id)
    return tokens['accessToken']


@app.route('/individualEntry/<entryId>', methods=["GET"])
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
        return ('<html><style>body { background-color: ivory }</style><div>Individual Entry Fetch Error:</div> %s</html>' % e)


@app.route('/allActivities', methods=["GET"])
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


@app.route('/auth', methods=["GET"])
def auth():
    client_id = os.environ.get("strava_client_id")
    strava_exc_token_redirect_uri = os.environ.get(
        "strava_exc_token_redirect_uri"
    )

    url = "http://www.strava.com/oauth/authorize?client_id=" + client_id + \
        "&response_type=code&redirect_uri=" + strava_exc_token_redirect_uri + \
        "/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all"
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
        athlete_id = str(strava_tokens['athlete']['id'])
        tokens = {
            'access_token': strava_tokens['access_token'],
            'refresh_token': strava_tokens['refresh_token']
        }
        upsert_tokens(athlete_id, tokens)
        response = make_response(redirect('https://stravareportgenerator.app'))
        response.set_cookie('srg_athlete_id', athlete_id)
        return response
    except Exception as e:
        return 'authentication error'


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000)
