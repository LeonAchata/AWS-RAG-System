"""
Procesadores de documentos para diferentes formatos
"""
import io
from typing import Optional, Dict, Any
from pathlib import Path


class DocumentProcessor:
    """Clase base para procesadores de documentos"""
    
    @staticmethod
    def extract_text(file_content: bytes, file_extension: str) -> str:
        """
        Extrae texto de un documento según su tipo
        
        Args:
            file_content: Contenido del archivo en bytes
            file_extension: Extensión del archivo (.pdf, .docx, etc.)
            
        Returns:
            Texto extraído del documento
        """
        extension = file_extension.lower().lstrip('.')
        
        if extension == 'pdf':
            return PDFProcessor.extract_text(file_content)
        elif extension == 'docx':
            return DocxProcessor.extract_text(file_content)
        elif extension in ['txt', 'md']:
            return TextProcessor.extract_text(file_content)
        elif extension in ['html', 'htm']:
            return HTMLProcessor.extract_text(file_content)
        else:
            raise ValueError(f"Formato de archivo no soportado: {extension}")


class PDFProcessor:
    """Procesador para archivos PDF"""
    
    @staticmethod
    def extract_text(file_content: bytes) -> str:
        """Extrae texto de un PDF"""
        try:
            import PyPDF2
            
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n\n".join(text_parts)
            
        except ImportError:
            # Fallback a pdfplumber si PyPDF2 no está disponible
            try:
                import pdfplumber
                
                pdf_file = io.BytesIO(file_content)
                text_parts = []
                
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                
                return "\n\n".join(text_parts)
                
            except ImportError:
                raise ImportError("Se requiere PyPDF2 o pdfplumber para procesar PDFs")
        except Exception as e:
            raise Exception(f"Error procesando PDF: {str(e)}")


class DocxProcessor:
    """Procesador para archivos Word (.docx)"""
    
    @staticmethod
    def extract_text(file_content: bytes) -> str:
        """Extrae texto de un archivo Word"""
        try:
            from docx import Document
            
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            return "\n\n".join(text_parts)
            
        except ImportError:
            raise ImportError("Se requiere python-docx para procesar archivos Word")
        except Exception as e:
            raise Exception(f"Error procesando DOCX: {str(e)}")


class TextProcessor:
    """Procesador para archivos de texto plano"""
    
    @staticmethod
    def extract_text(file_content: bytes) -> str:
        """Extrae texto de un archivo de texto plano"""
        try:
            # Intentar diferentes encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    return file_content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            
            raise ValueError("No se pudo decodificar el archivo con los encodings disponibles")
            
        except Exception as e:
            raise Exception(f"Error procesando archivo de texto: {str(e)}")


class HTMLProcessor:
    """Procesador para archivos HTML"""
    
    @staticmethod
    def extract_text(file_content: bytes) -> str:
        """Extrae texto de un archivo HTML"""
        try:
            from bs4 import BeautifulSoup
            
            html_content = file_content.decode('utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remover scripts y estilos
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Obtener texto
            text = soup.get_text()
            
            # Limpiar espacios en blanco excesivos
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except ImportError:
            raise ImportError("Se requiere beautifulsoup4 para procesar archivos HTML")
        except Exception as e:
            raise Exception(f"Error procesando HTML: {str(e)}")


def get_metadata_from_file(
    filename: str,
    file_size: int,
    file_content: bytes,
    file_extension: str
) -> Dict[str, Any]:
    """
    Extrae metadatos básicos de un archivo
    
    Args:
        filename: Nombre del archivo
        file_size: Tamaño en bytes
        file_content: Contenido del archivo
        file_extension: Extensión del archivo
        
    Returns:
        Diccionario con metadatos
    """
    metadata = {
        "filename": filename,
        "file_size": file_size,
        "file_extension": file_extension
    }
    
    # Metadatos específicos para PDFs
    if file_extension.lower() == '.pdf':
        try:
            import PyPDF2
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            metadata["page_count"] = len(pdf_reader.pages)
            
            if pdf_reader.metadata:
                metadata["title"] = pdf_reader.metadata.get('/Title', filename)
                metadata["author"] = pdf_reader.metadata.get('/Author')
                metadata["subject"] = pdf_reader.metadata.get('/Subject')
                metadata["creator"] = pdf_reader.metadata.get('/Creator')
        except:
            pass
    
    return metadata
