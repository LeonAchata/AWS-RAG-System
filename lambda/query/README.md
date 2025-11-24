# Lambda de Query - RAG System

## Descripción

Esta función Lambda procesa consultas de usuarios, realiza búsqueda vectorial en OpenSearch, y genera respuestas contextualizadas usando Amazon Bedrock Claude.

## Flujo de Procesamiento

1. **Recepción de Query**: Consulta del usuario vía API Gateway
2. **Validación**: Sanitización y validación de la consulta
3. **Caché Check**: Verifica si existe respuesta cacheada (opcional)
4. **Embedding**: Genera vector de la consulta con Titan Embeddings
5. **Búsqueda**: Recupera top-K chunks más relevantes de OpenSearch
6. **Construcción de Prompt**: Crea prompt con contexto recuperado
7. **Generación**: Claude genera respuesta basada en contexto
8. **Respuesta**: Retorna respuesta + fuentes + métricas de confianza

## Archivos

- `handler.py` - Handler principal del Lambda
- `requirements.txt` - Dependencias de Python
- `utils/prompt_builder.py` - Construcción de prompts y formateo
- `utils/cache.py` - Sistema de caché en memoria

## Variables de Entorno

| Variable | Descripción | Requerido | Default |
|----------|-------------|-----------|---------|
| `OPENSEARCH_ENDPOINT` | Endpoint de OpenSearch | Sí | - |
| `OPENSEARCH_INDEX` | Nombre del índice | No | `rag-documents` |
| `AWS_REGION` | Región de AWS | No | `us-east-1` |
| `BEDROCK_EMBEDDING_MODEL` | Modelo de embeddings | No | `amazon.titan-embed-text-v2:0` |
| `BEDROCK_LLM_MODEL` | Modelo LLM | No | `anthropic.claude-3-sonnet-20240229-v1:0` |
| `TOP_K` | Número de chunks a recuperar | No | `5` |
| `MIN_SIMILARITY` | Similitud mínima | No | `0.7` |
| `USE_CACHE` | Habilitar caché | No | `true` |

## Request Format

### Query Simple

```json
{
  "query": "¿Qué es machine learning?",
  "top_k": 5,
  "min_similarity": 0.7,
  "include_sources": true
}
```

### Query con Filtros

```json
{
  "query": "¿Cuáles son las mejores prácticas?",
  "filters": {
    "document_type": "pdf",
    "author": "John Doe"
  },
  "top_k": 3
}
```

### Query Conversacional

```json
{
  "query": "¿Y cuál es la diferencia con deep learning?",
  "conversational": true,
  "conversation_history": [
    {
      "role": "user",
      "content": "¿Qué es machine learning?"
    },
    {
      "role": "assistant",
      "content": "Machine learning es..."
    }
  ]
}
```

## Response Format

```json
{
  "statusCode": 200,
  "body": {
    "query": "¿Qué es machine learning?",
    "answer": "Machine learning es una rama de la inteligencia artificial que...",
    "sources": [
      {
        "document_id": "uuid-1234",
        "filename": "ml-guide.pdf",
        "title": "Guía de Machine Learning",
        "chunks_used": [
          {
            "chunk_index": 0,
            "score": 0.92
          }
        ],
        "score": 0.92
      }
    ],
    "total_chunks_used": 3,
    "confidence": {
      "confidence": "high",
      "avg_similarity": 0.87,
      "max_similarity": 0.92,
      "chunks_retrieved": 3
    },
    "response_time": 2.45,
    "from_cache": false
  }
}
```

## Características

### 1. Sistema de Caché Inteligente

- Caché en memoria de queries frecuentes
- TTL configurable (default: 30 minutos)
- Reduce costos de Bedrock
- Evita caché de queries temporales ("hoy", "ahora", etc.)

### 2. Niveles de Confianza

- **High**: Similitud promedio > 0.75, máxima > 0.85
- **Medium**: Similitud promedio > 0.60, máxima > 0.70
- **Low**: Similitudes menores

### 3. Modo Conversacional

- Mantiene contexto de conversación
- Considera historial de mensajes previos
- Respuestas más naturales y contextuales

### 4. Construcción Inteligente de Prompts

- System prompts optimizados para RAG
- Inclusión de metadatos de fuentes
- Instrucciones claras al modelo
- Formateo de contexto legible

### 5. Trazabilidad de Fuentes

- Identifica documentos utilizados
- Scores de similitud
- Referencias a chunks específicos
- Metadatos completos

## Prompt Engineering

### System Prompt Default

```
Eres un asistente experto que responde preguntas basándose únicamente en el contexto proporcionado.

Instrucciones:
1. Responde SOLO basándote en la información del contexto proporcionado
2. Si la información no está en el contexto, di claramente "No tengo información suficiente"
3. Sé conciso pero completo
4. Si citas información, menciona de qué documento proviene
5. Mantén un tono profesional y claro
6. No inventes información
```

### User Prompt Structure

```
Contexto de documentos relevantes:

[Fuente 1: documento.pdf (relevancia: 0.92)]
{contenido del chunk}

---

Pregunta del usuario: {query}

Por favor, responde la pregunta basándote únicamente en el contexto proporcionado.
```

## Permisos IAM Requeridos

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:*:*:inference-profile/amazon.titan-embed-text-v2:0",
        "arn:aws:bedrock:*:*:inference-profile/anthropic.claude-3-sonnet-20240229-v1:0"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "es:ESHttpGet",
        "es:ESHttpPost"
      ],
      "Resource": "arn:aws:es:*:*:domain/*/rag-documents/*"
    }
  ]
}
```

## Optimizaciones

### Reducción de Costos

1. **Caché activado** - Reutiliza respuestas frecuentes
2. **Embeddings solo de query** - No re-embeddings de documentos
3. **Top-K ajustable** - Menos chunks = menor costo LLM
4. **Filtros** - Búsqueda más precisa, menos tokens

### Performance

1. **Singleton clients** - Reutiliza conexiones
2. **Batch operations** - Cuando es posible
3. **Búsqueda k-NN optimizada** - Usando HNSW en OpenSearch
4. **Memory allocation** - 512-1024 MB suficiente

## Testing Local

```python
import json
from handler import lambda_handler

# Test simple
event = {
    "body": json.dumps({
        "query": "¿Qué es AWS Lambda?",
        "top_k": 3
    })
}

result = lambda_handler(event, None)
print(json.dumps(json.loads(result['body']), indent=2))
```

## Métricas y Monitoreo

### CloudWatch Logs

- Queries procesadas
- Tiempo de respuesta
- Chunks recuperados
- Scores de similitud
- Cache hits/misses

### Métricas Clave

- Latencia P50, P95, P99
- Tasa de éxito/error
- Cache hit rate
- Costos por query (Bedrock)
- Relevancia de resultados

## Troubleshooting

### No se encuentran documentos relevantes

- Verificar que los documentos estén indexados
- Reducir `min_similarity`
- Aumentar `top_k`
- Revisar filtros aplicados

### Respuestas irrelevantes

- Ajustar `min_similarity` (aumentar)
- Mejorar chunking strategy
- Revisar prompt engineering
- Usar re-ranking

### Timeout

- Aumentar timeout de Lambda (30-60 segundos)
- Reducir `top_k`
- Optimizar OpenSearch
- Verificar latencia de Bedrock

## Próximos Pasos

✅ Lambda de Query implementado
⏭️ Siguiente: Infraestructura CDK para deployment automático
