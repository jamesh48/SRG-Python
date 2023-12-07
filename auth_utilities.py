import os
import time
from flask import request
import requests
import boto3
from pprint import pprint
from botocore.exceptions import ClientError

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
