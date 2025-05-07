import json
import logging
import uuid
import re
import time
from typing import Dict, Tuple, Any, List

# Presidio imports
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Import for fuzzy matching
from rapidfuzz import fuzz

# Local imports
from app.utils.anonymizer.profiles import load_profiles
from app.utils.anonymizer.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Simple cache to store entity mappings
entity_mapping_store = {}

# Entity-specific thresholds - these will be default if no profile is specified
DEFAULT_ENTITY_THRESHOLDS = {
    "PERSON": 0.85,
    "EMAIL_ADDRESS": 0.75,
    "PHONE_NUMBER": 0.75,
    "LOCATION": 0.90, 
    "DATE_TIME": 0.95,
    "NRP": 0.85,
    "IP_ADDRESS": 0.75,
    "DOMAIN_NAME": 0.80,
    "URL": 0.80,
    "DEFAULT": 0.85
}

# Initialize Presidio analyzer engine
def get_analyzer_engine():
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]
    })
    nlp_engine = provider.create_engine()
    registry = RecognizerRegistry()
    return AnalyzerEngine(
        nlp_engine=nlp_engine,
        registry=registry,
        supported_languages=["en"]
    )

# Initialize engines
analyzer = get_analyzer_engine()
anonymizer = AnonymizerEngine()
profiles = load_profiles()
logger.info("Presidio engines and profiles initialized")

def fuzzy_match_custom_entities(text: str, custom_entities: Dict[str, List[str]], 
                              fuzzy_thresholds: Dict[str, int]) -> List[Tuple[str, str, float]]:
    """Perform fuzzy matching on text with custom entities."""
    if not text:
        return []
    
    matches = []
    default_threshold = fuzzy_thresholds.get("DEFAULT", 80)
    
    # Tokenize text into words and phrases
    words = text.split()
    phrases = []
    for i in range(len(words)):
        for j in range(i+1, min(i+6, len(words)+1)):  # Match phrases up to 5 words
            phrase = " ".join(words[i:j])
            if len(phrase) > 3:  # Only consider phrases longer than 3 chars
                phrases.append(phrase)
    
    for entity_type, entities in custom_entities.items():
        threshold = fuzzy_thresholds.get(entity_type, default_threshold)
        
        for entity in entities:
            # Skip very short entities
            if len(entity) < 4:
                continue
                
            # First check if the entity appears directly in the text (much faster)
            if entity in text:
                matches.append((entity_type, entity, 100))
                continue
            
            # Try fuzzy matching against phrases
            for phrase in phrases:
                ratio = fuzz.ratio(entity.lower(), phrase.lower())
                if ratio >= threshold:
                    logger.info(f"Fuzzy match: {phrase} -> {entity} ({ratio}%)")
                    matches.append((entity_type, entity, ratio))
                    break
    
    return matches

