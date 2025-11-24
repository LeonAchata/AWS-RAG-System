"""
Modelos de datos para documentos y chunks
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class DocumentStatus(Enum):
    """Estados posibles de un documento"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(Enum):
    """Tipos de documentos soportados"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MD = "md"
    JSON = "json"


@dataclass
class DocumentMetadata:
    """Metadatos de un documento"""
    document_id: str
    title: str
    source: str
    document_type: DocumentType
    author: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    language: str = "es"
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentChunk:
    """Fragmento de un documento con su embedding"""
    chunk_id: str
    document_id: str
    content: str
    embedding: Optional[List[float]] = None
    chunk_index: int = 0
    start_char: int = 0
    end_char: int = 0
    metadata: Optional[DocumentMetadata] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el chunk a diccionario para almacenamiento"""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "content": self.content,
            "embedding": self.embedding,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "metadata": self.metadata.__dict__ if self.metadata else None
        }


@dataclass
class Document:
    """Documento completo"""
    document_id: str
    content: str
    metadata: DocumentMetadata
    chunks: List[DocumentChunk] = field(default_factory=list)
    status: DocumentStatus = DocumentStatus.PENDING
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el documento a diccionario"""
        return {
            "document_id": self.document_id,
            "content": self.content,
            "metadata": self.metadata.__dict__,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "status": self.status.value,
            "error_message": self.error_message,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }


@dataclass
class QueryResult:
    """Resultado de una búsqueda"""
    query: str
    answer: str
    relevant_chunks: List[DocumentChunk]
    similarity_scores: List[float]
    response_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
