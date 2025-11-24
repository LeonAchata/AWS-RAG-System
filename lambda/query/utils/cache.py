"""
Utilidades para caché de resultados y optimización
"""
import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


class SimpleCache:
    """
    Caché en memoria simple para queries frecuentes
    Útil para reducir costos de Bedrock en queries repetidas
    """
    
    def __init__(self, max_size: int = 100, ttl_minutes: int = 60):
        """
        Inicializa el caché
        
        Args:
            max_size: Número máximo de elementos en caché
            ttl_minutes: Tiempo de vida en minutos
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def _generate_key(self, query: str, filters: Optional[Dict] = None) -> str:
        """Genera una clave única para una consulta"""
        data = f"{query}:{json.dumps(filters or {}, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, query: str, filters: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene un resultado del caché si existe y no ha expirado
        
        Args:
            query: Consulta del usuario
            filters: Filtros aplicados
            
        Returns:
            Resultado cacheado o None
        """
        key = self._generate_key(query, filters)
        
        if key in self.cache:
            entry = self.cache[key]
            
            # Verificar expiración
            if datetime.now() - entry['timestamp'] < self.ttl:
                entry['hits'] += 1
                return entry['data']
            else:
                # Eliminar entrada expirada
                del self.cache[key]
        
        return None
    
    def set(self, query: str, data: Dict[str, Any], filters: Optional[Dict] = None):
        """
        Guarda un resultado en el caché
        
        Args:
            query: Consulta del usuario
            data: Datos a cachear
            filters: Filtros aplicados
        """
        key = self._generate_key(query, filters)
        
        # Si el caché está lleno, eliminar el elemento menos usado
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now(),
            'hits': 0
        }
    
    def _evict_lru(self):
        """Elimina el elemento menos recientemente usado"""
        if not self.cache:
            return
        
        # Encontrar el elemento con menos hits
        lru_key = min(self.cache.items(), key=lambda x: x[1]['hits'])[0]
        del self.cache[lru_key]
    
    def clear(self):
        """Limpia todo el caché"""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché"""
        total_hits = sum(entry['hits'] for entry in self.cache.values())
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'total_hits': total_hits,
            'ttl_minutes': self.ttl.total_seconds() / 60
        }


# Instancia global del caché (persistente durante la vida del contenedor Lambda)
_query_cache = SimpleCache(max_size=100, ttl_minutes=30)


def get_cache() -> SimpleCache:
    """Obtiene la instancia del caché"""
    return _query_cache


def should_use_cache(query: str) -> bool:
    """
    Determina si una consulta debería usar caché
    
    Args:
        query: Consulta del usuario
        
    Returns:
        True si debería usar caché
    """
    # No cachear queries muy cortas o comandos especiales
    if len(query) < 10:
        return False
    
    # No cachear queries con instrucciones temporales
    temporal_keywords = ['hoy', 'ahora', 'actual', 'último', 'reciente']
    query_lower = query.lower()
    
    for keyword in temporal_keywords:
        if keyword in query_lower:
            return False
    
    return True
