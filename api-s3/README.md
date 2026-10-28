# Semana 11: API REST para S3

Proyecto del ejercicio propuesto del Taller 3. Usa Serverless Framework **3.40.0**, Python 3.12, API Gateway REST y cinco funciones Lambda. El servicio se despliega por separado en `dev`, `test` y `prod`.

## Requisitos

- Una sesión activa de AWS Academy en la cuenta `904208419583`, con la función `LabRole` disponible.
- Node.js y npm para instalar Serverless v3.
- Python 3.12 en AWS Lambda. En CloudShell, Python 3 sirve para generar la solicitud de prueba.
- Para ejecutar las pruebas locales: `python -m pip install boto3 pytest`.

No guardar claves AWS en este repositorio. Confirmar la sesión antes del despliegue:

```bash
aws sts get-caller-identity
```

El `Account` debe ser `904208419583`. Si el laboratorio entrega credenciales temporales, configurarlas en CloudShell según las instrucciones de AWS Academy y volver a verificar la identidad. La organización Serverless configurada es `diegoladrondeguevara`.

## Despliegue en CloudShell

```bash
git clone https://github.com/DiegoLadrondeGuevara/sem11.git
cd sem11/api-s3
npm ci
npx serverless --version
npx serverless deploy --stage dev
npx serverless deploy --stage test
npx serverless deploy --stage prod
npx serverless info --stage dev
npx serverless info --stage test
npx serverless info --stage prod
```

Si Serverless solicita iniciar sesión en la organización, usar la cuenta asociada a `diegoladrondeguevara`. La URL de API Gateway cambia en cada stage; copiar cada URL completa (incluido `/dev`, `/test` o `/prod`) desde `serverless info`.

## Rutas

| Método | Ruta | Cuerpo JSON | Resultado |
| --- | --- | --- | --- |
| GET | `/s3/lista-buckets` | Ninguno | Lista de buckets |
| POST | `/s3/bucket/lista-objetos` | `{"bucket":"..."}` | Lista de claves, incluso vacía |
| POST | `/s3/bucket/crear` | `{"bucket":"..."}` | Bucket nuevo |
| POST | `/s3/bucket/directorio/crear` | `{"bucket":"...","directorio":"imagenes-chicas"}` | Directorio nuevo |
| POST | `/s3/bucket/archivo/subir` | Ver ejemplo abajo | Archivo nuevo |

El archivo se transmite en base64 dentro de JSON. S3 representa el directorio con un objeto vacío cuya clave termina en `/`. Crear ese directorio antes de subir el archivo. El límite implementado para el archivo decodificado es 4 MiB. Usar nombres de bucket únicos en todo AWS, por ejemplo `sem11-904208419583-dev-<sufijo>` y un nombre diferente para cada stage.

```json
{
  "bucket": "sem11-904208419583-dev-ejemplo",
  "directorio": "imagenes-chicas",
  "nombre_archivo": "galleta01-small.png",
  "tipo_contenido": "image/png",
  "contenido_base64": "BASE64_DEL_ARCHIVO"
}
```

## Pruebas desde Linux

El script usa `curl` para las cinco rutas y sube la imagen incluida en `ejemplos/`. Sustituir URL y bucket por valores reales. Usar un bucket diferente para cada stage, porque la creación de buckets es global.

```bash
bash scripts/probar_api.sh 'https://ID.execute-api.us-east-1.amazonaws.com/dev' 'sem11-904208419583-dev-<sufijo>' | tee evidencias/dev-curl.log
bash scripts/probar_api.sh 'https://ID.execute-api.us-east-1.amazonaws.com/test' 'sem11-904208419583-test-<sufijo>' | tee evidencias/test-curl.log
bash scripts/probar_api.sh 'https://ID.execute-api.us-east-1.amazonaws.com/prod' 'sem11-904208419583-prod-<sufijo>' | tee evidencias/prod-curl.log
```

Importar `api-s3.postman_collection.json` en Postman. Cambiar `baseUrl` y `bucket` al stage que se esté probando. La cuarta solicitud contiene un archivo de texto pequeño; para subir una imagen en Postman, reemplazar los campos del cuerpo con el archivo codificado en base64. El script de Linux ya sube una imagen real.

También se incluyen tres entornos de Postman en `postman/`, con las URLs reales desplegadas para `dev`, `test` y `prod`. Importar el entorno correspondiente antes de ejecutar la colección. Cada entorno usa un bucket propio con sufijo `pm-9af36eb`, diferente de los buckets usados por `curl`, para que la operación de creación responda `201` en la primera ejecución.

## Evidencias

Guardar las capturas reales de las ejecuciones de CloudShell, Postman y la consola S3 para los tres stages. `evidencias/README.md` contiene la lista. Después reunirlas en un único Word o PDF. Las capturas y el documento final se elaborarán durante la sesión de CloudShell; este repositorio no inventa resultados de AWS.

## Comprobación local

```bash
python -m pytest -q
npx serverless print --stage dev
```

Serverless 3.40.0 puede mostrar una advertencia de validación para `python3.12`: su lista interna de runtimes quedó desactualizada. El empaquetado local termina correctamente y la plantilla de CloudFormation conserva `python3.12`. La ejecución real se verificará al desplegar en AWS Academy.