def _process_text(text: str, is_anonymize: bool, profile_name: str = "default") -> Tuple[str, Dict[str, str]]:
    """Process text content to anonymize or deanonymize PII."""
    start_time = time.time()
    
    if not text or not isinstance(text, str) or len(text) < 5:
        return text, {}
    
    # Get profile configuration
    profile_thresholds = DEFAULT_ENTITY_THRESHOLDS
    profile_custom_entities = {}
    fuzzy_match_enabled = False
    fuzzy_thresholds = {"DEFAULT": 80}
    skip_terms = []
    
    if profile_name in profiles:
        profile = profiles[profile_name]
        if "thresholds" in profile:
            profile_thresholds = {**DEFAULT_ENTITY_THRESHOLDS, **profile["thresholds"]}
        if "custom_entities" in profile:
            profile_custom_entities = profile["custom_entities"]
        if "fuzzy_match" in profile:
            fuzzy_config = profile["fuzzy_match"]
            fuzzy_match_enabled = fuzzy_config.get("enabled", False)
            if "thresholds" in fuzzy_config:
                fuzzy_thresholds = fuzzy_config["thresholds"]
        if "skip_terms" in profile:
            skip_terms = profile["skip_terms"]
    
    # Skip processing for common non-PII data
    if text.lower() in skip_terms or (len(text) == 36 and text.count("-") == 4):  # Skip UUIDs
        return text, {}
    
    if is_anonymize:
        entity_mapping = {}
        processed_text = text
        
        # 1. Check for custom entities if provided
        if profile_custom_entities:
            # Exact matches first
            for entity_type, values in profile_custom_entities.items():
                for value in values:
                    if value in processed_text:
                        entity_id = str(uuid.uuid4())[:8]
                        placeholder = f"<{entity_type}_{entity_id}>"
                        processed_text = processed_text.replace(value, placeholder)
                        entity_mapping[placeholder] = value
                        logger.info(f"Custom entity match: {entity_type}: {value}")
            
            # Fuzzy matches if enabled
            if fuzzy_match_enabled:
                fuzzy_matches = fuzzy_match_custom_entities(
                    processed_text, 
                    profile_custom_entities,
                    fuzzy_thresholds
                )
                
                for entity_type, entity_value, score in fuzzy_matches:
                    entity_id = str(uuid.uuid4())[:8]
                    placeholder = f"<{entity_type}_{entity_id}>"
                    processed_text = processed_text.replace(entity_value, placeholder)
                    entity_mapping[placeholder] = entity_value
                    logger.info(f"Fuzzy match: {entity_type}: {entity_value} (score: {score:.1f}%)")
        
        # 2. Use Presidio for entity detection
        analyzer_results = analyzer.analyze(
            text=processed_text,
            language="en"
        )
        
        # Filter results based on entity-specific thresholds
        filtered_results = []
        for result in analyzer_results:
            entity_threshold = profile_thresholds.get(
                result.entity_type, 
                profile_thresholds["DEFAULT"]
            )
            if result.score >= entity_threshold:
                filtered_results.append(result)
        
        # Process Presidio results
        for item in filtered_results:
            entity_type = item.entity_type
            entity_id = str(uuid.uuid4())[:8]
            placeholder = f"<{entity_type}_{entity_id}>"
            original = processed_text[item.start:item.end]
            
            # Skip if already processed
            if original not in processed_text:
                continue
                
            # Replace in text
            processed_text = processed_text.replace(original, placeholder)
            entity_mapping[placeholder] = original
            logger.info(f"Detected {entity_type}: {original} (score: {item.score:.2f})")
        
        if entity_mapping:
            # Store mapping with a UUID for this request
            mapping_id = str(uuid.uuid4())
            entity_mapping_store[mapping_id] = entity_mapping
            
            processing_time = time.time() - start_time
            logger.info(f"Anonymization time: {processing_time:.4f}s, {len(entity_mapping)} entities found")
            
            return processed_text, {"mapping_id": mapping_id, "entities": entity_mapping}
        
        logger.info(f"No entities found. Time: {time.time() - start_time:.4f}s")
        return text, {}
    
    else:
        # Deanonymizing - replace placeholders with original values
        processed_text = text
        
        # Extract mapping ID if provided in metadata
        mapping_id = None
        for store_mapping_id in entity_mapping_store.keys():
            if store_mapping_id in text:
                mapping_id = store_mapping_id
                break
                
        # First try with a specific mapping if available
        if mapping_id and mapping_id in entity_mapping_store:
            mapping = entity_mapping_store[mapping_id]
            for placeholder, original in mapping.items():
                if placeholder in processed_text:
                    processed_text = processed_text.replace(placeholder, original)
        
        # Generic pattern for placeholders
        placeholder_pattern = re.compile(r'<([A-Z_]+)_[0-9a-f]{8}>')
        for match in placeholder_pattern.finditer(processed_text):
            placeholder = match.group(0)
            
            # Try all mappings to find a replacement
            replaced = False
            for mapping in entity_mapping_store.values():
                if placeholder in mapping:
                    original = mapping[placeholder]
                    processed_text = processed_text.replace(placeholder, original)
                    replaced = True
                    break
            
            if not replaced:
                # Handle pattern like <TYPE_{uuid}> 
                entity_type = match.group(1)
                for mapping in entity_mapping_store.values():
                    for p, original in mapping.items():
                        if f"<{entity_type}_" in p:
                            processed_text = processed_text.replace(placeholder, original)
                            replaced = True
                            break
                    if replaced:
                        break
        
        logger.info(f"Deanonymization completed in {time.time() - start_time:.4f}s")
        return processed_text, {}

