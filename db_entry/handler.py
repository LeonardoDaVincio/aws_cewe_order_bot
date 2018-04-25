import json
import os
import sys
from datetime import datetime
import requests
import boto3
import re

TOKEN = os.environ['TELEGRAM_TOKEN']
BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)

dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
table = dynamodb.Table('cewe_orders')


def hello(event, context):
    """
    Lambda handler.
    :param event: Contains the message from telegram
    :param context: Not used
    :return:
    """
    data = json.loads(event["body"])
    # data = event["body"] #debug
    message = str(data["message"]["text"])
    chat_id = data["message"]["chat"]["id"]
    first_name = data["message"]["chat"]["first_name"]

    if "start" in message:
        response = "Hello {} please send me your order number with /addorder 1234-1234".format(first_name)
        data = {"text": response.encode("utf8"), "chat_id": chat_id}
        url = BASE_URL + "/sendMessage"
        requests.post(url, json.dumps(data))

    if "/addorder" in message:
        order_number = re.search(r'\d*-\d*', message).group(0)  # Filters out the order number
        table.put_item(
            Item={
                'order': order_number,
                'order_status': 'Not yet tested',
                'last_date': str(datetime.now().timestamp()),
                'chat_id': chat_id
            }
        )

        response = "Your order has been added! \nIt may take a while until Cewe starts processing the order."
        data = {"text": response.encode("utf8"), "chat_id": chat_id}
        url = BASE_URL + "/sendMessage"
        requests.post(url, data)

    return {"statusCode": 200}
