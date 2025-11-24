# Sistema RAG (Retrieval-Augmented Generation) con AWS

## 🚀 Estructura del Proyecto Creada

```
AWS-RAG-System/
├── infrastructure/          # Infraestructura como código (AWS CDK)
│   ├── stacks/             # Definición de stacks de CloudFormation
│   ├── constructs/         # Componentes reutilizables de CDK
│   ├── config/             # Configuraciones de infraestructura
│   ├── app.py              # Punto de entrada CDK
│   ├── cdk.json            # Configuración CDK
│   └── requirements.txt    # Dependencias de CDK
│
├── lambda/                  # Funciones Lambda
│   ├── ingestion/          # Lambda de procesamiento de documentos
│   │   ├── handler.py
│   │   ├── requirements.txt
│   │   └── utils/
│   └── query/              # Lambda de consultas
│       ├── handler.py
│       ├── requirements.txt
│       └── utils/
│
├── shared/                  # Código compartido entre servicios
│   ├── models/             # Modelos de datos
│   │   └── document.py     # Clases Document, Chunk, QueryResult
│   ├── utils/              # Utilidades comunes
│   └── config/
│       └── settings.py     # Configuración centralizada
│
├── frontend/                # Aplicación web (React)
│   ├── src/
│   └── public/
│
├── tests/                   # Tests
│   ├── unit/
│   └── integration/
│
├── docs/                    # Documentación adicional
├── scripts/                 # Scripts de deployment y utilidades
├── .env.example            # Template de variables de entorno
├── .gitignore
├── requirements.txt        # Dependencias principales del proyecto
└── README.md              # Este archivo
```

## 📋 Archivos Creados

### Configuración:
- ✅ `.gitignore` - Ignora archivos innecesarios
- ✅ `.env.example` - Template de variables de entorno
- ✅ `requirements.txt` - Dependencias principales
- ✅ `shared/config/settings.py` - Configuración centralizada
- ✅ `shared/models/document.py` - Modelos de datos

### Infraestructura:
- ✅ `infrastructure/app.py` - Punto de entrada CDK
- ✅ `infrastructure/cdk.json` - Configuración CDK
- ✅ `infrastructure/requirements.txt` - Dependencias CDK

### Lambda Functions:
- ✅ `lambda/ingestion/requirements.txt` - Deps para ingesta
- ✅ `lambda/query/requirements.txt` - Deps para queries

## 🎯 Próximos Pasos

### 1. Implementar Funciones Lambda
- Handler de ingesta para procesar documentos
- Handler de query para responder preguntas
- Utilidades de procesamiento de texto
- Cliente de Bedrock para embeddings y LLM

### 2. Configurar Infraestructura CDK
- Stack principal con todos los recursos
- S3 buckets para documentos
- OpenSearch cluster para vectores
- API Gateway para endpoints
- IAM roles y políticas

### 3. Frontend
- Interfaz React para subir documentos
- Chat interface para hacer preguntas
- Visualización de resultados

## 📦 Instalación

```bash
# Instalar dependencias principales
pip install -r requirements.txt

# Instalar dependencias de CDK
cd infrastructure
pip install -r requirements.txt
```

## 🔧 Configuración

1. Copiar `.env.example` a `.env`
2. Completar las variables de entorno
3. Configurar AWS CLI con credenciales

## ¿Continuamos?

Dime qué parte quieres que implemente primero:
1. **Lambdas** (ingesta y query)
2. **Infraestructura CDK** (deployment)
3. **Frontend** (interfaz web)
4. **Utilidades** (procesadores de documentos, cliente Bedrock)
