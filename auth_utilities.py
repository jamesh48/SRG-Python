import os
import time
from flask import request, redirect, make_response
import requests
import json
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
        "&approval_prompt=force&scope=profile:read_all,activity:read_all"
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
            'athlete_id': athlete_id,
            'access_token': strava_tokens['access_token'],
            'refresh_token': strava_tokens['refresh_token'],
            'expires_at': strava_tokens['expires_at']
        }
        upsert_tokens(tokens)
        return athlete_id
    except Exception as e:
        pprint(e)
        return 'authentication error'


def upsert_tokens(tokens):
    try:
        dynamodb = boto3.resource('dynamodb')
        tokens_table = dynamodb.Table('srg-token-table')
        key = {'athleteId': tokens['athlete_id']}

        update_expression = 'SET #accessTokenAttr = :accessTokenValue, #refreshTokenAttr = :refreshTokenValue, #expiresAtAttr = :expiresAtValue'

        expression_attribute_names = {
            '#accessTokenAttr': 'accessToken',
            '#refreshTokenAttr': 'refreshToken',
            '#expiresAtAttr': 'expiresAt'
        }
        expression_attribute_values = {
            ':accessTokenValue': tokens['access_token'],
            ':refreshTokenValue': tokens['refresh_token'],
            ':expiresAtValue': tokens['expires_at']
        }
        response = tokens_table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names, ExpressionAttributeValues=expression_attribute_values
        )
        return response
    except Exception as e:
        pprint(e)
        return e


def refresh_tokens(athlete_id, refresh_token):
    client_id = os.environ.get('strava_client_id')
    client_secret = os.environ.get('strava_client_secret')
    strava_tokens = requests.post(url="https://www.strava.com/api/v3/oauth/token", data={
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    })
    strava_tokens = strava_tokens.json()
    tokens = {
        'athlete_id': athlete_id,
        'access_token': strava_tokens['access_token'],
        'refresh_token': strava_tokens['refresh_token'],
        'expires_at': strava_tokens['expires_at']
    }
    upsert_tokens(tokens)
    return tokens['access_token']


def fetch_tokens(athlete_id):
    dynamodb = boto3.resource('dynamodb')
    tokens_table = dynamodb.Table('srg-token-table')
    response = tokens_table.get_item(
        Key={
            'athleteId': athlete_id
        },
    )

    return response['Item']


def fetch_tokens_rs(athlete_id):
    lambda_client = boto3.client('lambda')
    function_name = 'rust-fetch-tokens-lambda'
    payload_dict = {
        "queryStringParameters": {
            "athleteId": athlete_id
        }
    }
    payload = json.dumps(payload_dict)
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=payload
    )

    response_payload = json.loads(response['Payload'].read())
    return response_payload['data']


def get_access_token_from_athlete_id(athlete_id):
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
