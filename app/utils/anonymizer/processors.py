"""Text processing functionality for anonymization and deanonymization."""

import logging
import re
import time
import uuid
from typing import Dict, Tuple, Any, List, Optional

# Local imports
from app.utils.anonymizer.store import entity_mapping_store
from app.utils.anonymizer.matchers import (
    fuzzy_match_custom_entities,
    create_entity_placeholder,
    should_skip_text
)

# Presidio imports
from presidio_analyzer import AnalyzerEngine

# Configure logging
logger = logging.getLogger(__name__)


def _load_profile_config(profiles: Dict[str, Any], profile_name: str, default_thresholds: Dict[str, float]) -> Dict[str, Any]:
    """Load and prepare profile configuration."""
    profile_thresholds = default_thresholds.copy()
    profile_custom_entities = {}
    fuzzy_match_enabled = False
    fuzzy_thresholds = {"DEFAULT": 80}
    skip_terms = []
    
    if profile_name in profiles:
        profile = profiles[profile_name]
        if "thresholds" in profile:
            profile_thresholds = {**default_thresholds, **profile["thresholds"]}
        if "custom_entities" in profile:
            profile_custom_entities = profile["custom_entities"]
        if "fuzzy_match" in profile:
            fuzzy_config = profile["fuzzy_match"]
            fuzzy_match_enabled = fuzzy_config.get("enabled", False)
            if "thresholds" in fuzzy_config:
                fuzzy_thresholds = fuzzy_config["thresholds"]
        if "skip_terms" in profile:
            skip_terms = profile["skip_terms"]
    
    return {
        "thresholds": profile_thresholds,
        "custom_entities": profile_custom_entities,
        "fuzzy_match_enabled": fuzzy_match_enabled,
        "fuzzy_thresholds": fuzzy_thresholds,
        "skip_terms": skip_terms
    }


def _process_custom_entities(text: str, custom_entities: Dict[str, List[str]], 
                            fuzzy_enabled: bool, fuzzy_thresholds: Dict[str, float]) -> Tuple[str, Dict[str, str]]:
    """Process custom entities with exact and fuzzy matching."""
    mappings = {}
    processed_text = text
    
    # Exact matches
    for entity_type, values in custom_entities.items():
        for value in values:
            if value in processed_text:
                placeholder, _ = create_entity_placeholder(entity_type)
                processed_text = processed_text.replace(value, placeholder)
                mappings[placeholder] = value
                logger.info(f"Custom entity match: {entity_type}: {value}")
    
    # Fuzzy matches if enabled
    if fuzzy_enabled:
        fuzzy_matches = fuzzy_match_custom_entities(
            processed_text, 
            custom_entities,
            fuzzy_thresholds
        )
        
        for entity_type, entity_value, score in fuzzy_matches:
            placeholder, _ = create_entity_placeholder(entity_type)
            processed_text = processed_text.replace(entity_value, placeholder)
            mappings[placeholder] = entity_value
            logger.info(f"Fuzzy match: {entity_type}: {entity_value} (score: {score:.1f}%)")
    
    return processed_text, mappings


def _process_with_presidio(text: str, analyzer: AnalyzerEngine, thresholds: Dict[str, float]) -> Tuple[str, Dict[str, str]]:
    """Process text with Presidio analyzer."""
    mappings = {}
    processed_text = text
    
    # Analyze with Presidio
    analyzer_results = analyzer.analyze(
        text=processed_text,
        language="en"
    )
    
    # Filter results based on entity-specific thresholds
    filtered_results = []
    for result in analyzer_results:
        entity_threshold = thresholds.get(
            result.entity_type, 
            thresholds["DEFAULT"]
        )
        if result.score >= entity_threshold:
            filtered_results.append(result)
    
    # Process Presidio results
    for item in filtered_results:
        entity_type = item.entity_type
        placeholder, _ = create_entity_placeholder(entity_type)
        original = processed_text[item.start:item.end]
        
        # Skip if already processed
        if original not in processed_text:
            continue
            
        # Replace in text
        processed_text = processed_text.replace(original, placeholder)
        mappings[placeholder] = original
        logger.info(f"Detected {entity_type}: {original} (score: {item.score:.2f})")
    
    return processed_text, mappings


