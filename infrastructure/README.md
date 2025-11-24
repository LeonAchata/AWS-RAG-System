# AWS CDK - Guía de Deployment

## 🚀 Quick Start

### Prerequisitos

1. **Node.js** (v18 o superior)
   ```bash
   node --version
   ```

2. **AWS CLI** configurado con credenciales
   ```bash
   aws --version
   aws configure
   ```

3. **AWS CDK** instalado globalmente
   ```bash
   npm install -g aws-cdk
   cdk --version
   ```

4. **Python 3.11** o superior
   ```bash
   python --version
   ```

### Instalación Rápida

#### Opción 1: Script Automático (PowerShell)

```powershell
# En Windows
cd scripts
.\deploy.ps1 all
```

#### Opción 2: Script Python

```bash
# Linux/Mac
cd scripts
python deploy.py all
```

#### Opción 3: Manual

```bash
# 1. Instalar dependencias
cd infrastructure
pip install -r requirements.txt

# 2. Bootstrap CDK (solo primera vez)
cdk bootstrap

# 3. Ver cambios
cdk diff

# 4. Desplegar
cdk deploy
```

## 📋 Comandos CDK

### Comandos Básicos

```bash
# Ver la plantilla CloudFormation generada
cdk synth

# Ver cambios antes de aplicar
cdk diff

# Desplegar stack
cdk deploy

# Eliminar stack
cdk destroy

# Listar stacks
cdk ls

# Ver metadatos del stack
cdk metadata
```

### Con Perfil AWS Específico

```bash
cdk deploy --profile production
cdk diff --profile staging
```

### Auto-aprobar Cambios

```bash
# Sin pedir confirmación
cdk deploy --require-approval never
```

## 🏗️ Estructura del Stack

### Recursos Creados

El stack `RagStack` crea automáticamente:

#### 1. **S3 Buckets** (2)
- `RawDocumentsBucket` - Documentos sin procesar
  - Versionado habilitado
  - Cifrado S3-managed
  - Lifecycle: eliminar versiones antiguas después de 30 días
  
- `ProcessedDocumentsBucket` - Backup de procesados
  - Cifrado S3-managed
  - Block public access

#### 2. **OpenSearch Domain** (1)
- Versión: OpenSearch 2.11
- Instancia: t3.small.search (dev) → ajustable
- Nodos: 1 (dev) → 3 (prod)
- EBS: 10GB (dev) → 100GB (prod)
- k-NN habilitado para búsqueda vectorial
- Cifrado at-rest y node-to-node
- HTTPS obligatorio
- Fine-grained access control

#### 3. **Lambda Functions** (2)

**Ingestion Lambda:**
- Runtime: Python 3.11
- Memoria: 2048 MB
- Timeout: 5 minutos
- Trigger: S3 (objeto creado)
- Permisos: S3 read, OpenSearch write, Bedrock invoke

**Query Lambda:**
- Runtime: Python 3.11
- Memoria: 1024 MB
- Timeout: 60 segundos
- Trigger: API Gateway
- Permisos: OpenSearch read, Bedrock invoke

#### 4. **Lambda Layer** (1)
- Código compartido (`shared/`)
- Clientes de Bedrock y OpenSearch
- Compatible con Python 3.11

#### 5. **API Gateway** (1)
- Type: REST API
- Stage: prod
- CORS habilitado
- Throttling: 100 req/sec (dev) → 2000 req/sec (prod)

**Endpoints:**
- `POST /query` - Realizar consultas
- `POST /ingest` - Ingestar documentos directamente
- `GET /health` - Health check

#### 6. **IAM Roles y Policies** (automático)
- Roles para cada Lambda
- Permisos de mínimo privilegio
- Políticas de acceso a Bedrock, S3, OpenSearch

#### 7. **CloudWatch Logs** (automático)
- Log groups para cada Lambda
- Retención: 7 días (dev) → 90 días (prod)

## 📊 Outputs del Stack

Después del deployment, obtendrás:

```
Outputs:
RagSystemStack.ApiUrl = https://abc123.execute-api.us-east-1.amazonaws.com/prod/
RagSystemStack.QueryEndpoint = https://abc123.execute-api.us-east-1.amazonaws.com/prod/query
RagSystemStack.IngestEndpoint = https://abc123.execute-api.us-east-1.amazonaws.com/prod/ingest
RagSystemStack.RawBucketName = ragsystemstack-rawdocumentsbucket-abc123
RagSystemStack.OpenSearchEndpoint = search-rag-abc123.us-east-1.es.amazonaws.com
RagSystemStack.OpenSearchDashboard = https://search-rag-abc123.us-east-1.es.amazonaws.com/_dashboards
```

Guarda estos valores - los necesitarás para usar el sistema.

## 🔧 Configuración por Ambiente

El stack soporta múltiples ambientes con configuraciones diferentes:

