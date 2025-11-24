# Sistema RAG (Retrieval-Augmented Generation) con AWS

## Descripción General del Proyecto

Este proyecto implementa un sistema completo de RAG (Retrieval-Augmented Generation) utilizando servicios de AWS, específicamente Amazon Bedrock para embeddings y generación de respuestas. El sistema permite a los usuarios cargar documentos, procesarlos automáticamente, indexarlos en una base de datos vectorial, y posteriormente realizar consultas inteligentes sobre el contenido almacenado.

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

## Estructura de Directorios Sugerida

```
rag-system/
├── infrastructure/          # IaC (CDK, Terraform, etc.)
│   ├── stacks/
│   ├── constructs/
│   └── config/
├── lambda/                  # Funciones Lambda
│   ├── ingestion/
│   │   ├── handler.py
│   │   ├── requirements.txt
│   │   └── utils/
│   └── query/
│       ├── handler.py
│       ├── requirements.txt
│       └── utils/
├── frontend/                # Aplicación de usuario (opcional)
│   ├── src/
│   ├── public/
│   └── package.json
├── shared/                  # Código compartido
│   ├── models/
│   ├── utils/
│   └── config/
├── tests/                   # Tests unitarios e integración
│   ├── unit/
│   └── integration/
├── docs/                    # Documentación adicional
├── scripts/                 # Scripts de deployment y utilidades
└── README.md
```

## Flujo de Datos Detallado

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

## Pasos de Implementación Sugeridos

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