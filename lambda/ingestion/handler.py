"""
AWS Lambda Handler para Ingesta de Documentos
Procesa documentos, genera embeddings y los indexa en OpenSearch
"""
import json
import os
import boto3
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Importar utilidades locales
from utils.document_processor import DocumentProcessor, get_metadata_from_file
from utils.text_chunker import chunk_text, clean_text

# Importar clientes compartidos (necesitarán estar en Lambda Layer o empaquetados)
import sys
sys.path.append('/opt/python')  # Para Lambda Layers

try:
    from shared.utils.bedrock_client import get_bedrock_client
    from shared.utils.opensearch_client import get_opensearch_client
except ImportError:
    # Fallback para desarrollo local
    print("Warning: No se pudieron importar shared utilities")


# Cliente S3
s3_client = boto3.client('s3')

# Variables de entorno
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX', 'rag-documents')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
BEDROCK_EMBEDDING_MODEL = os.environ.get('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v2:0')
CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', '800'))
CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', '100'))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler principal de Lambda
    Procesa eventos de S3 cuando se sube un nuevo documento
    
    Args:
        event: Evento de S3 o evento de API Gateway
        context: Contexto de Lambda
        
    Returns:
        Respuesta con el resultado del procesamiento
    """
    print(f"Evento recibido: {json.dumps(event)}")
    
    try:
        # Determinar si es un evento de S3 o API Gateway
        if 'Records' in event and event['Records']:
            # Evento de S3
            return process_s3_event(event, context)
        else:
            # Evento de API Gateway (carga directa)
            return process_api_event(event, context)
            
    except Exception as e:
        print(f"Error en lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Error procesando documento'
            })
        }


def process_s3_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Procesa un evento de S3 (nuevo archivo subido)
    """
    results = []
    
    for record in event['Records']:
        try:
            # Obtener información del archivo
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            print(f"Procesando archivo: s3://{bucket}/{key}")
            
            # Descargar archivo de S3
            response = s3_client.get_object(Bucket=bucket, Key=key)
            file_content = response['Body'].read()
            file_size = response['ContentLength']
            
            # Procesar documento
            result = process_document(
                file_content=file_content,
                filename=key,
                file_size=file_size,
                source=f"s3://{bucket}/{key}"
            )
            
            results.append({
                'file': key,
                'status': 'success',
                'document_id': result['document_id'],
                'chunks_created': result['chunks_count']
            })
            
        except Exception as e:
            print(f"Error procesando {key}: {str(e)}")
            results.append({
                'file': key,
                'status': 'error',
                'error': str(e)
            })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Procesamiento completado',
            'results': results
        })
    }


def process_api_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Procesa un evento de API Gateway (carga directa vía API)
    """
    try:
        # Parsear body si es string
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        # Validar parámetros requeridos
        if 'content' not in body:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Parámetro "content" requerido'
                })
            }
        
        # Procesar documento directamente desde contenido
        content = body['content']
        filename = body.get('filename', 'document.txt')
        
        # Si el contenido está en base64, decodificar
        import base64
        if body.get('is_base64', False):
            file_content = base64.b64decode(content)
        else:
            file_content = content.encode('utf-8')
        
        result = process_document(
            file_content=file_content,
            filename=filename,
            file_size=len(file_content),
            source='api_upload'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Documento procesado exitosamente',
                'document_id': result['document_id'],
                'chunks_count': result['chunks_count']
            })
        }
        
    except Exception as e:
        print(f"Error en process_api_event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def process_document(
    file_content: bytes,
    filename: str,
    file_size: int,
    source: str
) -> Dict[str, Any]:
    """
    Procesa un documento completo: extrae texto, chunking, embeddings e indexación
    
    Args:
        file_content: Contenido del archivo en bytes
        filename: Nombre del archivo
        file_size: Tamaño del archivo
        source: Origen del documento
        
    Returns:
        Información del procesamiento
    """
    document_id = str(uuid.uuid4())
    
    # 1. Extraer extensión del archivo
    file_extension = os.path.splitext(filename)[1]
    
    print(f"Extrayendo texto de {filename}...")
    
    # 2. Extraer texto del documento
    text = DocumentProcessor.extract_text(file_content, file_extension)
    text = clean_text(text)
    
    print(f"Texto extraído: {len(text)} caracteres")
    
    # 3. Extraer metadatos
    metadata = get_metadata_from_file(filename, file_size, file_content, file_extension)
    metadata['source'] = source
    metadata['processed_at'] = datetime.utcnow().isoformat()
    
    # 4. Dividir en chunks
    print(f"Dividiendo texto en chunks...")
    chunks = chunk_text(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    
    print(f"Generado {len(chunks)} chunks")
    
    # 5. Generar embeddings para cada chunk
    print("Generando embeddings...")
    bedrock_client = get_bedrock_client(region_name=AWS_REGION)
    
    chunks_data = []
    for chunk in chunks:
        # Generar embedding
        embedding = bedrock_client.generate_embeddings(
            text=chunk.content,
            model_id=BEDROCK_EMBEDDING_MODEL
        )
        
        chunk_id = f"{document_id}_{chunk.chunk_index}"
        
        chunks_data.append({
            'chunk_id': chunk_id,
            'document_id': document_id,
            'content': chunk.content,
            'embedding': embedding,
            'chunk_index': chunk.chunk_index,
            'metadata': metadata
        })
    
    print(f"Embeddings generados para {len(chunks_data)} chunks")
    
    # 6. Indexar en OpenSearch
    print("Indexando en OpenSearch...")
    opensearch_client = get_opensearch_client(
        endpoint=OPENSEARCH_ENDPOINT,
        region=AWS_REGION,
        index_name=OPENSEARCH_INDEX
    )
    
    result = opensearch_client.index_documents_batch(chunks_data)
    
    print(f"Indexación completada: {result['success']} exitosos, {result['failed']} fallidos")
    
    return {
        'document_id': document_id,
        'filename': filename,
        'chunks_count': len(chunks_data),
        'indexing_result': result,
        'metadata': metadata
    }


def validate_environment():
    """
    Valida que las variables de entorno necesarias estén configuradas
    """
    required_vars = ['OPENSEARCH_ENDPOINT']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        raise ValueError(f"Variables de entorno faltantes: {', '.join(missing_vars)}")


# Validar entorno al inicializar
try:
    validate_environment()
except Exception as e:
    print(f"Warning: {str(e)}")
