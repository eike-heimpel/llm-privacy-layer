"""Entity matching functionality for anonymization."""

import logging
import uuid
from typing import Dict, List, Tuple, Any

# Import for fuzzy matching
from rapidfuzz import fuzz

# Import configuration
from app.utils.anonymizer.config import config

# Configure logging
logger = logging.getLogger(__name__)


def _extract_phrases_from_text(text: str) -> List[str]:
    """Extract phrases from text for matching."""
    words = text.split()
    phrases = []
    
    for i in range(len(words)):
        for j in range(i+1, min(i+config.max_phrase_words+1, len(words)+1)):
            phrase = " ".join(words[i:j])
            if len(phrase) > config.min_entity_length:
                phrases.append(phrase)
                
    return phrases


def _find_fuzzy_matches(entity: str, phrases: List[str], entity_type: str, threshold: float) -> List[Tuple[str, str, float]]:
    """Find fuzzy matches for an entity in a list of phrases."""
    matches = []
    
    for phrase in phrases:
        ratio = fuzz.ratio(entity.lower(), phrase.lower())
        if ratio >= threshold:
            logger.info(f"Fuzzy match: {phrase} -> {entity} ({ratio}%)")
            matches.append((entity_type, entity, ratio))
            break
            
    return matches


def fuzzy_match_custom_entities(text: str, custom_entities: Dict[str, List[str]], 
                              fuzzy_thresholds: Dict[str, int]) -> List[Tuple[str, str, float]]:
    """Perform fuzzy matching on text with custom entities."""
    if not text:
        return []
    
    matches = []
    default_threshold = fuzzy_thresholds.get("DEFAULT", 80)
    
    # Extract phrases function to reduce nesting
    phrases = _extract_phrases_from_text(text)
    
    for entity_type, entities in custom_entities.items():
        threshold = fuzzy_thresholds.get(entity_type, default_threshold)
        
        for entity in entities:
            # Skip very short entities - using config value
            if len(entity) < config.min_entity_length:
                continue
                
            # Check exact match first
            if entity in text:
                matches.append((entity_type, entity, 100))
                continue
            
            # Find fuzzy matches
            entity_matches = _find_fuzzy_matches(entity, phrases, entity_type, threshold)
            matches.extend(entity_matches)
    
    return matches


def create_entity_placeholder(entity_type: str) -> Tuple[str, str]:
    """Create a placeholder for an entity with a unique ID."""
    entity_id = str(uuid.uuid4())[:8]
    placeholder = f"<{entity_type}_{entity_id}>"
    return placeholder, entity_id


def should_skip_text(text: str, skip_terms: List[str]) -> bool:
    """Determine if processing should be skipped for this text."""
    # Skip terms explicitly listed in profile
    if text.lower() in skip_terms:
        return True
        
    # Skip UUIDs - using config values
    if (len(text) == config.uuid_length and 
        text.count("-") == config.uuid_dash_count):
        return True
        
    return False 