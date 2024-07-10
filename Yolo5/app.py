import time
from pathlib import Path
from detect import run
import yaml
from loguru import logger
import os
import boto3
import json
import requests
import flask
from decimal import Decimal

#
# region_db = os.environ['Region_Dynamodb']
# dynamodb_table = os.environ['Dynamodb_table']
# images_bucket = os.environ['BUCKET_NAME']
# queue_name = os.environ['SQS_QUEUE_NAME']
# region_sqs = os.environ['Region_SQS']

app = flask.Flask(__name__)
region_db = 'us-west-2'
dynamodb_table = 'Sabaa_dynamodb2'
s3_bucket = 'naghambucket'
queue_name = 'Sabaa_SQS'
region_secret = 'eu-central-1'
region_s3 = 'us-east-2'
region_sqs = 'us-east-1'
path_cert = 'PUBLIC.pem'

sqs_client = boto3.client('sqs', region_name=region_sqs)
s3_client = boto3.client('s3')
# dynamodb_client = boto3.client('dynamodb', region_name=region_db)
dynamodb_resource = boto3.resource('dynamodb', region_name=region_db)

with open("data/coco128.yaml", "r") as stream:
    names = yaml.safe_load(stream)['names']
@app.route('/health')
def health_check():
    return 'Ok', 200

@app.route('/liveness')
def liveness():
    return 'Ok', 200
@app.route('/readiness')
def liveness():
    return 'Ok', 200

def consume():
    while True:
        response = sqs_client.receive_message(QueueUrl=queue_name, MaxNumberOfMessages=1, WaitTimeSeconds=5)

        if 'Messages' in response:
            message = response['Messages'][0]['Body']
            receipt_handle = response['Messages'][0]['ReceiptHandle']

            # Use the ReceiptHandle as a prediction UUID
            prediction_id = response['Messages'][0]['MessageId']

            logger.info(f'prediction: {prediction_id}. start processing')

            # Receives a URL parameter representing the image to download from S3
            img_name = ...  # TODO extract from `message`
            chat_id = ...  # TODO extract from `message`
            message_data = json.loads(message)
            img_name = message_data['img_name']
            chat_id = message_data['chat_id']
            original_img_path = ...  # TODO download img_name from S3, store the local image path in original_img_path
            original_img_path = f"{img_name}"
            s3_client.download_file(s3_bucket, img_name, original_img_path)

            logger.info(f'prediction: {prediction_id}/{original_img_path}. Download img completed')

            # Predicts the objects in the image
            run(
                weights='yolov5s.pt',
                data='data/coco128.yaml',
                source=original_img_path,
                project='usr/src/app',
                name=prediction_id,
                save_txt=True
            )

            logger.info(f'prediction: {prediction_id}/{original_img_path}. done')

            # This is the path for the predicted image with labels
            # The predicted image typically includes bounding boxes drawn around the detected objects, along with class labels and possibly confidence scores.
            predicted_img_path = Path(f'usr/src/app/{prediction_id}/{original_img_path}')

            # TODO Uploads the predicted image (predicted_img_path) to S3 (be careful not to override the original image).
            # Construct the new filename for the predicted image
            predicted_img_name = f"predicted_{img_name}"
            # Upload the renamed predicted image to S3
            s3_client.upload_file(str(predicted_img_path), s3_bucket, predicted_img_name)

            # Parse prediction labels and create a summary
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

                logger.info(f'prediction: {prediction_id}/{original_img_path}. prediction summary:\n\n{labels}')
                prediction_id = str(prediction_id)

                # prediction_summary = {
                #     "'{'prediction_id': '" + str(
                #         prediction_id) + "', 'original_img_path': '" + original_img_path + "', 'predicted_img_path': '" + str(
                #         Path(predicted_img_path)) + "', 'labels': '" + str(
                #         labels) + "', 'text_results': 'The predicted image is stored in S3 as: " + predicted_img_name + "', 'chat_id': '" + str(
                #         chat_id) + "'}'"
                # }
                # prediction_summary = {
                #      "{'prediction_id': '" + str(prediction_id) + "', 'original_img_path': '" + str(
                #             original_img_path) + "', 'predicted_img_path': '" + str(
                #             Path(predicted_img_path)) + "', 'labels': '" + str(
                #             labels) + "', 'text_results': 'The predicted image is stored in S3 as: " + str(
                #             predicted_img_name) + "', 'chat_id': '" + str(chat_id) + "'}"
                # }
                prediction_summary = {
                    'prediction_id': str(prediction_id),
                    'original_img_path': str(original_img_path),
                    'predicted_img_path': str(Path(predicted_img_path)),
                    'labels': str(labels),
                    # 'time': time.time(),
                    'text_results': f"The predicted image is stored in S3 as: {predicted_img_name}",
                    'chat_id': str(chat_id)
                }

                logger.info(f'prediction summary : {prediction_summary}')

                # TODO store the prediction_summary in a DynamoDB table
                # Initialize DynamoDB client and table resource
                # table = dynamodb_client.Table(dynamodb_table)
                table = dynamodb_resource.Table(dynamodb_table)

                # Put item into DynamoDB table
                # prediction_summary1 = {
                #     'prediction_id': prediction_id,
                #     'prediction_summary': prediction_summary
                # }
                table.put_item(Item=prediction_summary)
                logger.info(f'putted in DynamoDB table: {prediction_summary}')

                # TODO perform a GET request to Polybot to `/results` endpoint
                polybot_url = "http://polybotlb-2005455536.eu-central-1.elb.amazonaws.com/results/"
                response = requests.get(polybot_url, params={'predictionId': str(prediction_id)})
                sqs_client.delete_message(QueueUrl=queue_name, ReceiptHandle=receipt_handle)


if __name__ == "__main__":
    consume()
    app.run(host='0.0.0.0', port=80, debug=True)