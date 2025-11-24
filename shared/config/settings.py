"""
Configuración central del sistema RAG
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class BedrockConfig:
    """Configuración para Amazon Bedrock"""
    # Modelo de embeddings
    embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    embedding_dimension: int = 1024
    
    # Modelo LLM
    llm_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 2048
    
    # Región
    region_name: str = "us-east-1"


@dataclass
class ChunkingConfig:
    """Configuración para división de documentos"""
    chunk_size: int = 800
    chunk_overlap: int = 100
    separator: str = "\n\n"


@dataclass
class RetrievalConfig:
    """Configuración para búsqueda vectorial"""
    top_k: int = 5
    similarity_threshold: float = 0.7
    similarity_metric: str = "cosine"


@dataclass
class S3Config:
    """Configuración para S3"""
    raw_bucket_name: str = os.getenv("RAW_BUCKET_NAME", "rag-system-raw-docs")
    processed_bucket_name: str = os.getenv("PROCESSED_BUCKET_NAME", "rag-system-processed")


@dataclass
class OpenSearchConfig:
    """Configuración para OpenSearch"""
    endpoint: Optional[str] = os.getenv("OPENSEARCH_ENDPOINT")
    index_name: str = "rag-documents"
    username: Optional[str] = os.getenv("OPENSEARCH_USERNAME", "admin")
    password: Optional[str] = os.getenv("OPENSEARCH_PASSWORD")


class Config:
    """Configuración principal del sistema"""
    def __init__(self):
        self.bedrock = BedrockConfig()
        self.chunking = ChunkingConfig()
        self.retrieval = RetrievalConfig()
        self.s3 = S3Config()
        self.opensearch = OpenSearchConfig()


# Instancia global de configuración
config = Config()
