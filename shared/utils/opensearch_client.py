"""
Cliente para OpenSearch - Indexación y búsqueda vectorial
"""
import json
from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3


class OpenSearchClient:
    """Cliente para interactuar con Amazon OpenSearch Service"""
    
    def __init__(
        self, 
        endpoint: str,
        region: str = "us-east-1",
        index_name: str = "rag-documents"
    ):
        """
        Inicializa el cliente de OpenSearch
        
        Args:
            endpoint: Endpoint de OpenSearch (sin https://)
            region: Región de AWS
            index_name: Nombre del índice
        """
        self.endpoint = endpoint
        self.region = region
        self.index_name = index_name
        
        # Autenticación con IAM
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, region)
        
        # Cliente de OpenSearch
        self.client = OpenSearch(
            hosts=[{'host': endpoint, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        
        # Crear índice si no existe
        self._create_index_if_not_exists()
    
    def _create_index_if_not_exists(self):
        """Crea el índice con configuración k-NN si no existe"""
        if self.client.indices.exists(index=self.index_name):
            return
        
        # Configuración del índice con soporte k-NN
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 512
                }
            },
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1024,  # Titan Embeddings V2
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 512,
                                "m": 16
                            }
                        }
                    },
                    "content": {"type": "text"},
                    "document_id": {"type": "keyword"},
                    "chunk_id": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "metadata": {"type": "object", "enabled": True}
                }
            }
        }
        
        self.client.indices.create(index=self.index_name, body=index_body)
        print(f"Índice '{self.index_name}' creado exitosamente")
    
    def index_document(
        self, 
        chunk_id: str,
        document_id: str,
        content: str,
        embedding: List[float],
        chunk_index: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Indexa un chunk de documento en OpenSearch
        
        Args:
            chunk_id: ID único del chunk
            document_id: ID del documento original
            content: Texto del chunk
            embedding: Vector de embedding
            chunk_index: Posición del chunk en el documento
            metadata: Metadatos adicionales
            
        Returns:
            True si la indexación fue exitosa
        """
        try:
            document = {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "content": content,
                "embedding": embedding,
                "chunk_index": chunk_index,
                "metadata": metadata or {}
            }
            
            response = self.client.index(
                index=self.index_name,
                id=chunk_id,
                body=document,
                refresh=True
            )
            
            return response['result'] in ['created', 'updated']
            
        except Exception as e:
            print(f"Error indexando documento: {e}")
            return False
    
    def index_documents_batch(
        self, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Indexa múltiples documentos en batch
        
        Args:
            documents: Lista de diccionarios con los datos a indexar
            
        Returns:
            Diccionario con estadísticas de la operación
        """
        from opensearchpy.helpers import bulk
        
        actions = []
        for doc in documents:
            action = {
                "_index": self.index_name,
                "_id": doc.get("chunk_id"),
                "_source": doc
            }
            actions.append(action)
        
        try:
            success, failed = bulk(self.client, actions)
            return {"success": success, "failed": failed}
        except Exception as e:
            print(f"Error en indexación batch: {e}")
            return {"success": 0, "failed": len(documents)}
    
    def search_similar(
        self, 
        query_embedding: List[float],
        k: int = 5,
        min_score: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos similares usando k-NN
        
        Args:
            query_embedding: Vector de embedding de la consulta
            k: Número de resultados a retornar
            min_score: Score mínimo de similitud
            filters: Filtros adicionales de metadatos
            
        Returns:
            Lista de documentos similares con sus scores
        """
        try:
            # Query k-NN
            query_body = {
                "size": k,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_embedding,
                            "k": k
                        }
                    }
                }
            }
            
            # Añadir filtros si existen
            if filters:
                query_body["query"] = {
                    "bool": {
                        "must": [
                            query_body["query"]
                        ],
                        "filter": [
                            {"term": {key: value}} 
                            for key, value in filters.items()
                        ]
                    }
                }
            
            response = self.client.search(
                index=self.index_name,
                body=query_body
            )
            
            # Procesar resultados
            results = []
            for hit in response['hits']['hits']:
                score = hit['_score']
                if score >= min_score:
                    results.append({
                        "chunk_id": hit['_id'],
                        "document_id": hit['_source'].get('document_id'),
                        "content": hit['_source'].get('content'),
                        "score": score,
                        "chunk_index": hit['_source'].get('chunk_index'),
                        "metadata": hit['_source'].get('metadata', {})
                    })
            
            return results
            
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return []
    
    def delete_document(self, document_id: str) -> int:
        """
        Elimina todos los chunks de un documento
        
        Args:
            document_id: ID del documento a eliminar
            
        Returns:
            Número de chunks eliminados
        """
        try:
            query = {
                "query": {
                    "term": {"document_id": document_id}
                }
            }
            
            response = self.client.delete_by_query(
                index=self.index_name,
                body=query
            )
            
            return response.get('deleted', 0)
            
        except Exception as e:
            print(f"Error eliminando documento: {e}")
            return 0


# Instancia global para reutilización en Lambda
_opensearch_client = None


def get_opensearch_client(
    endpoint: str,
    region: str = "us-east-1",
    index_name: str = "rag-documents"
) -> OpenSearchClient:
    """
    Obtiene una instancia singleton del cliente de OpenSearch
    """
    global _opensearch_client
    if _opensearch_client is None:
        _opensearch_client = OpenSearchClient(endpoint, region, index_name)
    return _opensearch_client
