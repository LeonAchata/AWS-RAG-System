"""
Configuración de variables del stack
Permite diferentes configuraciones para dev, staging, prod
"""
from typing import Dict, Any


class StackConfig:
    """Configuración base del stack"""
    
    def __init__(self, environment: str = "dev"):
        self.environment = environment
        self.config = self._get_config()
    
    def _get_config(self) -> Dict[str, Any]:
        """Retorna configuración según el ambiente"""
        
        configs = {
            "dev": {
                # OpenSearch
                "opensearch_instance_type": "t3.small.search",
                "opensearch_data_nodes": 1,
                "opensearch_ebs_volume_size": 10,
                
                # Lambda
                "ingestion_lambda_memory": 2048,
                "ingestion_lambda_timeout": 5,  # minutos
                "query_lambda_memory": 1024,
                "query_lambda_timeout": 60,  # segundos
                
                # API Gateway
                "api_throttle_rate_limit": 100,
                "api_throttle_burst_limit": 200,
                
                # RAG Parameters
                "chunk_size": 800,
                "chunk_overlap": 100,
                "top_k": 5,
                "min_similarity": 0.7,
                
                # Bedrock Models
                "embedding_model": "amazon.titan-embed-text-v2:0",
                "llm_model": "anthropic.claude-3-sonnet-20240229-v1:0",
                
                # Retention
                "log_retention_days": 7,
                "s3_lifecycle_days": 30,
                
                # Removal Policy
                "removal_policy": "DESTROY",
                "auto_delete_objects": True
            },
            
            "staging": {
                # OpenSearch - más robusto
                "opensearch_instance_type": "t3.medium.search",
                "opensearch_data_nodes": 2,
                "opensearch_ebs_volume_size": 50,
                
                # Lambda - más recursos
                "ingestion_lambda_memory": 3008,
                "ingestion_lambda_timeout": 10,
                "query_lambda_memory": 1536,
                "query_lambda_timeout": 90,
                
                # API Gateway - más capacidad
                "api_throttle_rate_limit": 500,
                "api_throttle_burst_limit": 1000,
                
                # RAG Parameters
                "chunk_size": 800,
                "chunk_overlap": 100,
                "top_k": 5,
                "min_similarity": 0.7,
                
                # Bedrock Models
                "embedding_model": "amazon.titan-embed-text-v2:0",
                "llm_model": "anthropic.claude-3-sonnet-20240229-v1:0",
                
                # Retention
                "log_retention_days": 30,
                "s3_lifecycle_days": 90,
                
                # Removal Policy
                "removal_policy": "RETAIN",
                "auto_delete_objects": False
            },
            
            "prod": {
                # OpenSearch - producción
                "opensearch_instance_type": "r6g.large.search",
                "opensearch_data_nodes": 3,
                "opensearch_ebs_volume_size": 100,
                
                # Lambda - máximo rendimiento
                "ingestion_lambda_memory": 3008,
                "ingestion_lambda_timeout": 15,
                "query_lambda_memory": 2048,
                "query_lambda_timeout": 120,
                
                # API Gateway - alta capacidad
                "api_throttle_rate_limit": 2000,
                "api_throttle_burst_limit": 5000,
                
                # RAG Parameters
                "chunk_size": 800,
                "chunk_overlap": 100,
                "top_k": 5,
                "min_similarity": 0.7,
                
                # Bedrock Models
                "embedding_model": "amazon.titan-embed-text-v2:0",
                "llm_model": "anthropic.claude-3-5-sonnet-20240620-v1:0",  # Claude 3.5
                
                # Retention
                "log_retention_days": 90,
                "s3_lifecycle_days": 365,
                
                # Removal Policy
                "removal_policy": "RETAIN",
                "auto_delete_objects": False
            }
        }
        
        return configs.get(self.environment, configs["dev"])
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración"""
        return self.config.get(key, default)
