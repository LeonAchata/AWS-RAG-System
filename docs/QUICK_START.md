# Quick Start Guide - Sistema RAG

## 🚀 Deployment en 5 Minutos

### Paso 1: Prerequisitos

```powershell
# Verificar instalaciones
node --version          # Debe ser v18+
aws --version          # AWS CLI configurado
cdk --version          # CDK instalado
python --version       # Python 3.11+
```

Si falta algo:
```powershell
# Instalar CDK
npm install -g aws-cdk

# Instalar AWS CLI
pip install awscli

# Configurar AWS
aws configure
```

### Paso 2: Clonar y Configurar

```powershell
# Clonar repo (si no lo has hecho)
git clone https://github.com/LeonAchata/AWS-RAG-System.git
cd AWS-RAG-System

# Instalar dependencias
cd infrastructure
pip install -r requirements.txt
```

### Paso 3: Bootstrap CDK (Solo Primera Vez)

```powershell
# Preparar tu cuenta AWS para CDK
cdk bootstrap
```

Esto crea recursos necesarios en tu cuenta (solo se hace una vez).

### Paso 4: Deploy

```powershell
# Opción 1: Script automatizado
cd ..\scripts
.\deploy.ps1 deploy

# Opción 2: Manual
cd ..\infrastructure
cdk deploy
```

**Tiempo estimado:** 15-20 minutos (OpenSearch tarda en crear)

### Paso 5: Obtener URLs

Después del deployment, verás:

```
✅ RagSystemStack

Outputs:
RagSystemStack.ApiUrl = https://xyz123.execute-api.us-east-1.amazonaws.com/prod/
RagSystemStack.QueryEndpoint = https://xyz123.execute-api.us-east-1.amazonaws.com/prod/query
RagSystemStack.RawBucketName = ragsystemstack-rawdocumentsbucket-xyz123
RagSystemStack.OpenSearchEndpoint = search-rag-xyz123.us-east-1.es.amazonaws.com
```

**¡Guarda estos valores!**

## 🧪 Probar el Sistema

### Test 1: Health Check

```powershell
$API_URL = "https://xyz123.execute-api.us-east-1.amazonaws.com/prod"
curl "$API_URL/health"
```

Respuesta esperada:
```json
{"status": "ok", "service": "RAG System"}
```

### Test 2: Subir un Documento

```powershell
# Crear documento de prueba
@"
Machine Learning es una rama de la inteligencia artificial que permite
a las computadoras aprender de datos sin ser explícitamente programadas.
Se utiliza en reconocimiento de voz, visión por computadora y más.
"@ | Out-File -FilePath test-ml.txt -Encoding utf8

# Subir a S3
$BUCKET_NAME = "ragsystemstack-rawdocumentsbucket-xyz123"
aws s3 cp test-ml.txt "s3://$BUCKET_NAME/documents/test-ml.txt"
```

**Espera 10-30 segundos** para que se procese.

### Test 3: Verificar Indexación

```powershell
# Ver logs del Lambda de ingesta
aws logs tail /aws/lambda/RagSystemStack-IngestionLambda --follow
```

Deberías ver:
```
Procesando archivo: s3://...
Texto extraído: 200 caracteres
Generado 1 chunks
Embeddings generados para 1 chunks
Indexación completada: 1 exitosos
```

### Test 4: Hacer una Consulta

```powershell
$QUERY_URL = "$API_URL/query"

$body = @{
    query = "¿Qué es machine learning?"
    top_k = 3
    include_sources = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri $QUERY_URL -Method Post -Body $body -ContentType "application/json"
```

Respuesta esperada:
```json
{
  "query": "¿Qué es machine learning?",
  "answer": "Machine Learning es una rama de la inteligencia artificial que permite a las computadoras aprender de datos sin ser explícitamente programadas...",
  "sources": [
    {
      "document_id": "uuid-123",
      "filename": "test-ml.txt",
      "score": 0.95
    }
  ],
  "confidence": {
    "confidence": "high",
    "avg_similarity": 0.95
  },
  "response_time": 2.3
}
```

## 🎯 Uso Diario

### Subir Documentos

```powershell
# PDFs, DOCX, TXT, MD, HTML soportados
aws s3 cp mi-documento.pdf "s3://$BUCKET_NAME/documents/"
aws s3 cp mi-reporte.docx "s3://$BUCKET_NAME/documents/"
```

### Hacer Consultas

```powershell
# Crear función helper
function Query-RAG {
    param([string]$Question)
    
    $body = @{
        query = $Question
        top_k = 5
    } | ConvertTo-Json
    
    Invoke-RestMethod -Uri $QUERY_URL -Method Post -Body $body -ContentType "application/json"
}

# Usar
Query-RAG "¿Cuáles son las ventajas del deep learning?"
```

### Ver Logs

```powershell
# Lambda de Ingesta
aws logs tail /aws/lambda/RagSystemStack-IngestionLambda --follow

# Lambda de Query
aws logs tail /aws/lambda/RagSystemStack-QueryLambda --follow
```

### Ver OpenSearch Dashboard

Abre en tu navegador:
```
https://search-rag-xyz123.us-east-1.es.amazonaws.com/_dashboards
```

## 🛠️ Actualizar el Sistema

Cuando hagas cambios al código:

```powershell
# Ver cambios
cd infrastructure
cdk diff

# Aplicar
cdk deploy
```

CDK solo actualiza lo que cambió (incremental).

## 🗑️ Eliminar Todo

```powershell
# Eliminar stack completo
cd infrastructure
cdk destroy

# O con script
cd ..\scripts
.\deploy.ps1 destroy -Force
```

## 📊 Monitoreo

### CloudWatch Dashboard

1. Ve a AWS Console → CloudWatch
2. Dashboards → Busca "RagSystemStack"
3. Verás métricas de:
   - Invocaciones Lambda
   - Errores
   - Latencia
   - Throttling API

### Costos

```powershell
# Ver costos estimados
aws ce get-cost-and-usage `
    --time-period Start=2024-01-01,End=2024-01-31 `
    --granularity MONTHLY `
    --metrics "UnblendedCost" `
    --filter file://filter.json
```

## 🆘 Troubleshooting Rápido

### "No se encuentran documentos"

```powershell
# Verificar que el documento se indexó
aws opensearch list-documents --domain-name rag-opensearch
```

### "Lambda timeout"

Aumenta el timeout en `infrastructure/config/stack_config.py`:
```python
"ingestion_lambda_timeout": 10  # minutos
```

Luego: `cdk deploy`

### "Error de permisos"

Verifica tu usuario AWS tenga estos permisos:
- AmazonS3FullAccess
- AmazonOpenSearchServiceFullAccess
- AWSLambda_FullAccess
- AmazonAPIGatewayAdministrator
- CloudWatchLogsFullAccess

### "Bedrock no disponible"

Habilita modelos en AWS Console:
1. Ve a Amazon Bedrock
2. "Model access"
3. Request access para:
   - Titan Embeddings V2
   - Claude 3 Sonnet

## 📚 Recursos

- [README Principal](../README.md)
- [Documentación CDK](infrastructure/README.md)
- [Lambda Ingestion](lambda/ingestion/README.md)
- [Lambda Query](lambda/query/README.md)

## 🎉 ¡Listo!

Tu sistema RAG está funcionando. Ahora puedes:

1. ✅ Subir documentos a S3
2. ✅ Hacer consultas vía API
3. ✅ Ver resultados con fuentes
4. ✅ Monitorear en CloudWatch
5. ✅ Escalar según necesidad

**¿Próximo paso?** Crea un frontend o integra con tu aplicación.
