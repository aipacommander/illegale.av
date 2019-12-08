import json
import boto3


DB = boto3.resource('dynamodb')


def lambda_handler(event, context):
    table_name = 'IlligalAvSiteUrlList'
    table = DB.Table(table_name)
    res = table.scan()
    
    print(event, context)
    return {
        'statusCode': 200,
        'body': json.dumps(res['Items'])
    }