def _recursive_process(data: Any, is_anonymize: bool, profile_name: str = "default", path: str = "") -> Tuple[Any, Dict[str, Dict[str, str]]]:
    """Recursively process data structure to anonymize or deanonymize text."""
    all_mappings = {}
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            processed_value, mappings = _recursive_process(value, is_anonymize, profile_name, current_path)
            result[key] = processed_value
            all_mappings.update(mappings)
        return result, all_mappings
    
    elif isinstance(data, list):
        result = []
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]"
            
            # Skip processing system messages
            if path == "messages" and isinstance(item, dict) and item.get("role") == "system":
                result.append(item)
                continue
                
            processed_item, mappings = _recursive_process(item, is_anonymize, profile_name, current_path)
            result.append(processed_item)
            all_mappings.update(mappings)
        return result, all_mappings
    
    elif isinstance(data, str):
        processed_text, mapping = _process_text(data, is_anonymize, profile_name)
        if mapping:
            all_mappings[path] = mapping
        return processed_text, all_mappings
    
    else:
        # Return unchanged for other data types
        return data, all_mappings

def anonymize_data(data: Dict[str, Any], profile_name: str = None) -> Tuple[Dict[str, Any], Dict[str, Dict[str, str]]]:
    """Anonymize sensitive information in the provided data."""
    # Use provided profile or the default from config
    profile = profile_name or config.default_profile
    
    total_start_time = time.time()
    logger.info(f"Starting anonymization with profile: {profile}")
    
    # Process each part of the data structure
    anonymized_data, entity_mappings = _recursive_process(data, is_anonymize=True, profile_name=profile)
    
    # Generate a global mapping ID for this request
    global_mapping_id = str(uuid.uuid4())
    entity_mapping_store[global_mapping_id] = entity_mappings
    
    # Add mapping ID to metadata for use during deanonymization
    if "metadata" not in anonymized_data:
        anonymized_data["metadata"] = {}
    anonymized_data["metadata"]["privacy_mapping_id"] = global_mapping_id
    
    # Log mapping summary
    mapping_count = sum(1 for m in entity_mappings.values() if m)
    logger.info(f"Anonymization complete: {mapping_count} mappings, {time.time() - total_start_time:.4f}s total")
    
    return anonymized_data, entity_mappings

def deanonymize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Deanonymize data that was previously anonymized."""
    total_start_time = time.time()
    logger.info("Starting deanonymization")
    
    # Extract mapping ID if present
    mapping_id = None
    if "metadata" in data and "privacy_mapping_id" in data["metadata"]:
        mapping_id = data["metadata"]["privacy_mapping_id"]
        logger.info(f"Found mapping ID: {mapping_id}")
    
    # Process the data to restore original values
    deanonymized_data, _ = _recursive_process(data, is_anonymize=False)
    
    # Remove the mapping ID from the response after processing is complete
    if "metadata" in deanonymized_data and "privacy_mapping_id" in deanonymized_data["metadata"]:
        del deanonymized_data["metadata"]["privacy_mapping_id"]
    
    logger.info(f"Deanonymization complete: {time.time() - total_start_time:.4f}s total")
    return deanonymized_data 