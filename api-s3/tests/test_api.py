import base64
import json
import sys
from pathlib import Path
from unittest.mock import Mock

import boto3
import pytest
from botocore.exceptions import ClientError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import crear_bucket
import crear_directorio
import lista_buckets
import lista_objetos_bucket
import subir_archivo


def event(**data):
    return {"body": json.dumps(data)}


def payload(result):
    return json.loads(result["body"])


def test_listar_buckets(monkeypatch):
    client = Mock()
    client.list_buckets.return_value = {"Buckets": [{"Name": "uno"}, {"Name": "dos"}]}
    monkeypatch.setattr(boto3, "client", lambda name: client)
    result = lista_buckets.lambda_handler({}, None)
    assert result["statusCode"] == 200
    assert payload(result)["lista_buckets"] == ["uno", "dos"]


def test_listar_bucket_vacio(monkeypatch):
    client = Mock()
    client.get_paginator.return_value.paginate.return_value = [{}]
    monkeypatch.setattr(boto3, "client", lambda name: client)
    result = lista_objetos_bucket.lambda_handler(event(bucket="sem11-prueba-123"), None)
    assert result["statusCode"] == 200
    assert payload(result)["lista_objetos"] == []


def test_crear_bucket_us_east_1(monkeypatch):
    client = Mock()
    client.meta.region_name = "us-east-1"
    monkeypatch.setattr(boto3, "client", lambda name: client)
    result = crear_bucket.lambda_handler(event(bucket="sem11-prueba-123"), None)
    assert result["statusCode"] == 201
    client.create_bucket.assert_called_once_with(Bucket="sem11-prueba-123")


def test_crear_bucket_otra_region(monkeypatch):
    client = Mock()
    client.meta.region_name = "us-west-2"
    monkeypatch.setattr(boto3, "client", lambda name: client)
    result = crear_bucket.lambda_handler(event(bucket="sem11-prueba-123"), None)
    assert result["statusCode"] == 201
    client.create_bucket.assert_called_once_with(
        Bucket="sem11-prueba-123",
        CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
    )


def test_crear_directorio(monkeypatch):
    client = Mock()
    client.list_objects_v2.return_value = {"KeyCount": 0}
    monkeypatch.setattr(boto3, "client", lambda name: client)
    result = crear_directorio.lambda_handler(event(bucket="sem11-prueba-123", directorio="imagenes/chicas"), None)
    assert result["statusCode"] == 201
    client.put_object.assert_called_once_with(Bucket="sem11-prueba-123", Key="imagenes/chicas/", Body=b"")


def test_subir_imagen_decodifica_bytes(monkeypatch):
    client = Mock()
    client.list_objects_v2.return_value = {"KeyCount": 1}
    monkeypatch.setattr(boto3, "client", lambda name: client)
    content = b"\x89PNG\r\n\x1a\n"
    result = subir_archivo.lambda_handler(
        event(
            bucket="sem11-prueba-123",
            directorio="imagenes/chicas",
            nombre_archivo="ejemplo.png",
            contenido_base64=base64.b64encode(content).decode(),
            tipo_contenido="image/png",
        ),
        None,
    )
    assert result["statusCode"] == 201
    assert payload(result)["bytes"] == len(content)
    client.put_object.assert_called_once_with(
        Bucket="sem11-prueba-123",
        Key="imagenes/chicas/ejemplo.png",
        Body=content,
        ContentType="image/png",
    )


def test_subir_archivo_sin_directorio(monkeypatch):
    client = Mock()
    client.list_objects_v2.return_value = {"KeyCount": 0}
    monkeypatch.setattr(boto3, "client", lambda name: client)
    result = subir_archivo.lambda_handler(
        event(bucket="sem11-prueba-123", directorio="faltante", nombre_archivo="a.txt", contenido_base64="YQ=="),
        None,
    )
    assert result["statusCode"] == 404
    client.put_object.assert_not_called()


@pytest.mark.parametrize("body", ["", "no-json", "[]"])
def test_json_invalido(body):
    result = crear_bucket.lambda_handler({"body": body}, None)
    assert result["statusCode"] == 400


def test_conflicto_bucket(monkeypatch):
    client = Mock()
    client.meta.region_name = "us-east-1"
    client.create_bucket.side_effect = ClientError(
        {"Error": {"Code": "BucketAlreadyExists", "Message": "Ya existe"}}, "CreateBucket"
    )
    monkeypatch.setattr(boto3, "client", lambda name: client)
    result = crear_bucket.lambda_handler(event(bucket="sem11-prueba-123"), None)
    assert result["statusCode"] == 409
