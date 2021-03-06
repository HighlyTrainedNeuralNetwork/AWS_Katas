import boto3
import json
import logging
from decimal import Decimal
import os
from dotenv import load_dotenv

if logging.getLogger().handlers:
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().handlers[0].setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
else:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
load_dotenv()
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.getenv("DB_TABLE_NAME"))

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return json.JSONEncoder.default(self, o)

def lambda_handler(event, context):
    connection = event["httpMethod"]
    endpoint = event["path"]
    logging.info("Request made to %s with %s" % (endpoint, connection))
    if connection == "GET" and endpoint == "/status":
        response = read_status(200)
    elif connection == "GET" and endpoint == "/tank":
        response = read_tank(event["queryStringParameters"]["ID"])
    elif connection == "GET" and endpoint == "/tanks":
        response = read_tanks()
    elif connection == "POST" and endpoint == "/tank":
        response = create_tank(json.loads(event["body"]))
    elif connection == "PATCH" and endpoint == "/tank":
        request = json.loads(event["body"])
        response = update_tank(request["ID"], request["updateKey"], request["updateValue"])
    elif connection == "DELETE" and endpoint == "/tank":
        request = json.loads(event["body"])
        response = delete_tank(request["ID"])
    else:
        response = read_status(404, "Not found")
    return response

def read_status(status_code, body=None):
    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }
    }
    if body:
        response["body"] = json.dumps(body, cls=DecimalEncoder)
    logging.info("Responded with %s" % response)
    return response

def read_tank(ID):
    try:
        response = table.get_item(Key={'ID': ID})
        logging.info("Read tank %s" % ID)
        if 'Item' in response:
            return read_status(200, response['Item'])
        else:
            return read_status(404, {"Message": "Tank ID %s not found" % ID})
    except Exception as e:
        logging.error(e)
        return read_status(500, {"Message": "An unexpected error occurred"})

def read_tanks():
    try:
        response = table.scan()
        logging.info("Read %s tanks" % len(response['Items']))
        if 'Items' in response:
            return read_status(200, response['Items'])
        else:
            return read_status(404, {"Message": "No tanks exist"})
    except Exception as e:
        logging.error(e)
        return read_status(500, {"Message": "An unexpected error occurred"})

def create_tank(request):
    try:
        response = table.put_item(Item=request)
        body = {"Operation": "CREATE", "ID": request}
        logging.info("Created tank %s" % request["ID"])
        return read_status(201, body)
    except Exception as e:
        logging.error(e)
        return read_status(500, {"Message": "An unexpected error occurred"})

def update_tank(ID, updateKey, updateValue):
    try:
        response = table.update_item(Key={'ID': ID},
                                     UpdateExpression="set %s = :value" % updateKey,
                                     ExpressionAttributeValues={":value": updateValue},
                                     ReturnValues="UPDATED_NEW")
        body = {"Operation": "UPDATE", "Updated": response}
        logging.info("Updated tank %s" % ID)
        return read_status(200, body)
    except Exception as e:
        logging.error(e)
        return read_status(500, {"Message": "An unexpected error occurred"})

def delete_tank(ID):
    try:
        response = table.delete_item(Key={'ID': ID}, ReturnValues="ALL_OLD")
        body = {"Operation": "DELETE", "ID": ID}
        logging.info("Deleted tank %s" % ID)
        return read_status(200, body)
    except Exception as e:
        logging.error(e)
        return read_status(500, {"Message": "An unexpected error occurred"})
