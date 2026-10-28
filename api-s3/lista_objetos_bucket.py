import boto3
from botocore.exceptions import ClientError

from api_utils import RequestError, aws_error, bucket_name, parse_body, response


def lambda_handler(event, context):
    try:
        name = bucket_name(parse_body(event))
        s3 = boto3.client("s3")
        # list_objects_v2 no incluye Contents cuando el bucket está vacío.
        keys = []
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=name):
            keys.extend(item["Key"] for item in page.get("Contents", []))
        return response(200, {"bucket": name, "lista_objetos": keys})
    except RequestError as exc:
        return response(exc.status_code, {"error": str(exc)})
    except ClientError as exc:
        return aws_error(exc)
