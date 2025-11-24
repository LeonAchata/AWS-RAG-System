"""
Text chunking utilities usando LangChain
"""
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Representa un fragmento de texto"""
    content: str
    start_char: int
    end_char: int
    chunk_index: int


def chunk_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    separator: str = "\n\n"
) -> List[TextChunk]:
    """
    Divide un texto en chunks usando RecursiveCharacterTextSplitter
    
    Args:
        text: Texto a dividir
        chunk_size: Tamaño aproximado de cada chunk en caracteres
        chunk_overlap: Superposición entre chunks
        separator: Separador principal para dividir
        
    Returns:
        Lista de TextChunk objects
    """
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        # Configurar el splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[separator, "\n", ". ", " ", ""],
            length_function=len
        )
        
        # Dividir el texto
        chunks = text_splitter.split_text(text)
        
        # Crear objetos TextChunk con información de posición
        result_chunks = []
        current_position = 0
        
        for i, chunk_content in enumerate(chunks):
            # Encontrar la posición del chunk en el texto original
            start_pos = text.find(chunk_content, current_position)
            if start_pos == -1:
                start_pos = current_position
            
            end_pos = start_pos + len(chunk_content)
            
            result_chunks.append(TextChunk(
                content=chunk_content,
                start_char=start_pos,
                end_char=end_pos,
                chunk_index=i
            ))
            
            current_position = end_pos
        
        return result_chunks
        
    except ImportError:
        # Fallback simple si LangChain no está disponible
        return simple_chunk_text(text, chunk_size, chunk_overlap)


def simple_chunk_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100
) -> List[TextChunk]:
    """
    División simple de texto sin dependencias externas
    Usado como fallback si LangChain no está disponible
    """
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Si no es el último chunk, intentar cortar en un espacio
        if end < len(text):
            # Buscar el último espacio antes del límite
            last_space = text.rfind(' ', start, end)
            if last_space > start:
                end = last_space
        
        chunk_content = text[start:end].strip()
        
        if chunk_content:
            chunks.append(TextChunk(
                content=chunk_content,
                start_char=start,
                end_char=end,
                chunk_index=chunk_index
            ))
            chunk_index += 1
        
        # Mover el inicio con overlap
        start = end - chunk_overlap if end < len(text) else end
    
    return chunks


def estimate_tokens(text: str) -> int:
    """
    Estima el número de tokens en un texto
    Aproximación: 1 token ≈ 4 caracteres
    
    Args:
        text: Texto a analizar
        
    Returns:
        Estimación del número de tokens
    """
    return len(text) // 4


def clean_text(text: str) -> str:
    """
    Limpia y normaliza un texto
    
    Args:
        text: Texto a limpiar
        
    Returns:
        Texto limpio
    """
    import re
    
    # Remover espacios en blanco excesivos
    text = re.sub(r'\s+', ' ', text)
    
    # Remover líneas vacías múltiples
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Trim
    text = text.strip()
    
    return text
