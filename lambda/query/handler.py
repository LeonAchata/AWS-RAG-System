"""
AWS Lambda Handler para Query y Generación de Respuestas
Recibe consultas, busca documentos relevantes y genera respuestas con LLM
"""
import json
import os
import time
from typing import Dict, Any, List, Optional

# Importar utilidades locales
from utils.prompt_builder import (
    build_rag_prompt,
    format_response_with_sources,
    sanitize_query
)

# Importar clientes compartidos
import sys
sys.path.append('/opt/python')  # Para Lambda Layers

try:
    from shared.utils.bedrock_client import get_bedrock_client
    from shared.utils.postgres_client import PostgresVectorClient
except ImportError as e:
    print(f"Warning: No se pudieron importar shared utilities: {e}")


# Variables de entorno
DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN')
DB_NAME = os.environ.get('DB_NAME', 'ragdb')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
BEDROCK_EMBEDDING_MODEL = os.environ.get('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v2:0')
BEDROCK_LLM_MODEL = os.environ.get('BEDROCK_LLM_MODEL', 'anthropic.claude-3-sonnet-20240229-v1:0')
TOP_K = int(os.environ.get('TOP_K', '5'))
MIN_SIMILARITY = float(os.environ.get('MIN_SIMILARITY', '0.1'))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler principal de Lambda para queries
    
    Args:
        event: Evento de API Gateway con la consulta del usuario
        context: Contexto de Lambda
        
    Returns:
        Respuesta con la respuesta generada y fuentes
    """
    print(f"Evento recibido: {json.dumps(event)}")
    
    start_time = time.time()
    
    try:
        # Parsear body
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        # Validar parámetros
        if 'query' not in body:
            return error_response(400, 'Parámetro "query" requerido')
        
        query = sanitize_query(body['query'])
        
        # Parámetros opcionales
        filters = body.get('filters')
        top_k = body.get('top_k', TOP_K)
        min_similarity = body.get('min_similarity', MIN_SIMILARITY)
        include_sources = body.get('include_sources', True)
        
        print(f"Query: {query}")
        print(f"Top-K: {top_k}, Min Similarity: {min_similarity}")
        
        # Procesar query
        result = process_query(
            query=query,
            filters=filters,
            top_k=top_k,
            min_similarity=min_similarity,
            include_sources=include_sources
        )
        
        result['response_time'] = time.time() - start_time
        
        return success_response(result)
        
    except ValueError as e:
        print(f"Error de validación: {str(e)}")
        return error_response(400, str(e))
    except Exception as e:
        print(f"Error en lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(500, f"Error procesando consulta: {str(e)}")


def process_query(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 5,
    min_similarity: float = 0.7,
    include_sources: bool = True
) -> Dict[str, Any]:
    """
    Procesa una consulta completa: embedding -> búsqueda -> generación
    
    Args:
        query: Consulta del usuario
        filters: Filtros de metadatos opcionales
        top_k: Número de chunks a recuperar
        min_similarity: Similitud mínima requerida
        conversational: Si usar modo conversacional
        conversation_history: Historial de conversación
        include_sources: Si incluir fuentes en la respuesta
        
    Returns:
        Diccionario con respuesta y metadatos
    """
    # 1. Generar embedding de la query
    print("Generando embedding de la consulta...")
    bedrock_client = get_bedrock_client(region_name=AWS_REGION)
    
    query_embedding = bedrock_client.generate_embeddings(
        text=query,
        model_id=BEDROCK_EMBEDDING_MODEL
    )
    
    print(f"Embedding generado. Dimensión: {len(query_embedding)}")
    
    # 2. Buscar documentos relevantes en PostgreSQL
    print(f"Buscando documentos similares en PostgreSQL...")
    with PostgresVectorClient(
        db_secret_arn=DB_SECRET_ARN,
        db_name=DB_NAME,
        region=AWS_REGION
    ) as pg_client:
        documents = pg_client.search_similar(
            query_embedding=query_embedding,
            top_k=top_k,
            min_similarity=min_similarity
        )
    
    print(f"Se encontraron {len(documents)} documentos relevantes")
    
    # Si no hay documentos relevantes
    if not documents:
        return {
            'answer': 'No encontré información relevante para responder tu pregunta. Por favor, intenta reformular tu consulta o sube documentos relacionados.',
            'sources': [],
            'num_sources': 0,
            'confidence': 0.0
        }
    
    # 3. Construir prompt con contexto
    print("Construyendo prompt...")
    prompt = build_rag_prompt(
        query=query,
        documents=documents
    )
    
    # 4. Generar respuesta con LLM
    print("Generando respuesta con Claude...")
    response_text = bedrock_client.generate_response(
        prompt=prompt,
        model_id=BEDROCK_LLM_MODEL,
        temperature=0.2,
        max_tokens=2048
    )
    
    print("Respuesta generada")
    
    # 5. Formatear respuesta con fuentes
    result = format_response_with_sources(
        response_text=response_text,
        documents=documents,
        include_sources=include_sources
    )
    
    return result


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Genera una respuesta de error"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message
        })
    }


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Genera una respuesta exitosa"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data, ensure_ascii=False)
    }

