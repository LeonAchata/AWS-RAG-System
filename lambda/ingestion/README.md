# Lambda de Ingesta de Documentos

## Descripción

Esta función Lambda procesa documentos subidos al sistema, los divide en chunks, genera embeddings y los indexa en OpenSearch para búsqueda vectorial.

## Flujo de Procesamiento

1. **Recepción del Documento**: Desde S3 (evento automático) o API Gateway (upload directo)
2. **Extracción de Texto**: Soporta PDF, DOCX, TXT, HTML, MD
3. **Chunking**: Divide el texto en fragmentos de ~800 caracteres con overlap de 100
4. **Embeddings**: Genera vectores usando Amazon Bedrock Titan Embeddings V2
5. **Indexación**: Almacena chunks y vectores en OpenSearch

## Archivos

- `handler.py` - Handler principal del Lambda
- `requirements.txt` - Dependencias de Python
- `utils/document_processor.py` - Procesamiento de diferentes formatos
- `utils/text_chunker.py` - División de texto en chunks

## Variables de Entorno

| Variable | Descripción | Requerido | Default |
|----------|-------------|-----------|---------|
| `OPENSEARCH_ENDPOINT` | Endpoint de OpenSearch | Sí | - |
| `OPENSEARCH_INDEX` | Nombre del índice | No | `rag-documents` |
| `AWS_REGION` | Región de AWS | No | `us-east-1` |
| `BEDROCK_EMBEDDING_MODEL` | Modelo de embeddings | No | `amazon.titan-embed-text-v2:0` |
| `CHUNK_SIZE` | Tamaño de cada chunk | No | `800` |
| `CHUNK_OVERLAP` | Overlap entre chunks | No | `100` |

## Eventos Soportados

### Evento S3 (Automático)

```json
{
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "mi-bucket"
        },
        "object": {
          "key": "documentos/archivo.pdf"
        }
      }
    }
  ]
}
```

### Evento API Gateway (Manual)

```json
{
  "body": {
    "content": "Contenido del documento...",
    "filename": "documento.txt",
    "is_base64": false
  }
}
```

## Respuesta

```json
{
  "statusCode": 200,
  "body": {
    "message": "Documento procesado exitosamente",
    "document_id": "uuid-del-documento",
    "chunks_count": 15
  }
}
```

## Formatos Soportados

- **PDF** (`.pdf`) - Usa PyPDF2 o pdfplumber
- **Word** (`.docx`) - Usa python-docx
- **Texto** (`.txt`, `.md`) - Lectura directa
- **HTML** (`.html`, `.htm`) - Usa BeautifulSoup

## Permisos IAM Requeridos

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::tu-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "es:ESHttpPut",
        "es:ESHttpPost",
        "es:ESHttpGet"
      ],
      "Resource": "arn:aws:es:*:*:domain/*"
    }
  ]
}
```

## Desarrollo Local

### Instalar dependencias

```bash
cd lambda/ingestion
pip install -r requirements.txt
```

### Testing manual

```python
import json
from handler import lambda_handler

event = {
    "body": json.dumps({
        "content": "Este es un documento de prueba",
        "filename": "test.txt"
    })
}

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
```

## Deployment

El deployment se maneja a través de AWS CDK desde el directorio `infrastructure/`.

## Logs

Los logs se envían automáticamente a CloudWatch Logs:
- Grupo: `/aws/lambda/rag-ingestion-lambda`
- Nivel: INFO
- Incluye: Errores, tiempo de procesamiento, número de chunks

## Troubleshooting

### Error: "Import could not be resolved"

Los errores de import son normales en desarrollo local. Las dependencias estarán disponibles en el entorno Lambda cuando se despliegue.

### Error: "OPENSEARCH_ENDPOINT not found"

Asegúrate de configurar la variable de entorno en la configuración del Lambda.

### Timeout

Si procesas documentos muy grandes, aumenta el timeout del Lambda (recomendado: 5 minutos) y la memoria (recomendado: 2048 MB).

## Próximos Pasos

✅ Lambda de ingesta implementado
⏭️ Siguiente: Lambda de Query para búsqueda y generación de respuestas