def _extract_mapping_id_from_text(text: str) -> Optional[str]:
    """Extract mapping ID from text if present."""
    for store_mapping_id in entity_mapping_store.get_all().keys():
        if store_mapping_id in text:
            return store_mapping_id
    return None


def _replace_placeholders_from_all_mappings(text: str) -> str:
    """Replace placeholders using pattern matching and all available mappings."""
    processed_text = text
    
    # Generic pattern for placeholders
    placeholder_pattern = re.compile(r'<([A-Z_]+)_[0-9a-f]{8}>')
    
    for match in placeholder_pattern.finditer(processed_text):
        placeholder = match.group(0)
        entity_type = match.group(1)
        
        # Try to find replacement in all mappings
        replaced = False
        
        # Check exact placeholder matches
        for mapping in entity_mapping_store.get_all().values():
            if placeholder in mapping:
                processed_text = processed_text.replace(placeholder, mapping[placeholder])
                replaced = True
                break
        
        # If not replaced, try by entity type
        if not replaced:
            for mapping in entity_mapping_store.get_all().values():
                for p, original in mapping.items():
                    if f"<{entity_type}_" in p:
                        processed_text = processed_text.replace(placeholder, original)
                        replaced = True
                        break
                if replaced:
                    break
    
    return processed_text


def anonymize_text(text: str, analyzer: AnalyzerEngine, profiles: Dict[str, Any], 
                  default_thresholds: Dict[str, float], profile_name: str = "default") -> Tuple[str, Dict[str, str]]:
    """Anonymize text using profile configuration."""
    start_time = time.time()
    
    # Early returns for invalid or very short text
    if not text or not isinstance(text, str) or len(text) < 5:
        return text, {}
    
    # Load profile settings
    profile_config = _load_profile_config(profiles, profile_name, default_thresholds)
    
    # Skip processing for common non-PII data
    if should_skip_text(text, profile_config["skip_terms"]):
        return text, {}
    
    entity_mapping = {}
    processed_text = text
    
    # Process custom entities (exact and fuzzy matches)
    processed_text, custom_mappings = _process_custom_entities(
        processed_text, 
        profile_config["custom_entities"],
        profile_config["fuzzy_match_enabled"],
        profile_config["fuzzy_thresholds"]
    )
    entity_mapping.update(custom_mappings)
    
    # Process with Presidio
    processed_text, presidio_mappings = _process_with_presidio(
        processed_text,
        analyzer,
        profile_config["thresholds"]
    )
    entity_mapping.update(presidio_mappings)
    
    if entity_mapping:
        # Store mapping with a UUID for this request
        mapping_id = str(uuid.uuid4())
        entity_mapping_store.add(mapping_id, entity_mapping)
        
        processing_time = time.time() - start_time
        logger.info(f"Anonymization time: {processing_time:.4f}s, {len(entity_mapping)} entities found")
        
        return processed_text, {"mapping_id": mapping_id, "entities": entity_mapping}
    
    logger.info(f"No entities found. Time: {time.time() - start_time:.4f}s")
    return text, {}


def deanonymize_text(text: str) -> Tuple[str, Dict[str, str]]:
    """Deanonymize text by replacing placeholders with original values."""
    start_time = time.time()
    processed_text = text
    
    # Extract mapping ID if provided in metadata
    mapping_id = _extract_mapping_id_from_text(text)
    
    # First try with a specific mapping if available
    if mapping_id:
        mapping = entity_mapping_store.get(mapping_id)
        if mapping:
            for placeholder, original in mapping.items():
                if placeholder in processed_text:
                    processed_text = processed_text.replace(placeholder, original)
    
    # Generic pattern for placeholders
    processed_text = _replace_placeholders_from_all_mappings(processed_text)
    
    logger.info(f"Deanonymization completed in {time.time() - start_time:.4f}s")
    return processed_text, {} 