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
    build_conversational_prompt,
    format_response_with_sources,
    calculate_response_confidence,
    sanitize_query
)
from utils.cache import get_cache, should_use_cache

# Importar clientes compartidos
import sys
sys.path.append('/opt/python')  # Para Lambda Layers

try:
    from shared.utils.bedrock_client import get_bedrock_client
    from shared.utils.opensearch_client import get_opensearch_client
except ImportError:
    print("Warning: No se pudieron importar shared utilities")


# Variables de entorno
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX', 'rag-documents')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
BEDROCK_EMBEDDING_MODEL = os.environ.get('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v2:0')
BEDROCK_LLM_MODEL = os.environ.get('BEDROCK_LLM_MODEL', 'anthropic.claude-3-sonnet-20240229-v1:0')
TOP_K = int(os.environ.get('TOP_K', '5'))
MIN_SIMILARITY = float(os.environ.get('MIN_SIMILARITY', '0.7'))
USE_CACHE = os.environ.get('USE_CACHE', 'true').lower() == 'true'


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
        conversational = body.get('conversational', False)
        conversation_history = body.get('conversation_history')
        include_sources = body.get('include_sources', True)
        
        print(f"Query: {query}")
        print(f"Filters: {filters}, Top-K: {top_k}, Min Similarity: {min_similarity}")
        
        # Verificar caché si está habilitado
        if USE_CACHE and should_use_cache(query):
            cache = get_cache()
            cached_result = cache.get(query, filters)
            
            if cached_result:
                print("Respuesta obtenida del caché")
                return success_response({
                    **cached_result,
                    'from_cache': True,
                    'response_time': time.time() - start_time
                })
        
        # Procesar query
        result = process_query(
            query=query,
            filters=filters,
            top_k=top_k,
            min_similarity=min_similarity,
            conversational=conversational,
            conversation_history=conversation_history,
            include_sources=include_sources
        )
        
        # Cachear resultado si es apropiado
        if USE_CACHE and should_use_cache(query):
            cache = get_cache()
            cache.set(query, result, filters)
        
        result['response_time'] = time.time() - start_time
        result['from_cache'] = False
        
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
    conversational: bool = False,
    conversation_history: Optional[List[Dict[str, str]]] = None,
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
    
    print(f"Embedding generado: {len(query_embedding)} dimensiones")
    
    # 2. Buscar documentos similares en OpenSearch
    print(f"Buscando documentos relevantes (top-{top_k})...")
    opensearch_client = get_opensearch_client(
        endpoint=OPENSEARCH_ENDPOINT,
        region=AWS_REGION,
        index_name=OPENSEARCH_INDEX
    )
    
    relevant_chunks = opensearch_client.search_similar(
        query_embedding=query_embedding,
        k=top_k,
        min_score=min_similarity,
        filters=filters
    )
    
    print(f"Encontrados {len(relevant_chunks)} chunks relevantes")
    
    # Verificar si se encontraron resultados
    if not relevant_chunks:
        return {
            'answer': "No encontré información relevante en los documentos para responder tu pregunta.",
            'sources': [],
            'confidence': {
                'confidence': 'none',
                'avg_similarity': 0.0,
                'max_similarity': 0.0,
                'chunks_retrieved': 0
            }
        }
    
    # 3. Construir prompt con contexto
    print("Construyendo prompt...")
    
    if conversational and conversation_history:
        system_prompt, user_prompt = build_conversational_prompt(
            query=query,
            context_chunks=relevant_chunks,
            conversation_history=conversation_history
        )
    else:
        system_prompt, user_prompt = build_rag_prompt(
            query=query,
            context_chunks=relevant_chunks
        )
    
    # 4. Generar respuesta con el LLM
    print("Generando respuesta con LLM...")
    
    answer = bedrock_client.generate_response(
        prompt=user_prompt,
        system_prompt=system_prompt,
        model_id=BEDROCK_LLM_MODEL,
        temperature=0.2,
        max_tokens=2048
    )
    
    print(f"Respuesta generada: {len(answer)} caracteres")
    
    # 5. Calcular métricas de confianza
    similarity_scores = [chunk['score'] for chunk in relevant_chunks]
    confidence = calculate_response_confidence(
        similarity_scores=similarity_scores,
        num_chunks=len(relevant_chunks)
    )
    
    # 6. Formatear respuesta final
    if include_sources:
        result = format_response_with_sources(
            answer=answer,
            sources=relevant_chunks,
            include_scores=True
        )
    else:
        result = {
            'answer': answer,
            'total_chunks_used': len(relevant_chunks)
        }
    
    result['confidence'] = confidence
    result['query'] = query
    
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


def validate_environment():
    """Valida que las variables de entorno necesarias estén configuradas"""
    required_vars = ['OPENSEARCH_ENDPOINT']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        raise ValueError(f"Variables de entorno faltantes: {', '.join(missing_vars)}")


# Validar entorno al inicializar
try:
    validate_environment()
except Exception as e:
    print(f"Warning: {str(e)}")
