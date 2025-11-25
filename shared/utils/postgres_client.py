"""
Cliente para PostgreSQL con pgvector - Indexación y búsqueda vectorial
"""
import json
import os
import boto3
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict, Any, Optional


class PostgresVectorClient:
    """Cliente para interactuar con PostgreSQL + pgvector"""
    
    def __init__(
        self, 
        db_secret_arn: str = None,
        db_name: str = "ragdb",
        region: str = "us-east-1"
    ):
        """
        Inicializa el cliente de PostgreSQL
        
        Args:
            db_secret_arn: ARN del secret con credenciales de DB
            db_name: Nombre de la base de datos
            region: Región de AWS
        """
        self.db_name = db_name
        self.region = region
        self.connection = None
        
        # Obtener credenciales desde Secrets Manager
        if db_secret_arn:
            credentials = self._get_db_credentials(db_secret_arn)
            self.host = credentials['host']
            self.port = credentials['port']
            self.username = credentials['username']
            self.password = credentials['password']
        
        # Conectar y configurar la base de datos
        self._connect()
        self._setup_database()
    
    def _get_db_credentials(self, secret_arn: str) -> Dict[str, Any]:
        """Obtiene las credenciales de la base de datos desde Secrets Manager"""
        secrets_client = boto3.client('secretsmanager', region_name=self.region)
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response['SecretString'])
        return secret
    
    def _connect(self):
        """Establece conexión con PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.db_name,
                user=self.username,
                password=self.password
            )
            self.connection.autocommit = False
        except Exception as e:
            print(f"Error conectando a PostgreSQL: {str(e)}")
            raise
    
    def _setup_database(self):
        """Configura la base de datos con pgvector y crea las tablas necesarias"""
        try:
            with self.connection.cursor() as cursor:
                # Crear extensión pgvector si no existe
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Crear tabla para documentos con vectores
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id SERIAL PRIMARY KEY,
                        document_id VARCHAR(255) UNIQUE NOT NULL,
                        content TEXT NOT NULL,
                        embedding vector(1024),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Crear índice para búsqueda vectorial (HNSW es más rápido que IVFFlat)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                    ON documents USING hnsw (embedding vector_cosine_ops);
                """)
                
                # Crear índice para búsqueda por document_id
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS documents_document_id_idx 
                    ON documents (document_id);
                """)
                
                self.connection.commit()
                print("Base de datos configurada correctamente")
        except Exception as e:
            self.connection.rollback()
            print(f"Error configurando base de datos: {str(e)}")
            raise
    
    def index_document(
        self,
        document_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Indexa un documento con su embedding
        
        Args:
            document_id: ID único del documento
            content: Contenido del documento
            embedding: Vector de embedding
            metadata: Metadata adicional del documento
            
        Returns:
            True si se indexó correctamente
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO documents (document_id, content, embedding, metadata)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (document_id) 
                    DO UPDATE SET 
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP;
                """, (
                    document_id,
                    content,
                    embedding,
                    json.dumps(metadata) if metadata else None
                ))
                self.connection.commit()
                return True
        except Exception as e:
            self.connection.rollback()
            print(f"Error indexando documento: {str(e)}")
            return False
    
    def bulk_index_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> int:
        """
        Indexa múltiples documentos en batch
        
        Args:
            documents: Lista de documentos con keys: document_id, content, embedding, metadata
            
        Returns:
            Número de documentos indexados exitosamente
        """
        try:
            with self.connection.cursor() as cursor:
                values = [
                    (
                        doc['document_id'],
                        doc['content'],
                        doc['embedding'],
                        json.dumps(doc.get('metadata'))
                    )
                    for doc in documents
                ]
                
                execute_values(
                    cursor,
                    """
                    INSERT INTO documents (document_id, content, embedding, metadata)
                    VALUES %s
                    ON CONFLICT (document_id) 
                    DO UPDATE SET 
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    values
                )
                self.connection.commit()
                return len(documents)
        except Exception as e:
            self.connection.rollback()
            print(f"Error en bulk indexing: {str(e)}")
            return 0
    
    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos similares usando búsqueda vectorial
        
        Args:
            query_embedding: Vector de embedding de la consulta
            top_k: Número de resultados a retornar
            min_similarity: Similitud mínima (0-1)
            
        Returns:
            Lista de documentos con sus scores de similitud
        """
        try:
            with self.connection.cursor() as cursor:
                # Búsqueda por similitud coseno
                # 1 - (embedding <=> query) da un score de 0 a 1
                cursor.execute("""
                    SELECT 
                        document_id,
                        content,
                        metadata,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM documents
                    WHERE 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                """, (
                    query_embedding,
                    query_embedding,
                    min_similarity,
                    query_embedding,
                    top_k
                ))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'document_id': row[0],
                        'content': row[1],
                        'metadata': row[2],
                        'similarity': float(row[3])
                    })
                
                return results
        except Exception as e:
            print(f"Error en búsqueda: {str(e)}")
            return []
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un documento por su ID
        
        Args:
            document_id: ID del documento
            
        Returns:
            Documento o None si no existe
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT document_id, content, metadata, created_at, updated_at
                    FROM documents
                    WHERE document_id = %s;
                """, (document_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'document_id': row[0],
                        'content': row[1],
                        'metadata': row[2],
                        'created_at': row[3].isoformat() if row[3] else None,
                        'updated_at': row[4].isoformat() if row[4] else None
                    }
                return None
        except Exception as e:
            print(f"Error obteniendo documento: {str(e)}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """
        Elimina un documento por su ID
        
        Args:
            document_id: ID del documento
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM documents WHERE document_id = %s;
                """, (document_id,))
                self.connection.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            print(f"Error eliminando documento: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la base de datos
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM documents;")
                total_docs = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as docs_with_vectors
                    FROM documents 
                    WHERE embedding IS NOT NULL;
                """)
                docs_with_vectors = cursor.fetchone()[0]
                
                return {
                    'total_documents': total_docs,
                    'documents_with_vectors': docs_with_vectors,
                    'database_name': self.db_name
                }
        except Exception as e:
            print(f"Error obteniendo estadísticas: {str(e)}")
            return {}
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        """Context manager enter"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
