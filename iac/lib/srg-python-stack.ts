import * as cdk from 'aws-cdk-lib';
import * as ecsPatterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

import { Construct } from 'constructs';
import { aws_elasticloadbalancingv2 } from 'aws-cdk-lib';

interface SRGPythonStackProps extends cdk.StackProps {
  aws_env: {
    AWS_ACM_CERTIFICATE_ARN: string;
    AWS_CLUSTER_ARN: string;
    AWS_DEFAULT_SG: string;
    AWS_LOAD_BALANCER_ARN: string;
    AWS_VPC_ID: string;
  };
  svc_env: {
    STRAVA_CLIENT_ID: string;
    STRAVA_CLIENT_SECRET: string;
  };
}

export class SRGPythonStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: SRGPythonStackProps) {
    super(scope, id, props);

    const srgPythonService =
      new ecsPatterns.ApplicationLoadBalancedFargateService(
        this,
        'srg-python-alb',
        {
          certificate: acm.Certificate.fromCertificateArn(
            this,
            'srg-python-imported-certificate',
            props.aws_env.AWS_ACM_CERTIFICATE_ARN
          ),
          cluster: ecs.Cluster.fromClusterAttributes(
            this,
            'srg-python-imported-cluster',
            {
              securityGroups: [
                ec2.SecurityGroup.fromSecurityGroupId(
                  this,
                  'imported-default-sg',
                  props.aws_env.AWS_DEFAULT_SG
                ),
              ],
              clusterName: 'jh-e1-ecs-cluster',
              clusterArn: props.aws_env.AWS_CLUSTER_ARN,
              vpc: ec2.Vpc.fromLookup(this, 'jh-imported-vpc', {
                vpcId: props.aws_env.AWS_VPC_ID,
              }),
            }
          ),
          loadBalancer:
            aws_elasticloadbalancingv2.ApplicationLoadBalancer.fromLookup(
              this,
              'srg-python-alb-imported',
              {
                loadBalancerArn: props.aws_env.AWS_LOAD_BALANCER_ARN,
              }
            ),
          // loadBalancerName: 'srg-python-alb',
          // redirectHTTP: true,
          taskImageOptions: {
            image: ecs.ContainerImage.fromAsset('../'),
            taskRole: iam.Role.fromRoleName(
              this,
              'jh-ecs-task-definition-role',
              'jh-ecs-task-definition-role'
            ),
            executionRole: iam.Role.fromRoleName(
              this,
              'jh-ecs-task-execution-role',
              'jh-ecs-task-execution-role'
            ),
            environment: {
              strava_client_id: props.svc_env.STRAVA_CLIENT_ID,
              strava_client_secret: props.svc_env.STRAVA_CLIENT_SECRET,
            },
          },
          capacityProviderStrategies: [
            {
              capacityProvider: 'FARGATE_SPOT',
              weight: 1,
            },
          ],
          desiredCount: 1,
          enableExecuteCommand: true,
        }
      );

    new dynamodb.Table(this, 'srg-token-table', {
      tableName: 'srg-token-table',
      partitionKey: { name: 'athleteId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    // new dynamodb.Table(this, 'srg-athlete-activities', {
    //   tableName: 'srg-activities-table',
    //   partitionKey: { name: 'athleteId', type: dynamodb.AttributeType.STRING },
    //   billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    // });
  }
}
