import * as cdk from 'aws-cdk-lib';
import * as ecsPatterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

import { Construct } from 'constructs';
import { aws_elasticloadbalancingv2 } from 'aws-cdk-lib';
import {
  ApplicationListener,
  ApplicationProtocol,
  ApplicationTargetGroup,
  TargetGroupBase,
} from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';

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

    const srgFargateService = new ecs.FargateService(
      this,
      'srg-python-service',
      {
        assignPublicIp: true,
        desiredCount: 1,
        capacityProviderStrategies: [
          {
            capacityProvider: 'FARGATE_SPOT',
            weight: 1,
          },
        ],
        taskDefinition: new ecs.FargateTaskDefinition(
          this,
          'srg-python-task-definition',
          {
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
          }
        ),
        cluster: ecs.Cluster.fromClusterAttributes(this, 'jh-impoted-cluster', {
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
        }),
        enableExecuteCommand: true,
      }
    );

    const container = srgFargateService.taskDefinition.addContainer(
      'srgPython-container',
      {
        environment: {
          strava_client_id: props.svc_env.STRAVA_CLIENT_ID,
          strava_client_secret: props.svc_env.STRAVA_CLIENT_SECRET,
          strava_exc_token_redirect_uri:
            'https://data.stravareportgenerator.app',
        },
        image: ecs.ContainerImage.fromAsset('../'),
        logging: new ecs.AwsLogDriver({
          streamPrefix: 'srgp-container',
          logRetention: RetentionDays.FIVE_DAYS,
        }),
        healthCheck: {
          command: [
            'CMD-SHELL',
            'curl -f http://127.0.0.1:5000/healthcheck || exit 1',
          ],
          interval: cdk.Duration.seconds(30),
          timeout: cdk.Duration.seconds(10),
          retries: 5,
        },
      }
    );

    container.addPortMappings({
      containerPort: 5000,
      hostPort: 5000,
    });

    const albListener = ApplicationListener.fromLookup(
      this,
      'imported-listener',
      {
        listenerArn:
          'arn:aws:elasticloadbalancing:us-east-1:471507967541:listener/app/fsh-fullstack-hrivnak-alb/8777d6587b6e774f/b74b5b3d1406d6d8',
      }
    );

    albListener.addCertificates('srg-certificate', [
      acm.Certificate.fromCertificateArn(
        this,
        'srg-python-imported-certificate',
        props.aws_env.AWS_ACM_CERTIFICATE_ARN
      ),
    ]);
    const targetGroup = new ApplicationTargetGroup(this, 'srg-python-tg', {
      targetGroupName: 'srg-svc-target',
      port: 5000,
      protocol: ApplicationProtocol.HTTP,
      targets: [srgFargateService],
      vpc: ec2.Vpc.fromLookup(this, 'jh-imported-vpc-tg', {
        vpcId: props.aws_env.AWS_VPC_ID,
      }),
      healthCheck: {
        path: '/healthcheck',
        unhealthyThresholdCount: 2,
        healthyHttpCodes: '200',
        healthyThresholdCount: 5,
        interval: cdk.Duration.seconds(30),
        port: '5000',
        timeout: cdk.Duration.seconds(10),
      },
    });

    albListener.addTargetGroups('srg-listener-tg', {
      targetGroups: [targetGroup],
      priority: 10,
      conditions: [
        aws_elasticloadbalancingv2.ListenerCondition.pathPatterns([
          '/healthcheck',
          '/auth',
        ]),
      ],
    });

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
