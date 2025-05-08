"""Storage mechanism for entity mappings."""

import time
from typing import Dict, Any, Optional

# Import configuration
from app.utils.anonymizer.config import config


class EntityMappingStore:
    """Store for entity mappings with cache management."""
    
    def __init__(self, max_cache_size=None):
        self.store = {}
        # Use the provided value or fall back to the config value
        self.max_cache_size = max_cache_size if max_cache_size is not None else config.mapping_store_max_size
        self.access_timestamps = {}
    
    def add(self, mapping_id: str, mapping: Dict[str, Any]) -> str:
        """Add a mapping to the store with cleanup if needed."""
        # Clean up if store is too large
        if len(self.store) >= self.max_cache_size:
            self._cleanup_oldest()
        
        self.store[mapping_id] = mapping
        self.access_timestamps[mapping_id] = time.time()
        return mapping_id
    
    def get(self, mapping_id: str) -> Optional[Dict[str, Any]]:
        """Get a mapping by ID and update its access timestamp."""
        if mapping_id in self.store:
            self.access_timestamps[mapping_id] = time.time()
            return self.store[mapping_id]
        return None
    
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Return all mappings (for searching placeholders)."""
        return self.store
    
    def _cleanup_oldest(self) -> None:
        """Remove the oldest accessed mapping when cache is full."""
        if not self.access_timestamps:
            return
        
        oldest_id = min(self.access_timestamps, key=self.access_timestamps.get)
        if oldest_id in self.store:
            del self.store[oldest_id]
        if oldest_id in self.access_timestamps:
            del self.access_timestamps[oldest_id]


# Global instance of the store
entity_mapping_store = EntityMappingStore() 