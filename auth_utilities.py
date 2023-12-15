import os
import time
from flask import request, redirect, make_response
import requests
import boto3
from pprint import pprint
from botocore.exceptions import ClientError
from flask import Blueprint


auth_controller_bp = Blueprint('auth_controller', __name__)


@auth_controller_bp.route('/srg/auth', methods=["GET"])
def route_auth():
    return auth()


def auth():
    client_id = os.environ.get("strava_client_id")
    strava_exc_token_redirect_uri = os.environ.get(
        "strava_exc_token_redirect_uri"
    )

    url = "http://www.strava.com/oauth/authorize?client_id=" + client_id + \
        "&response_type=code&redirect_uri=" + strava_exc_token_redirect_uri + \
        "/srg/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all"
    return redirect(url, code=302)


@auth_controller_bp.route('/srg/exchange_token', methods=["GET"])
def route_exchange_token():
    return exchange_token()


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
        response = make_response(redirect('https://stravareportgenerator.com'))
        # set_cookie comes after make_response
        response.set_cookie('srg_athlete_id', athlete_id)
        return response
    except Exception as e:
        pprint(e)
        return 'authentication error'


def upsert_tokens(athlete_id, tokens, dynamodb=None):
    try:
        dynamodb = boto3.resource('dynamodb')
        tokens_table = dynamodb.Table('srg-token-table')
        response = tokens_table.put_item(
            Item={
                "athleteId": athlete_id,
                "accessToken": tokens['access_token'],
                "refreshToken": tokens['refresh_token'],
                "expiresAt": tokens['expires_at']
            }
        )

        pprint(response)
        return response
    except Exception as e:
        pprint(e)
        return e


def refresh_tokens(athlete_id, refresh_token):
    client_id = os.environ.get('strava_client_id')
    client_secret = os.environ.get('strava_client_secret')
    tokens = requests.post(url="https://www.strava.com/api/v3/oauth/token", data={
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    })
    tokens = tokens.json()
    upsert_tokens(athlete_id, tokens)
    return tokens['access_token']


def fetch_tokens(athlete_id, dynamodb=None):
    print(os.environ.get('AWS_REGION'))
    dynamodb = boto3.resource('dynamodb')
    tokens_table = dynamodb.Table('srg-token-table')
    response = tokens_table.get_item(
        Key={
            'athleteId': athlete_id
        },
    )
    if 'Item' in response:
        return response['Item']
    else:
        raise ClientError({ 'Error': { 'Message': 'No athlete_id token found' }}, 'fetch_tokens')

def get_access_token_from_athlete_id():
    athlete_id = request.cookies.get('srg_athlete_id')
    tokens = fetch_tokens(athlete_id)

    # Check to see if the token is expired
    now = time.time()
    later = tokens['expiresAt']

    if now > later:
        pprint('expired token!')
        access_token = refresh_tokens(athlete_id, tokens['refreshToken'])
        return access_token
    else:
        pprint('Token not yet expired!')
        return tokens['accessToken']
