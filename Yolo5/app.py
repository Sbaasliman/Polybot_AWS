import time
from pathlib import Path
from detect import run  # Assuming `detect` module contains your object detection code
import yaml
from loguru import logger
import os
import boto3
import json
import requests
import flask
from decimal import Decimal
import threading  # Import threading module

app = flask.Flask(__name__)

# Define your AWS and Flask configurations here
region_db = 'us-west-2'
dynamodb_table = 'Sabaa_dynamodb2'
s3_bucket = 'naghambucket'
queue_name = 'Sabaa_SQS'
region_secret = 'eu-central-1'
region_s3 = 'us-east-2'
region_sqs = 'us-east-1'
path_cert = 'PUBLIC.pem'

# Initialize AWS clients
sqs_client = boto3.client('sqs', region_name=region_sqs)
s3_client = boto3.client('s3')
dynamodb_resource = boto3.resource('dynamodb', region_name=region_db)

# Load COCO names for object detection
with open("data/coco128.yaml", "r") as stream:
    names = yaml.safe_load(stream)['names']

# Flask health check endpoints
@app.route('/health')
def health_check():
    return 'Ok', 200

@app.route('/liveness')
def liveness():
    return 'Ok', 200

@app.route('/readiness')
def readiness():
    return 'Ok', 200

# SQS message consumer function
def consume():
    while True:
        response = sqs_client.receive_message(QueueUrl=queue_name, MaxNumberOfMessages=1, WaitTimeSeconds=5)

        if 'Messages' in response:
            message = response['Messages'][0]['Body']
            receipt_handle = response['Messages'][0]['ReceiptHandle']
            prediction_id = response['Messages'][0]['MessageId']

            logger.info(f'prediction: {prediction_id}. Start processing')

            # Extract data from message
            message_data = json.loads(message)
            img_name = message_data['img_name']
            chat_id = message_data['chat_id']

            # Download image from S3
            original_img_path = f"{img_name}"
            s3_client.download_file(s3_bucket, img_name, original_img_path)
            logger.info(f'prediction: {prediction_id}/{original_img_path}. Download img completed')

            # Run object detection
            run(
                weights='yolov5s.pt',
                data='data/coco128.yaml',
                source=original_img_path,
                project='usr/src/app',
                name=prediction_id,
                save_txt=True
            )

            logger.info(f'prediction: {prediction_id}/{original_img_path}. Object detection completed')

            # Upload predicted image to S3
            predicted_img_name = f"predicted_{img_name}"
            predicted_img_path = Path(f'usr/src/app/{prediction_id}/{original_img_path}')
            s3_client.upload_file(str(predicted_img_path), s3_bucket, predicted_img_name)
            logger.info(f'prediction: {prediction_id}/{original_img_path}. Predicted image uploaded to S3')

            # Parse prediction labels
            pred_summary_path = Path(f'usr/src/app/{prediction_id}/labels/{original_img_path.split(".")[0]}.txt')
            if pred_summary_path.exists():
                with open(pred_summary_path) as f:
                    labels = f.read().splitlines()
                    labels = [line.split(' ') for line in labels]
                    labels = [{
                        'class': names[int(l[0])],
                        'cx': float(l[1]),
                        'cy': float(l[2]),
                        'width': float(l[3]),
                        'height': float(l[4]),
                    } for l in labels]

                logger.info(f'prediction: {prediction_id}/{original_img_path}. Prediction summary:\n\n{labels}')

                # Prepare prediction summary
                prediction_summary = {
                    'prediction_id': str(prediction_id),
                    'original_img_path': str(original_img_path),
                    'predicted_img_path': str(Path(predicted_img_path)),
                    'labels': str(labels),
                    'text_results': f"The predicted image is stored in S3 as: {predicted_img_name}",
                    'chat_id': str(chat_id)
                }

                # Store prediction summary in DynamoDB
                table = dynamodb_resource.Table(dynamodb_table)
                table.put_item(Item=prediction_summary)
                logger.info(f'prediction: {prediction_id}. Prediction summary stored in DynamoDB')

                # Send GET request to Polybot for results
                polybot_url = "http://polybotlb-2005455536.eu-central-1.elb.amazonaws.com/results/"
                response = requests.get(polybot_url, params={'predictionId': str(prediction_id)})
                logger.info(f'prediction: {prediction_id}. GET request sent to Polybot')

                # Delete processed message from SQS queue
                sqs_client.delete_message(QueueUrl=queue_name, ReceiptHandle=receipt_handle)
                logger.info(f'prediction: {prediction_id}. Message deleted from SQS')

if __name__ == "__main__":
    # Start consuming messages from SQS
    consume_thread = threading.Thread(target=consume)
    consume_thread.start()

    # Run Flask app
    app.run(host='0.0.0.0', port=80, debug=True)
