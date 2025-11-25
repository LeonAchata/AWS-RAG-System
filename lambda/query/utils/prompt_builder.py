"""
Utilidades para construcción de prompts y generación de respuestas
"""
from typing import List, Dict, Any, Optional


def build_rag_prompt(
    query: str,
    documents: List[Dict[str, Any]]
) -> str:
    """
    Construye el prompt para el modelo LLM incluyendo contexto recuperado
    
    Args:
        query: Pregunta del usuario
        documents: Lista de documentos relevantes de PostgreSQL
        
    Returns:
        Prompt completo para el LLM
    """
    # Construir contexto a partir de los documentos
    context_parts = []
    for i, doc in enumerate(documents, 1):
        metadata = doc.get('metadata', {})
        filename = metadata.get('filename', 'documento desconocido') if metadata else 'documento'
        content = doc.get('content', '')
        similarity = doc.get('similarity', 0)
        
        context_parts.append(
            f"[Fuente {i}: {filename} (similitud: {similarity:.2f})]\n{content}\n"
        )
    
    context_text = "\n---\n".join(context_parts)
    
    # Prompt completo
    prompt = f"""Eres un asistente experto que responde preguntas basándose únicamente en el contexto proporcionado.

Instrucciones:
1. Responde SOLO basándote en la información del contexto proporcionado
2. Si la información no está en el contexto, di claramente "No tengo información suficiente para responder esa pregunta"
3. Sé conciso pero completo en tus respuestas
4. Si citas información, menciona de qué documento proviene
5. Mantén un tono profesional y claro
6. No inventes información que no esté en el contexto

Contexto de documentos relevantes:

{context_text}

---

Pregunta del usuario: {query}

Por favor, responde la pregunta basándote únicamente en el contexto proporcionado arriba."""

    return prompt


def build_conversational_prompt(
    query: str,
    context_chunks: List[Dict[str, Any]],
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> tuple[str, str]:
    """
    Construye un prompt conversacional con historial
    
    Args:
        query: Pregunta actual del usuario
        context_chunks: Chunks relevantes recuperados
        conversation_history: Historial de conversación previa
        
    Returns:
        Tupla de (system_prompt, user_prompt)
    """
    system_prompt = """Eres un asistente conversacional experto. Mantén una conversación natural 
mientras respondes basándote en el contexto de documentos proporcionado.

Características de tus respuestas:
- Natural y conversacional
- Basadas en el contexto proporcionado
- Considera el historial de la conversación
- Admite cuando no tienes información suficiente
- Mantén coherencia con respuestas anteriores"""

    # Construir contexto
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        metadata = chunk.get('metadata', {})
        filename = metadata.get('filename', 'documento')
        content = chunk.get('content', '')
        context_parts.append(f"[Documento {i}: {filename}]\n{content}")
    
    context_text = "\n\n".join(context_parts)
    
    # Construir historial si existe
    history_text = ""
    if conversation_history:
        history_parts = []
        for msg in conversation_history[-5:]:  # Últimos 5 mensajes
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            history_parts.append(f"{role.upper()}: {content}")
        history_text = "\n".join(history_parts)
        history_text = f"\n\nHistorial de conversación:\n{history_text}\n"
    
    user_prompt = f"""Contexto relevante:
{context_text}
{history_text}
Usuario: {query}

Asistente:"""

    return system_prompt, user_prompt


def extract_keywords(query: str) -> List[str]:
    """
    Extrae palabras clave de una consulta (implementación simple)
    
    Args:
        query: Consulta del usuario
        
    Returns:
        Lista de palabras clave
    """
    import re
    
    # Palabras comunes a ignorar (stopwords español)
    stopwords = {
        'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no',
        'haber', 'por', 'con', 'su', 'para', 'como', 'estar', 'tener',
        'le', 'lo', 'todo', 'pero', 'más', 'hacer', 'o', 'poder', 'decir',
        'este', 'ir', 'otro', 'ese', 'la', 'si', 'me', 'ya', 'ver', 'porque',
        'dar', 'cuando', 'él', 'muy', 'sin', 'vez', 'mucho', 'saber', 'qué',
        'sobre', 'mi', 'alguno', 'mismo', 'yo', 'también', 'hasta', 'año',
        'dos', 'querer', 'entre', 'así', 'primero', 'desde', 'grande', 'eso',
        'ni', 'nos', 'llegar', 'pasar', 'tiempo', 'ella', 'sí', 'día', 'uno',
        'bien', 'poco', 'deber', 'entonces', 'poner', 'cosa', 'tanto', 'hombre',
        'parecer', 'nuestro', 'tan', 'donde', 'ahora', 'parte', 'después', 'vida',
        'es', 'del', 'los', 'las', 'una', 'al', 'son', 'cómo', 'cuál', 'cuáles'
    }
    
    # Limpiar y tokenizar
    query = query.lower()
    words = re.findall(r'\b\w+\b', query)
    
    # Filtrar stopwords y palabras muy cortas
    keywords = [
        word for word in words 
        if word not in stopwords and len(word) > 3
    ]
    
    return keywords


def format_response_with_sources(
    response_text: str,
    documents: List[Dict[str, Any]],
    include_sources: bool = True
) -> Dict[str, Any]:
    """
    Formatea la respuesta incluyendo las fuentes
    
    Args:
        response_text: Respuesta generada por el LLM
        documents: Lista de documentos de PostgreSQL
        include_sources: Si incluir fuentes en la respuesta
        
    Returns:
        Respuesta formateada con fuentes
    """
    result = {
        'answer': response_text,
        'num_sources': len(documents)
    }
    
    if include_sources:
        # Procesar fuentes únicas
        sources = []
        for doc in documents:
            metadata = doc.get('metadata', {}) or {}
            sources.append({
                'document_id': doc.get('document_id'),
                'filename': metadata.get('filename', 'Desconocido'),
                'similarity': doc.get('similarity', 0)
            })
        
        result['sources'] = sources
        result['confidence'] = documents[0].get('similarity', 0) if documents else 0.0
    
    return result


def calculate_response_confidence(
    similarity_scores: List[float],
    num_chunks: int
) -> Dict[str, Any]:
    """
    Calcula métricas de confianza de la respuesta
    
    Args:
        similarity_scores: Scores de similitud de chunks recuperados
        num_chunks: Número de chunks recuperados
        
    Returns:
        Métricas de confianza
    """
    if not similarity_scores:
        return {
            'confidence': 'low',
            'avg_similarity': 0.0,
            'max_similarity': 0.0
        }
    
    avg_score = sum(similarity_scores) / len(similarity_scores)
    max_score = max(similarity_scores)
    
    # Determinar nivel de confianza
    if max_score >= 0.85 and avg_score >= 0.75:
        confidence = 'high'
    elif max_score >= 0.70 and avg_score >= 0.60:
        confidence = 'medium'
    else:
        confidence = 'low'
    
    return {
        'confidence': confidence,
        'avg_similarity': round(avg_score, 3),
        'max_similarity': round(max_score, 3),
        'chunks_retrieved': num_chunks
    }


def sanitize_query(query: str, max_length: int = 1000) -> str:
    """
    Sanitiza y valida una consulta del usuario
    
    Args:
        query: Consulta original
        max_length: Longitud máxima permitida
        
    Returns:
        Consulta sanitizada
    """
    # Remover espacios excesivos
    query = ' '.join(query.split())
    
    # Truncar si es muy largo
    if len(query) > max_length:
        query = query[:max_length]
    
    # Validar que no esté vacío
    if not query.strip():
        raise ValueError("La consulta no puede estar vacía")
    
    return query.strip()
