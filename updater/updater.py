import os
import boto3
import botocore
import json
import requests
from datetime import datetime

def handle(event, context):

    # Helper class to convert a DynamoDB item to JSON.
    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                if o % 1 > 0:
                    return float(o)
                else:
                    return int(o)
            return super(DecimalEncoder, self).default(o)

    API = os.environ['API_ENDPOINT']

    TOKEN = os.environ['TELEGRAM_TOKEN']
    BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)

    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.Table('cewe_orders')

    response = table.scan()

    for item in response["Items"]:
        order_number = item['order']
        chat_id = item['chat_id']
        old_status = item['order_status']
        old_date = datetime.fromtimestamp(float(item["last_date"]))

        response = requests.get(API + order_number)
        response = response.json()

        new_date = datetime.now()
        new_status = response['summaryStateCode']
        new_price = response["summaryPriceText"]
        new_delivery = response['deliveryText']

        if old_status != new_status:
            table.update_item(
                Key={
                    'order': order_number
                },
                UpdateExpression="set order_status = :s, last_date=:d",
                ExpressionAttributeValues={
                    ':s': new_status,
                    ':d': str(datetime.now().timestamp())
                }
            )

            # Send message NEW STATUS
            if new_status == "DELIVERED":
                message = "Your order {} has been delivered to {}".format(order_number, new_delivery)
                message += "\n Price: {}".format(new_price)

                table.delete_item(
                    Key={
                        'order': order_number
                    }
                )
            elif new_status == "ERROR":
                message = "Your order {} could not be found.\nIt may take several days for Cewe to start tracking your order.\nIt is also possible that the order number is incorrect.".format(order_number)
            else:
                message = "Your order {} has a new status: {}".format(order_number, new_status)
                if new_price is not "":
                    message += "\nPrice: {}".format(new_price)
                if new_delivery is not "":
                    message += "\nDelivery: {}".format(new_delivery)

            data = {"text": message.encode("utf8"), "chat_id": chat_id}
            url = BASE_URL + "/sendMessage"
            requests.post(url, data)


        elif (new_date - old_date).days > 14:
            table.delete_item(
                Key={
                    'order': order_number
                }
            )

            message = "Your order {} hasn't been updated for too long.\nIt has been removed from the system."
            data = {"text": message.encode("utf8"), "chat_id": chat_id}
            url = BASE_URL + "/sendMessage"
            requests.post(url, json.dumps(data))


    return


