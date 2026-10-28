import boto3
from botocore.exceptions import ClientError

from api_utils import aws_error, response


def lambda_handler(event, context):
    try:
        buckets = boto3.client("s3").list_buckets().get("Buckets", [])
        return response(200, {"lista_buckets": [item["Name"] for item in buckets]})
    except ClientError as exc:
        return aws_error(exc)
