#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Uso: bash scripts/probar_api.sh URL_DEL_STAGE NOMBRE_BUCKET [ARCHIVO]" >&2
  exit 2
fi

api_url="${1%/}"
bucket="$2"
file="${3:-ejemplos/galleta01-small.png}"
directory="imagenes-chicas"
filename="$(basename "$file")"

if [[ ! -f "$file" ]]; then
  echo "No existe el archivo: $file" >&2
  exit 2
fi

request_file="$(mktemp)"
trap 'rm -f "$request_file"' EXIT

printf '\n1. Listar buckets\n'
curl --fail-with-body -sS -i "$api_url/s3/lista-buckets"
printf '\n2. Crear bucket\n'
printf '{"bucket":"%s"}' "$bucket" > "$request_file"
curl --fail-with-body -sS -i -X POST "$api_url/s3/bucket/crear" \
  -H 'Content-Type: application/json' --data-binary "@$request_file"

printf '\n3. Crear directorio\n'
printf '{"bucket":"%s","directorio":"%s"}' "$bucket" "$directory" > "$request_file"
curl --fail-with-body -sS -i -X POST "$api_url/s3/bucket/directorio/crear" \
  -H 'Content-Type: application/json' --data-binary "@$request_file"

printf '\n4. Subir archivo\n'
python3 - "$bucket" "$directory" "$filename" "$file" "$request_file" <<'PY'
import base64
import json
import mimetypes
import pathlib
import sys

bucket, directory, filename, source, output = sys.argv[1:]
content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
data = {
    "bucket": bucket,
    "directorio": directory,
    "nombre_archivo": filename,
    "tipo_contenido": content_type,
    "contenido_base64": base64.b64encode(pathlib.Path(source).read_bytes()).decode("ascii"),
}
pathlib.Path(output).write_text(json.dumps(data), encoding="utf-8")
PY
curl --fail-with-body -sS -i -X POST "$api_url/s3/bucket/archivo/subir" \
  -H 'Content-Type: application/json' --data-binary "@$request_file"

printf '\n5. Listar objetos para verificar directorio y archivo\n'
printf '{"bucket":"%s"}' "$bucket" > "$request_file"
curl --fail-with-body -sS -i -X POST "$api_url/s3/bucket/lista-objetos" \
  -H 'Content-Type: application/json' --data-binary "@$request_file"
printf '\n'
