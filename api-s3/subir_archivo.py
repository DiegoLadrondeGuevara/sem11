import base64
import binascii

import boto3
from botocore.exceptions import ClientError

from api_utils import RequestError, aws_error, bucket_name, directory_name, file_name, parse_body, response


MAX_BYTES = 4 * 1024 * 1024


def lambda_handler(event, context):
    try:
        data = parse_body(event)
        bucket = bucket_name(data)
        prefix = directory_name(data)
        filename = file_name(data)
        encoded = data.get("contenido_base64")
        if not isinstance(encoded, str) or not encoded:
            raise RequestError("El campo 'contenido_base64' es obligatorio.")
        try:
            content = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise RequestError("El archivo no tiene base64 válido.") from exc
        if len(content) > MAX_BYTES:
            raise RequestError("El archivo supera el límite de 4 MiB.", 413)
        content_type = data.get("tipo_contenido", "application/octet-stream")
        if not isinstance(content_type, str) or not content_type or "\n" in content_type or "\r" in content_type:
            raise RequestError("Tipo de contenido inválido.")

        s3 = boto3.client("s3")
        s3.head_bucket(Bucket=bucket)
        existing = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1)
        if not existing.get("KeyCount", 0):
            raise RequestError("El directorio no existe en el bucket.", 404)
        key = prefix + filename
        s3.put_object(Bucket=bucket, Key=key, Body=content, ContentType=content_type)
        return response(201, {"mensaje": "Archivo subido.", "bucket": bucket, "directorio": prefix, "archivo": filename, "key": key, "bytes": len(content)})
    except RequestError as exc:
        return response(exc.status_code, {"error": str(exc)})
    except ClientError as exc:
        return aws_error(exc)
