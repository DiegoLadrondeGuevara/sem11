import boto3
from botocore.exceptions import ClientError

from api_utils import RequestError, aws_error, bucket_name, directory_name, parse_body, response


def lambda_handler(event, context):
    try:
        data = parse_body(event)
        bucket = bucket_name(data)
        prefix = directory_name(data)
        s3 = boto3.client("s3")
        s3.head_bucket(Bucket=bucket)
        existing = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1)
        if existing.get("KeyCount", 0):
            return response(200, {"mensaje": "El directorio ya existe.", "bucket": bucket, "directorio": prefix})
        # S3 no tiene carpetas reales: un objeto vacío con sufijo / las representa.
        s3.put_object(Bucket=bucket, Key=prefix, Body=b"")
        return response(201, {"mensaje": "Directorio creado.", "bucket": bucket, "directorio": prefix})
    except RequestError as exc:
        return response(exc.status_code, {"error": str(exc)})
    except ClientError as exc:
        return aws_error(exc)
