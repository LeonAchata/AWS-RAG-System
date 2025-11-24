# Sistema RAG (Retrieval-Augmented Generation) con AWS

[![AWS](https://img.shields.io/badge/AWS-Bedrock-orange)](https://aws.amazon.com/bedrock/)
[![CDK](https://img.shields.io/badge/AWS-CDK-blue)](https://aws.amazon.com/cdk/)
[![Python](https://img.shields.io/badge/Python-3.11-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🚀 Quick Start

```powershell
# 1. Clonar el repositorio
git clone https://github.com/LeonAchata/AWS-RAG-System.git
cd AWS-RAG-System

# 2. Instalar CDK globalmente (si no lo tienes)
npm install -g aws-cdk

# 3. Configurar AWS credentials
aws configure

# 4. Deploy con un comando
cd scripts
.\deploy.ps1 all
```

**[Ver guía completa de inicio rápido →](docs/QUICK_START.md)**

## 📖 Descripción General del Proyecto

Este proyecto implementa un **sistema completo de RAG (Retrieval-Augmented Generation)** utilizando servicios de AWS, específicamente **Amazon Bedrock** para embeddings y generación de respuestas con Claude 3. 

El sistema permite:
- ✅ Cargar documentos (PDF, DOCX, TXT, HTML, MD)
- ✅ Procesamiento automático con chunking inteligente
- ✅ Indexación en base de datos vectorial (OpenSearch)
- ✅ Consultas en lenguaje natural
- ✅ Respuestas contextualizadas con fuentes

**Todo deployado automáticamente con AWS CDK.**

## Arquitectura del Sistema

El sistema está dividido en dos flujos principales:

### 1. Flujo de Ingesta (Ingestion Pipeline)

Este flujo se encarga de procesar y almacenar documentos en el sistema:

**Componentes:**
- **Fuentes de Datos**: El sistema acepta documentos de múltiples fuentes (S3, bases de datos relacionales, archivos locales)
- **Lambda de Ingesta**: Función serverless que orquesta el proceso de carga
- **S3 Raw**: Bucket de almacenamiento para documentos originales
- **Procesamiento y Chunking**: Divide los documentos en fragmentos manejables
- **Bedrock Titan Embeddings**: Genera vectores de embedding para cada fragmento de texto
- **Almacenamiento de Índices**: Guarda los vectores en una base de datos vectorial
- **Vector Database**: Almacena y permite búsqueda eficiente de vectores (OpenSearch, DynamoDB con extensiones vectoriales, o Aurora)

### 2. Flujo de Consulta (Query Pipeline)

Este flujo gestiona las peticiones de los usuarios y genera respuestas:

**Componentes:**
- **User Application**: Interfaz de usuario (web, móvil, o CLI)
- **API Gateway**: Punto de entrada para las peticiones HTTP
- **Lambda de Query**: Procesa las consultas de los usuarios
- **Bedrock Titan Embeddings**: Convierte la consulta del usuario en un vector
- **Vector Database**: Recupera los documentos más relevantes mediante búsqueda de similitud
- **Bedrock LLM (Claude/OpenAI)**: Genera respuestas contextuales basadas en los documentos recuperados
- **Respuesta al Usuario**: Retorna la respuesta generada a través de API Gateway

## Stack Tecnológico Recomendado

### Servicios de AWS Core

1. **Amazon S3**
   - Almacenamiento de documentos originales
   - Bucket para datos raw
   - Bucket para logs y metadatos
   - Versionado habilitado para trazabilidad

2. **AWS Lambda**
   - Lambda de Ingesta: Procesa documentos entrantes
   - Lambda de Query: Maneja peticiones de búsqueda
   - Runtime: Python 3.11 o superior
   - Memoria recomendada: 1024-2048 MB según tamaño de documentos

3. **Amazon API Gateway**
   - REST API o HTTP API
   - Autenticación mediante IAM, Cognito, o API Keys
   - Throttling y rate limiting configurado

4. **Amazon Bedrock**
   - Modelo de Embeddings: Titan Embeddings V2
   - Modelo LLM: Claude 3 Sonnet o Claude 3.5 Sonnet
   - Configuración de temperatura y tokens máximos

### Base de Datos Vectorial (Opciones)

**Opción 1: Amazon OpenSearch Service**
- Motor de búsqueda especializado con soporte nativo para vectores
- Plugin k-NN para búsqueda de vecinos más cercanos
- Escalabilidad horizontal
- Visualización con OpenSearch Dashboards

**Opción 2: Amazon DynamoDB con extensiones**
- Solución serverless completamente gestionada
- Menor costo para volúmenes pequeños/medianos
- Requiere implementación personalizada de búsqueda vectorial

**Opción 3: Amazon Aurora PostgreSQL con pgvector**
- Extension pgvector para búsqueda vectorial
- Ventaja si ya se usa PostgreSQL
- Consultas SQL tradicionales combinadas con búsqueda vectorial

### Procesamiento de Documentos

**Librerías de Parsing:**
- **LangChain**: Framework completo para aplicaciones LLM
- **PyPDF2/pdfplumber**: Extracción de texto de PDFs
- **python-docx**: Procesamiento de documentos Word
- **Beautiful Soup**: Parsing de HTML
- **Unstructured**: Biblioteca universal para múltiples formatos

**Text Splitting:**
- RecursiveCharacterTextSplitter de LangChain
- Tamaño de chunk recomendado: 500-1000 tokens
- Overlap entre chunks: 50-100 tokens

### Infraestructura como Código

**Opciones:**
- **AWS CDK (Cloud Development Kit)**: Python o TypeScript
- **Terraform**: Para equipos multi-cloud
- **AWS SAM (Serverless Application Model)**: Específico para arquitecturas serverless
- **CloudFormation**: Nativo de AWS pero más verboso

### Frontend (Opcional)

**Para Aplicación Web:**
- **React** + **Vite**: SPA moderna y rápida
- **Next.js**: Si se requiere SSR
- **Tailwind CSS**: Estilización
- **Axios/Fetch**: Cliente HTTP

**Para CLI:**
- **Click** o **Typer**: Frameworks de CLI en Python
- **Rich**: Formato y visualización en terminal

## 📁 Estructura del Proyecto

```
AWS-RAG-System/
├── infrastructure/          # 🏗️ AWS CDK - Infraestructura como código
│   ├── stacks/
│   │   └── rag_stack.py    # Stack principal con todos los recursos
│   ├── constructs/         # Componentes reutilizables de CDK
│   ├── config/             # Configuraciones por ambiente (dev/staging/prod)
│   ├── app.py              # Punto de entrada CDK
│   └── cdk.json            # Configuración CDK
│
├── lambda/                  # 🔧 Funciones Lambda
│   ├── ingestion/          # Lambda de ingesta de documentos
│   │   ├── handler.py      # ✅ Implementado
│   │   ├── requirements.txt
│   │   └── utils/
│   │       ├── document_processor.py  # Soporte PDF, DOCX, TXT, HTML
│   │       └── text_chunker.py        # Chunking inteligente con LangChain
│   └── query/              # Lambda de consultas
│       ├── handler.py      # ✅ Implementado
│       ├── requirements.txt
│       └── utils/
│           ├── prompt_builder.py      # Construcción de prompts RAG
│           └── cache.py               # Sistema de caché
│
├── shared/                  # 📦 Código compartido
│   ├── models/
│   │   └── document.py     # Modelos de datos (Document, Chunk, Query)
│   ├── utils/
│   │   ├── bedrock_client.py      # Cliente para Bedrock (embeddings + LLM)
│   │   └── opensearch_client.py   # Cliente para OpenSearch (indexación + búsqueda)
│   └── config/
│       └── settings.py     # Configuración centralizada
│
├── scripts/                 # 🚀 Scripts de deployment y testing
│   ├── deploy.py           # Script Python de deployment
│   ├── deploy.ps1          # Script PowerShell de deployment
│   └── test_system.py      # Tests automáticos del sistema
│
├── docs/                    # 📚 Documentación
│   ├── QUICK_START.md      # Guía de inicio rápido
│   └── SETUP.md            # Setup detallado
│
├── tests/                   # 🧪 Tests (por implementar)
│   ├── unit/
│   └── integration/
│
└── README.md               # Este archivo
```

**Estado actual:** ✅ Lambdas implementadas | ✅ CDK configurado | ⏭️ Listo para deploy

## 🎯 Características Implementadas

### Lambda de Ingesta ✅
- **Procesamiento Multi-formato:** PDF, DOCX, TXT, HTML, Markdown
- **Chunking Inteligente:** División automática con LangChain (800 chars, 100 overlap)
- **Embeddings con Bedrock:** Titan Embeddings V2 (1024 dimensiones)
- **Indexación Automática:** OpenSearch con k-NN vectorial
- **Triggers S3:** Procesamiento automático al subir documentos
- **Extracción de Metadatos:** Título, autor, fecha, etc.

### Lambda de Query ✅
- **Búsqueda Vectorial:** k-NN con similitud coseno en OpenSearch
- **Generación con Claude 3:** Respuestas contextualizadas con LLM
- **Sistema de Caché:** Reduce costos y latencia (30 min TTL)
- **Modo Conversacional:** Soporte para historial de chat
- **Métricas de Confianza:** High/Medium/Low basado en similitud
- **Trazabilidad:** Referencias a documentos fuente con scores
- **Filtros Opcionales:** Por metadatos (tipo, autor, fecha)

### Infraestructura CDK ✅
- **S3 Buckets:** Raw + Processed con versionado y lifecycle
- **OpenSearch Domain:** k-NN habilitado, cifrado, fine-grained access
- **Lambda Functions:** Con permisos IAM automáticos
- **API Gateway:** REST API con CORS y throttling
- **Lambda Layers:** Código compartido reutilizable
- **CloudWatch:** Logs y métricas automáticos
- **Multi-ambiente:** Configs para dev/staging/prod

### Clientes Compartidos ✅
- **BedrockClient:** Embeddings + LLM con singleton pattern
- **OpenSearchClient:** Indexación + búsqueda vectorial optimizada
- **Modelos de Datos:** Document, Chunk, QueryResult con tipos
- **Configuración:** Settings centralizados y parametrizables

### Proceso de Ingesta

1. **Carga de Documento**: Usuario sube documento a través de aplicación o directamente a S3
2. **Trigger**: Evento S3 activa Lambda de Ingesta
3. **Extracción**: Lambda extrae texto según el tipo de documento
4. **Chunking**: Divide el documento en fragmentos con overlap
5. **Metadatos**: Extrae y almacena metadatos (título, autor, fecha, etc.)
6. **Embedding**: Cada chunk se envía a Bedrock Titan Embeddings para generar vectores
7. **Indexación**: Vectores y metadatos se almacenan en la base de datos vectorial
8. **Confirmación**: Sistema registra el documento como procesado

### Proceso de Query

1. **Solicitud del Usuario**: Usuario envía pregunta a través de la aplicación
2. **API Gateway**: Recibe y valida la petición
3. **Lambda Query**: Procesa la consulta
4. **Embedding de Query**: Convierte la pregunta en vector usando Bedrock
5. **Búsqueda Vectorial**: Encuentra los top-K documentos más similares en la base de datos
6. **Construcción de Contexto**: Recupera el texto de los chunks relevantes
7. **Prompt Engineering**: Construye prompt con contexto y pregunta para el LLM
8. **Generación**: Bedrock Claude genera respuesta basada en el contexto
9. **Respuesta**: Sistema retorna respuesta al usuario con referencias opcionales

## Consideraciones Técnicas Importantes

### Seguridad

- **IAM Roles**: Principio de mínimo privilegio para cada componente
- **Encryption**: Datos en reposo (S3, bases de datos) y en tránsito (TLS)
- **VPC**: Opcionalmente colocar bases de datos en VPC privada
- **API Security**: Autenticación y autorización en API Gateway
- **Secrets Manager**: Almacenar credenciales y API keys

### Escalabilidad

- **Lambda Concurrency**: Configurar límites de concurrencia reservada
- **DynamoDB**: Configurar auto-scaling o modo on-demand
- **OpenSearch**: Dimensionar cluster según volumen de datos
- **S3**: Ilimitado, pero considerar políticas de lifecycle
- **API Gateway**: Rate limiting por usuario/API key

### Costos

**Factores principales de costo:**
- Invocaciones de Bedrock (embeddings y LLM)
- Almacenamiento en vector database
- Transferencia de datos
- Lambda invocations y compute time
- API Gateway requests

**Optimizaciones:**
- Cachear embeddings de queries frecuentes
- Usar Reserved Capacity si el uso es predecible
- Implementar lifecycle policies en S3
- Monitorear y ajustar tamaño de chunks

### Monitoreo y Observabilidad

**Métricas clave:**
- Latencia de ingesta y query
- Tasa de error en Lambdas
- Costos por operación en Bedrock
- Tamaño de índice vectorial
- Relevancia de resultados (métricas de retrieval)

**Herramientas:**
- **CloudWatch**: Logs y métricas nativas
- **X-Ray**: Trazado distribuido
- **CloudWatch Dashboards**: Visualización de métricas
- **Alarmas**: Notificaciones ante anomalías

### Calidad del RAG

**Métricas de evaluación:**
- **Precision@K**: Relevancia de los top-K resultados
- **Recall**: Cobertura de documentos relevantes
- **Latencia**: Tiempo de respuesta end-to-end
- **Cosine Similarity**: Similitud entre query y documentos recuperados

**Mejoras:**
- Fine-tuning de tamaño de chunk y overlap
- Experimentar con diferentes modelos de embedding
- Implementar re-ranking de resultados
- Usar metadatos para filtrado pre-búsqueda
- Implementar feedback loop de usuarios

## Variables de Configuración Críticas

### Para el Sistema de Embeddings
- Dimensión de vectores (según modelo elegido)
- Modelo de embedding (Titan Embeddings V2: 1024 dimensiones)
- Normalización de vectores

### Para Text Chunking
- Tamaño de chunk (500-1000 tokens recomendado)
- Overlap entre chunks (10-20% del tamaño)
- Estrategia de splitting (por párrafo, sentencia, carácter)

### Para Retrieval
- Número de documentos a recuperar (K = 3-5 típicamente)
- Método de similitud (cosine, euclidean, dot product)
- Threshold de similitud mínima

### Para el LLM
- Modelo (Claude 3 Sonnet, Claude 3.5 Sonnet)
- Temperature (0.1-0.3 para respuestas más determinísticas)
- Max tokens de respuesta (512-2048)
- System prompt para guiar comportamiento

## 🚀 Deployment

### Prerequisitos

```powershell
# Verificar instalaciones
node --version    # v18+
aws --version     # AWS CLI
cdk --version     # AWS CDK
python --version  # 3.11+
```

### Deploy Automático

```powershell
# Opción 1: PowerShell (Windows)
cd scripts
.\deploy.ps1 all

# Opción 2: Python (multiplataforma)
cd scripts
python deploy.py all
```

### Deploy Manual

```powershell
cd infrastructure

# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Bootstrap (solo primera vez)
cdk bootstrap

# 3. Ver cambios
cdk diff

# 4. Desplegar
cdk deploy
```

**Tiempo:** ~15-20 minutos (OpenSearch tarda en crear)

### Outputs del Stack

Después del deployment:

```
✅ RagSystemStack

Outputs:
RagSystemStack.ApiUrl = https://xyz.execute-api.us-east-1.amazonaws.com/prod/
RagSystemStack.QueryEndpoint = .../query
RagSystemStack.IngestEndpoint = .../ingest
RagSystemStack.RawBucketName = ragsystemstack-rawdocumentsbucket-xyz
RagSystemStack.OpenSearchEndpoint = search-rag-xyz.us-east-1.es.amazonaws.com
```

**[Ver documentación completa de deployment →](infrastructure/README.md)**

## 🧪 Testing

### Test Automático

```powershell
cd scripts
python test_system.py --api-url YOUR_API_URL --bucket YOUR_BUCKET_NAME
```

### Test Manual

```powershell
# 1. Health check
curl https://YOUR_API_URL/health

# 2. Subir documento
aws s3 cp documento.pdf s3://YOUR_BUCKET/documents/

# 3. Hacer query
curl -X POST https://YOUR_API_URL/query \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué es machine learning?", "top_k": 5}'
```

## 💡 Uso

### Subir Documentos

```powershell
# Via S3 (activa procesamiento automático)
aws s3 cp mi-documento.pdf s3://YOUR_BUCKET/documents/

# Via API (procesamiento directo)
curl -X POST https://YOUR_API_URL/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "...", "filename": "doc.txt"}'
```

### Realizar Consultas

```powershell
# Query simple
curl -X POST https://YOUR_API_URL/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Cuáles son las ventajas del deep learning?",
    "top_k": 5,
    "include_sources": true
  }'

# Query con filtros
curl -X POST https://YOUR_API_URL/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Qué dice sobre seguridad?",
    "filters": {"document_type": "pdf"},
    "min_similarity": 0.75
  }'

# Query conversacional
curl -X POST https://YOUR_API_URL/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Y cuál es la diferencia con IA tradicional?",
    "conversational": true,
    "conversation_history": [...]
  }'
```

### Response Format

```json
{
  "query": "¿Qué es machine learning?",
  "answer": "Machine Learning es...",
  "sources": [
    {
      "document_id": "uuid",
      "filename": "ml-guide.pdf",
      "chunks_used": [{"chunk_index": 0, "score": 0.92}]
    }
  ],
  "confidence": {
    "confidence": "high",
    "avg_similarity": 0.87,
    "max_similarity": 0.92
  },
  "response_time": 2.3,
  "from_cache": false
}
```

## 📊 Monitoreo

### CloudWatch

```powershell
# Ver logs de Ingesta
aws logs tail /aws/lambda/RagSystemStack-IngestionLambda --follow

# Ver logs de Query
aws logs tail /aws/lambda/RagSystemStack-QueryLambda --follow
```

### OpenSearch Dashboard

```
https://YOUR_OPENSEARCH_ENDPOINT/_dashboards
```

### Métricas Clave

- Invocaciones Lambda
- Errores y timeouts
- Latencia (P50, P95, P99)
- Cache hit rate
- Costos de Bedrock

## 💰 Costos Estimados

### Ambiente Dev

- OpenSearch (t3.small, 1 nodo): ~$25/mes
- Lambda (1M invocaciones): ~$5/mes
- S3 (10 GB): ~$0.23/mes
- API Gateway (1M requests): ~$3.50/mes
- **Bedrock (variable):**
  - Embeddings: $0.0001/1K tokens
  - Claude 3 Sonnet: $0.003/1K input, $0.015/1K output

**Total base: ~$34/mes + Bedrock según uso**

### Optimizaciones

- ✅ Caché habilitado (reduce 40-60% llamadas a Bedrock)
- ✅ Batch processing de embeddings
- ✅ Lifecycle policies en S3
- ✅ Reserved capacity para OpenSearch (30-70% ahorro)

## 🛠️ Configuración

### Variables de Entorno (Lambda)

```bash
# Bedrock
BEDROCK_EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
BEDROCK_LLM_MODEL=anthropic.claude-3-sonnet-20240229-v1:0

# OpenSearch
OPENSEARCH_ENDPOINT=search-rag-xyz.us-east-1.es.amazonaws.com
OPENSEARCH_INDEX=rag-documents

# RAG Parameters
CHUNK_SIZE=800
CHUNK_OVERLAP=100
TOP_K=5
MIN_SIMILARITY=0.7
USE_CACHE=true
```

### Configuración por Ambiente

Edita `infrastructure/config/stack_config.py`:

```python
# Cambiar ambiente
environment = "dev"    # o "staging", "prod"
```

Diferencias automáticas:
- Instancias más grandes en prod
- Más nodos OpenSearch
- Timeouts mayores
- Retention policies diferentes

## 🔧 Desarrollo Local

### Setup

```powershell
# Clonar repo
git clone https://github.com/LeonAchata/AWS-RAG-System.git
cd AWS-RAG-System

# Crear entorno virtual
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
pip install -r lambda/ingestion/requirements.txt
pip install -r lambda/query/requirements.txt
```

### Testing Local (sin AWS)

```python
# Test de procesamiento de documentos
from lambda.ingestion.utils.document_processor import DocumentProcessor

text = DocumentProcessor.extract_text(pdf_content, ".pdf")
print(text[:500])

# Test de chunking
from lambda.ingestion.utils.text_chunker import chunk_text

chunks = chunk_text(text, chunk_size=800)
print(f"Generados {len(chunks)} chunks")
```

## 📚 Documentación Adicional

- **[Quick Start Guide](docs/QUICK_START.md)** - Inicio en 5 minutos
- **[CDK Deployment](infrastructure/README.md)** - Guía completa de infraestructura
- **[Lambda Ingestion](lambda/ingestion/README.md)** - Documentación del Lambda de ingesta
- **[Lambda Query](lambda/query/README.md)** - Documentación del Lambda de query
- **[Setup Detallado](docs/SETUP.md)** - Configuración paso a paso

## 🤝 Contribuir

```powershell
# 1. Fork el repo
# 2. Crear branch
git checkout -b feature/nueva-funcionalidad

# 3. Hacer cambios y commit
git commit -m "feat: agregar nueva funcionalidad"

# 4. Push
git push origin feature/nueva-funcionalidad

# 5. Crear Pull Request
```

## 📝 License

MIT License - ver [LICENSE](LICENSE) para detalles

## 🙏 Agradecimientos

- AWS Bedrock por los modelos de IA
- LangChain por las herramientas de procesamiento
- OpenSearch por la búsqueda vectorial

---

**Desarrollado con ❤️ usando AWS CDK, Python y Bedrock**

### Fase 1: Setup Básico
1. Configurar cuenta de AWS y permisos
2. Habilitar Amazon Bedrock y solicitar acceso a modelos
3. Crear buckets S3 básicos
4. Implementar Lambda de ingesta simple (solo un tipo de documento)
5. Configurar base de datos vectorial básica

### Fase 2: Pipeline de Ingesta Completo
1. Añadir soporte para múltiples formatos de documento
2. Implementar chunking inteligente
3. Añadir procesamiento de metadatos
4. Implementar manejo de errores y reintentos
5. Crear sistema de logs estructurados

### Fase 3: Pipeline de Query
1. Implementar Lambda de query
2. Configurar API Gateway
3. Implementar búsqueda vectorial
4. Integrar con Bedrock LLM
5. Optimizar prompt engineering

### Fase 4: Frontend y UX
1. Crear interfaz de usuario básica
2. Implementar carga de documentos
3. Implementar interfaz de chat/búsqueda
4. Añadir visualización de resultados con referencias

### Fase 5: Optimización y Producción
1. Implementar caché
2. Añadir monitoreo completo
3. Optimizar costos
4. Implementar CI/CD
5. Documentación completa
6. Testing de carga

## Recursos y Referencias

### Documentación Oficial
- AWS Bedrock Documentation
- Amazon OpenSearch Service Guide
- AWS Lambda Best Practices
- LangChain Documentation

### Conceptos Clave a Estudiar
- Vector embeddings y similitud coseno
- Técnicas de prompt engineering
- RAG patterns y mejores prácticas
- Chunking strategies
- Arquitecturas serverless en AWS

### Herramientas de Desarrollo
- AWS CLI para gestión de recursos
- boto3 para Python SDK
- Postman para testing de APIs
- LocalStack para testing local (opcional)

## Próximos Pasos

Una vez comprendida esta arquitectura, el siguiente paso sería:
1. Decidir qué servicios específicos usar (principalmente la base de datos vectorial)
2. Elegir el framework de IaC
3. Comenzar con la implementación del pipeline de ingesta
4. Iterar y expandir funcionalidades