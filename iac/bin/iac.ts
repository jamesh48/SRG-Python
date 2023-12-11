#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { SRGPythonStack } from '../lib/srg-python-stack';

const app = new cdk.App();

const {
  AWS_ACCOUNT_NUMBER,
  AWS_ACM_CERTIFICATE_ARN,
  AWS_CLUSTER_ARN,
  AWS_DEFAULT_SG,
  AWS_LOAD_BALANCER_ARN,
  AWS_VPC_ID,
  CDK_REGION,
  STRAVA_CLIENT_ID,
  STRAVA_CLIENT_SECRET,
} = process.env;

if (!AWS_ACCOUNT_NUMBER) {
  throw new Error('AWS_ACCOUNT_NUMBER environment variable is undefined!');
}

if (!CDK_REGION) {
  throw new Error('CDK_REGION environment variable is undefined!');
}

if (!AWS_ACM_CERTIFICATE_ARN) {
  throw new Error('AWS_ACM_CERTIFICATE_ARN environment variable is undefined!');
}

if (!AWS_CLUSTER_ARN) {
  throw new Error('AWS_CLUSTER_ARN environment variable is undefined!');
}

if (!AWS_DEFAULT_SG) {
  throw new Error('AWS_DEFAULT_SG environment variable is undefined!');
}

if (!AWS_LOAD_BALANCER_ARN) {
  throw new Error('AWS_LOAD_BALANCER_ARN environment variable is undefined!');
}

if (!AWS_VPC_ID) {
  throw new Error('AWS_VPC_ID environment variable is undefined!');
}

// SVC Variables
if (!STRAVA_CLIENT_ID) {
  throw new Error('STRAVA_CLIENT_ID environment variable is undefined!');
}

if (!STRAVA_CLIENT_SECRET) {
  throw new Error('STRAVA_CLIENT_SECRET environment variable is undefined!');
}

new SRGPythonStack(app, 'SRGPythonStack', {
  aws_env: {
    AWS_ACM_CERTIFICATE_ARN,
    AWS_LOAD_BALANCER_ARN,
    AWS_CLUSTER_ARN,
    AWS_DEFAULT_SG,
    AWS_VPC_ID,
  },
  svc_env: {
    STRAVA_CLIENT_ID,
    STRAVA_CLIENT_SECRET,
  },
  env: {
    account: AWS_ACCOUNT_NUMBER,
    region: CDK_REGION,
  },
});
