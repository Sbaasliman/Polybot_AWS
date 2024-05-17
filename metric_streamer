import json
import boto3
import time

def lambda_handler(event, context):
    # TODO implement
    sqs_client = boto3.resource('sqs', region_name='us-east-1')
    asg_client = boto3.client('autoscaling', region_name='eu-central-1')

    AUTOSCALING_GROUP_NAME = 'ASG_Sabaa'
    QUEUE_NAME = 'Sabaa_SQS'

    while True:
        try:
            queue = sqs_client.get_queue_by_name(QueueName=QUEUE_NAME)
            print(f'queue = {queue}')
            msgs_in_queue = int(queue.attributes.get('ApproximateNumberOfMessages'))
            print(f'msgs_in_queue = {msgs_in_queue}')

            asg_groups = asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[AUTOSCALING_GROUP_NAME])['AutoScalingGroups']

            if not asg_groups:
                raise RuntimeError('Autoscaling group not found')
            else:
                asg_size = asg_groups[0]['DesiredCapacity']

            if asg_size == 0:
                print("Desired capacity of Auto Scaling group is zero. Skipping metric calculation.")
                continue

            backlog_per_instance = msgs_in_queue / asg_size
            print(f' \n\n\n backlog_per_instance = {backlog_per_instance}')

            cloudwatch = boto3.client('cloudwatch', region_name='eu-central-1')
            cloudwatch.put_metric_data(
                Namespace='Custom/Metrics',
                MetricData=[
                    {
                        'MetricName': 'SabaaBacklog',
                        'Value': backlog_per_instance,
                        'Unit': 'None'
                    }
                ]
            )

        except Exception as e:
            print("Error:", e)

        time.sleep(30)
#adding policy to the asg
# aws autoscaling put-scaling-policy --policy-name sqs-scale-out-policy \
#   --auto-scaling-group-name ASG_Sabaa --policy-type TargetTrackingScaling \
#   --target-tracking-configuration file://~/config.json \
#   --region eu-central-1
# config.json
# {
#    "TargetValue":3 ,
#    "CustomizedMetricSpecification": {
#       "MetricName": "SabaaBacklog",
#       "Namespace": "Custom/Metrics",
#       "Statistic": "Average",
#       "Unit": "None"
#    }
# }
