"""Validación y respuestas compartidas por las funciones Lambda."""

import json
import re

from botocore.exceptions import ClientError


BUCKET_RE = re.compile(r"^(?!\d+\.\d+\.\d+\.\d+$)[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")


class RequestError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(payload, ensure_ascii=False),
    }


def parse_body(event):
    body = event.get("body")
    if isinstance(body, dict):
        return body
    if not isinstance(body, str) or not body:
        raise RequestError("Se requiere un cuerpo JSON.")
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RequestError("El cuerpo no es JSON válido.") from exc
    if not isinstance(data, dict):
        raise RequestError("El cuerpo debe ser un objeto JSON.")
    return data


def required_text(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RequestError(f"El campo '{key}' es obligatorio.")
    return value.strip()


def bucket_name(data):
    name = required_text(data, "bucket")
    if not BUCKET_RE.fullmatch(name) or ".." in name or ".-" in name or "-." in name:
        raise RequestError("Nombre de bucket inválido: use 3 a 63 caracteres en minúsculas, números, puntos o guiones.")
    return name


def directory_name(data):
    name = required_text(data, "directorio").strip("/")
    parts = name.split("/")
    if not name or any(part in ("", ".", "..") for part in parts) or "\\" in name:
        raise RequestError("Directorio inválido.")
    return name + "/"


def file_name(data):
    name = required_text(data, "nombre_archivo")
    if name in (".", "..") or "/" in name or "\\" in name:
        raise RequestError("El nombre del archivo no debe contener rutas.")
    return name


def aws_error(exc):
    code = exc.response.get("Error", {}).get("Code", "S3Error")
    if code in ("NoSuchBucket", "NoSuchKey", "404", "NotFound"):
        status = 404
    elif code in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou", "OperationAborted"):
        status = 409
    elif code in ("InvalidBucketName", "InvalidRequest", "IllegalLocationConstraintException"):
        status = 400
    elif code in ("AccessDenied", "403"):
        status = 403
    else:
        status = 502
    return response(status, {"error": code, "mensaje": str(exc.response.get("Error", {}).get("Message", code))})