```python
# infrastructure/config/stack_config.py

# Desarrollo (default)
environment = "dev"

# Staging
environment = "staging"

# Producción
environment = "prod"
```

### Diferencias por Ambiente

| Recurso | Dev | Staging | Prod |
|---------|-----|---------|------|
| OpenSearch Instance | t3.small | t3.medium | r6g.large |
| OpenSearch Nodes | 1 | 2 | 3 |
| EBS Volume | 10 GB | 50 GB | 100 GB |
| Lambda Memory (Ing) | 2048 MB | 3008 MB | 3008 MB |
| Lambda Memory (Qry) | 1024 MB | 1536 MB | 2048 MB |
| API Throttle | 100/sec | 500/sec | 2000/sec |
| Log Retention | 7 days | 30 days | 90 days |
| Removal Policy | DESTROY | RETAIN | RETAIN |

## 🧪 Testing del Deployment

### 1. Health Check

```bash
curl https://YOUR_API_URL/health
```

Expected:
```json
{"status": "ok", "service": "RAG System"}
```

### 2. Subir Documento (S3)

```bash
aws s3 cp documento.pdf s3://YOUR_RAW_BUCKET/documents/documento.pdf
```

Esto activará automáticamente el Lambda de ingesta.

### 3. Realizar Query

```bash
curl -X POST https://YOUR_API_URL/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Qué es machine learning?",
    "top_k": 5
  }'
```

## 🔍 Monitoreo

### CloudWatch Logs

```bash
# Ver logs de Lambda de Ingesta
aws logs tail /aws/lambda/RagSystemStack-IngestionLambda --follow

# Ver logs de Lambda de Query
aws logs tail /aws/lambda/RagSystemStack-QueryLambda --follow
```

### CloudWatch Metrics

Los dashboards automáticos incluyen:
- Invocaciones de Lambda
- Errores y timeouts
- Latencia (P50, P95, P99)
- Throttling de API Gateway
- Estado de OpenSearch cluster

## 💰 Estimación de Costos

### Costos Aproximados (us-east-1)

**Ambiente Dev:**
- OpenSearch (t3.small, 1 nodo): ~$25/mes
- Lambda (1M invocaciones): ~$5/mes
- S3 (10 GB): ~$0.23/mes
- API Gateway (1M requests): ~$3.50/mes
- **Bedrock (variable):**
  - Embeddings: $0.0001/1K tokens input
  - Claude 3 Sonnet: $0.003/1K tokens input, $0.015/1K output

**Total base: ~$34/mes + costos de Bedrock**

**Ambiente Prod:**
- OpenSearch (r6g.large, 3 nodos): ~$420/mes
- Lambda (10M invocaciones): ~$50/mes
- S3 (100 GB): ~$2.30/mes
- API Gateway (10M requests): ~$35/mes
- Bedrock: Según uso

**Total base: ~$507/mes + costos de Bedrock**

### Optimizaciones de Costo

1. **Usar Reserved Instances** para OpenSearch (ahorro 30-70%)
2. **Habilitar caché** en Lambda Query (reduce llamadas a Bedrock)
3. **Lifecycle policies** en S3 para datos antiguos
4. **Right-sizing** de instancias según carga real
5. **CloudWatch alarms** para detectar uso excesivo

## 🗑️ Limpieza

### Eliminar Todo

```bash
cdk destroy
```

Esto elimina:
- ✅ Lambdas
- ✅ API Gateway
- ✅ Lambda Layers
- ✅ IAM Roles
- ✅ CloudWatch Logs
- ✅ OpenSearch Domain
- ✅ S3 Buckets (si `auto_delete_objects=True`)

**Nota:** En prod, los buckets y OpenSearch tienen `RETAIN` policy para evitar pérdida de datos.

### Eliminar Solo en Dev

```powershell
# PowerShell
.\deploy.ps1 destroy -Force

# O manual
cdk destroy --force
```

## 🐛 Troubleshooting

### Error: "Account not bootstrapped"

```bash
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

### Error: "Insufficient permissions"

Verificar que tu usuario AWS tenga:
- IAM permissions
- CloudFormation permissions
- Lambda, S3, OpenSearch permissions

### Error: OpenSearch domain creation failed

- Verificar límites de servicio en tu cuenta
- Verificar que la región soporta el tipo de instancia
- Puede tomar 20-30 minutos en crear

### Lambda timeout

- Aumentar timeout en `stack_config.py`
- Verificar que OpenSearch esté activo
- Verificar logs en CloudWatch

## 📚 Recursos Adicionales

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS CDK Python Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [OpenSearch Documentation](https://opensearch.org/docs/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)

## 🎯 Próximos Pasos

Después del deployment exitoso:

1. ✅ Verificar outputs del stack
2. ✅ Probar health check
3. ✅ Subir documento de prueba a S3
4. ✅ Verificar indexación en OpenSearch Dashboard
5. ✅ Realizar query de prueba vía API
6. ✅ Configurar frontend para uso interactivo
