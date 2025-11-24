"""
Cliente para Amazon Bedrock - Embeddings y LLM
"""
import json
import boto3
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError


class BedrockClient:
    """Cliente para interactuar con Amazon Bedrock"""
    
    def __init__(self, region_name: str = "us-east-1"):
        """
        Inicializa el cliente de Bedrock
        
        Args:
            region_name: Región de AWS donde está habilitado Bedrock
        """
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        self.region_name = region_name
        
    def generate_embeddings(
        self, 
        text: str, 
        model_id: str = "amazon.titan-embed-text-v2:0"
    ) -> List[float]:
        """
        Genera embeddings para un texto usando Titan Embeddings
        
        Args:
            text: Texto a convertir en embedding
            model_id: ID del modelo de embeddings
            
        Returns:
            Lista de floats representando el vector de embedding
        """
        try:
            # Preparar el cuerpo de la solicitud
            body = json.dumps({
                "inputText": text
            })
            
            # Invocar el modelo
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=body,
                contentType='application/json',
                accept='application/json'
            )
            
            # Parsear respuesta
            response_body = json.loads(response['body'].read())
            embedding = response_body.get('embedding', [])
            
            return embedding
            
        except ClientError as e:
            print(f"Error generando embeddings: {e}")
            raise
        except Exception as e:
            print(f"Error inesperado: {e}")
            raise
    
    def generate_embeddings_batch(
        self, 
        texts: List[str], 
        model_id: str = "amazon.titan-embed-text-v2:0"
    ) -> List[List[float]]:
        """
        Genera embeddings para múltiples textos
        
        Args:
            texts: Lista de textos
            model_id: ID del modelo de embeddings
            
        Returns:
            Lista de vectores de embeddings
        """
        embeddings = []
        for text in texts:
            embedding = self.generate_embeddings(text, model_id)
            embeddings.append(embedding)
        return embeddings
    
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> str:
        """
        Genera una respuesta usando Claude (para el Lambda de Query)
        
        Args:
            prompt: Prompt del usuario
            system_prompt: Instrucciones del sistema
            model_id: ID del modelo LLM
            temperature: Control de aleatoriedad (0-1)
            max_tokens: Máximo de tokens en la respuesta
            
        Returns:
            Respuesta generada por el modelo
        """
        try:
            # Construir mensajes
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Preparar el cuerpo de la solicitud
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature
            }
            
            # Añadir system prompt si existe
            if system_prompt:
                body["system"] = system_prompt
            
            # Invocar el modelo
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parsear respuesta
            response_body = json.loads(response['body'].read())
            
            # Extraer el texto de la respuesta
            content = response_body.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            
            return ""
            
        except ClientError as e:
            print(f"Error generando respuesta: {e}")
            raise
        except Exception as e:
            print(f"Error inesperado: {e}")
            raise


# Instancia global para reutilización en Lambda
_bedrock_client = None


def get_bedrock_client(region_name: str = "us-east-1") -> BedrockClient:
    """
    Obtiene una instancia singleton del cliente de Bedrock
    Útil para reutilizar conexiones en Lambda
    """
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient(region_name)
    return _bedrock_client
