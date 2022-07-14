import boto3
import json
# import logging
from decimal import Decimal
import os
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.getenv("DB_TABLE_NAME"))

# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s %(levelname)-8s %(message)s',
#                     filename="logs/main.log",
#                     datefmt='%Y-%m-%d %H:%M:%S')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return json.JSONEncoder.default(self, o)

def lambda_handler(event, context):
    connection = event["httpMethod"]
    endpoint = event["path"]
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
    return response

def read_tank(ID):
    try:
        response = table.get_item(Key={'ID': ID})
        if 'Item' in response:
            return read_status(200, response['Item'])
        else:
            return read_status(404, {"Message": "Tank ID %s not found" % ID})
    except Exception as e:
        return read_status(500, {"Message": "An unexpected error occurred"})

def read_tanks():
    try:
        response = table.scan()
        if 'Items' in response:
            return read_status(200, response['Items'])
        else:
            return read_status(404, {"Message": "No tanks exist"})
    except Exception as e:
        return read_status(500, {"Message": "An unexpected error occurred"})

def create_tank(request):
    try:
        response = table.put_item(Item=request)
        body = {"Operation": "CREATE", "ID": request}
        return read_status(201, body)
    except Exception as e:
        return read_status(500, {"Message": "An unexpected error occurred"})

def update_tank(ID, updateKey, updateValue):
    try:
        response = table.update_item(Key={'ID': ID},
                                     UpdateExpression="set %s = :value" % updateKey,
                                     ExpressionAttributeValues={":value": updateValue},
                                     ReturnValues="UPDATED_NEW")
        body = {"Operation": "UPDATE", "Updated": response}
        return read_status(200, body)
    except Exception as e:
        return read_status(500, {"Message": "An unexpected error occurred"})

def delete_tank(ID):
    try:
        response = table.delete_item(Key={'ID': ID}, ReturnValues="ALL_OLD")
        body = {"Operation": "DELETE", "ID": ID}
        return read_status(200, body)
    except Exception as e:
        return read_status(500, {"Message": "An unexpected error occurred"})
