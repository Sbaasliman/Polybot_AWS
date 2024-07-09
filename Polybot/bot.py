import telebot
from loguru import logger
import os
import time
import boto3
import json
import requests
from botocore.exceptions import NoCredentialsError
from pathlib import Path
import pymongo


class Bot:
    def __init__(self, token, telegram_chat_url, s3_bucket_name, region_s3, sqs_queue_name, region_sqs, path_cert):
        # Initialize Telegram Bot client
        self.region_sqs = region_sqs
        self.sqs_queue_name = sqs_queue_name
        self.region_s3 = region_s3
        self.s3_bucket_name = s3_bucket_name
        self.telegram_bot_client = telebot.TeleBot(token)
        self.telegram_bot_client.remove_webhook()
        self.path_cert = path_cert
        print(path_cert)
        print(token)
        print(telegram_chat_url)

        time.sleep(0.5)
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60, certificate=open(self.path_cert, 'rb'))

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    # Method to send text message
    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    # Method to check if current message contains a photo
    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    # Method to download user photo
    def download_user_photo(self, msg):
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')
        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)
        return file_info.file_path

    # Method to handle incoming messages
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')

class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])

class ObjectDetectionBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')
        if self.is_current_msg_photo(msg):
            # Upload photo to S3 and send job to SQS queue
            photo_path = self.download_user_photo(msg)
            print('Photo successfully downloaded')
            sqs_client = boto3.client('sqs', region_name=self.region_sqs)
            s3_client = boto3.client('s3', region_name=self.region_s3)
            photo_key = os.path.basename(photo_path)
            print('Uploading...')
            try:
                s3_client.upload_file(photo_path, self.s3_bucket_name, photo_key)
                print('File successfully uploaded')
                logger.info(f'Uploaded photo to S3: {photo_key}')
            except NoCredentialsError:
                print('Credentials not available')
            sqs_message = {'chat_id': msg['chat']['id'], 'img_name': photo_key}
            sqs_client.send_message(QueueUrl=self.sqs_queue_name, MessageBody=json.dumps(sqs_message))
            self.send_text(msg['chat']['id'], 'Your image is being processed. Please wait...')
            logger.info(f'Message to the Telegram end-user sent')
