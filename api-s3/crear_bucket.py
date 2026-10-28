import boto3
from botocore.exceptions import ClientError

from api_utils import RequestError, aws_error, bucket_name, parse_body, response


def lambda_handler(event, context):
    try:
        name = bucket_name(parse_body(event))
        s3 = boto3.client("s3")
        region = s3.meta.region_name or "us-east-1"
        params = {"Bucket": name}
        if region != "us-east-1":
            params["CreateBucketConfiguration"] = {"LocationConstraint": region}
        s3.create_bucket(**params)
        return response(201, {"mensaje": "Bucket creado.", "bucket": name, "region": region})
    except RequestError as exc:
        return response(exc.status_code, {"error": str(exc)})
    except ClientError as exc:
        return aws_error(exc)
