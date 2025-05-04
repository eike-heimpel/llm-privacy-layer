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

# Configure logging with better formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Simple cache to store entity mappings
entity_mapping_store = {}

# Initialize Presidio with minimal configuration
def get_analyzer_engine():
    # Create NLP engine
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]
    })
    nlp_engine = provider.create_engine()
    
    # Create registry with the default recognizers
    registry = RecognizerRegistry()
    return AnalyzerEngine(
        nlp_engine=nlp_engine,
        registry=registry,
        supported_languages=["en"]
    )

# Initialize engines once
try:
    analyzer = get_analyzer_engine()
    anonymizer = AnonymizerEngine()
    logger.info("Presidio engines initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Presidio engines: {e}")
    analyzer = None
    anonymizer = None

def _process_text(text: str, is_anonymize: bool) -> Tuple[str, Dict[str, str]]:
    """
    Process text content to anonymize or deanonymize PII.
    
    Args:
        text: The text to process
        is_anonymize: If True, anonymize. If False, deanonymize.
        
    Returns:
        Tuple of (processed_text, entity_mapping)
    """
    # Start timing
    start_time = time.time()
    
    if not text or not isinstance(text, str):
        return text, {}
    
    # Skip very short texts that can't contain much PII
    if len(text) < 5:
        return text, {}
    
    # Skip processing for common non-PII data
    skip_terms = [
        "en", "de", "en-US", "en-GB", "de-DE", "user", "assistant", "system",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "january", "february", "march", "april", "may", "june", "july", 
        "august", "september", "october", "november", "december"
    ]
    if text.lower() in skip_terms or (len(text) == 36 and text.count("-") == 4):  # Skip UUIDs
        return text, {}
    
    if is_anonymize:
        entity_mapping = {}
        processed_text = text
        
        # Using only Presidio for entity detection
        if analyzer and len(processed_text) > 5:  # Analyze text of reasonable length
            try:
                # Log timing before Presidio analysis
                presidio_start = time.time()
                logger.info(f"Starting Presidio analysis")
                
                # Use Presidio to identify PII - include all built-in entity types
                analyzer_results = analyzer.analyze(
                    text=processed_text,
                    language="en",
                    score_threshold=0.75  # Increased threshold to reduce false positives
                )
                
                presidio_analyze_time = time.time() - presidio_start
                logger.info(f"Presidio analysis completed in {presidio_analyze_time:.4f} seconds")
                
                if analyzer_results and len(analyzer_results) > 0:
                    # Create proper operator config for Presidio
                    operators = {
                        "PERSON": OperatorConfig("replace", ""),
                        "EMAIL_ADDRESS": OperatorConfig("replace", ""),
                        "PHONE_NUMBER": OperatorConfig("replace", ""),
                        "LOCATION": OperatorConfig("replace", ""),
                        "NRP": OperatorConfig("replace", ""),
                        "IP_ADDRESS": OperatorConfig("replace", ""),
                        "DOMAIN_NAME": OperatorConfig("replace", ""),
                        "URL": OperatorConfig("replace", "")
                    }
                    
                    # Process Presidio results
                    for item in analyzer_results:
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
                        logger.info(f"Presidio found {entity_type}: {original} (score: {item.score:.2f})")
            except Exception as e:
                logger.warning(f"Presidio processing error: {e}")
        
        if entity_mapping:
            # Store mapping with a UUID for this request
            mapping_id = str(uuid.uuid4())
            logger.info(f"Created {len(entity_mapping)} mappings with ID: {mapping_id}")
            entity_mapping_store[mapping_id] = entity_mapping
            
            # Log total processing time
            processing_time = time.time() - start_time
            logger.info(f"Total anonymization processing time: {processing_time:.4f} seconds")
            
            return processed_text, {"mapping_id": mapping_id, "entities": entity_mapping}
        
        processing_time = time.time() - start_time
        logger.info(f"No entities found. Processing completed in {processing_time:.4f} seconds")
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
                    logger.info(f"Replacing placeholder: {placeholder} -> {original}")
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
                    logger.info(f"Replacing from store: {placeholder} -> {original}")
                    processed_text = processed_text.replace(placeholder, original)
                    replaced = True
                    break
            
            if not replaced:
                # Handle pattern like <TYPE_{uuid}> 
                entity_type = match.group(1)
                for mapping in entity_mapping_store.values():
                    for p, original in mapping.items():
                        if f"<{entity_type}_" in p:
                            logger.info(f"Replacing generic pattern: {placeholder} -> {original}")
                            processed_text = processed_text.replace(placeholder, original)
                            replaced = True
                            break
                    if replaced:
                        break
        
        # Log total processing time
        processing_time = time.time() - start_time
        logger.info(f"Total deanonymization processing time: {processing_time:.4f} seconds")
        
        return processed_text, {}

def _recursive_process(data: Any, is_anonymize: bool, path: str = "") -> Tuple[Any, Dict[str, Dict[str, str]]]:
    """
    Recursively process data structure to anonymize or deanonymize text.
    
    Args:
        data: The data to process (can be dict, list, or primitive)
        is_anonymize: If True, anonymize. If False, deanonymize.
        path: Current path in the JSON structure
        
    Returns:
        Tuple of (processed_data, all_mappings)
    """
    all_mappings = {}
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            # Skip technical fields that should never be processed
            skip_keys = [
                "format", "type", "id", "model", "object", "role", "tool_calls", 
                "tool_call_id", "function", "name", "arguments", "temperature", 
                "max_tokens", "top_p", "frequency_penalty", "presence_penalty", 
                "stop", "stream", "safe_prompt", "chat_id", "session_id", 
                "conversation_id", "correlation_id", "features", "loading", "settings"
            ]
            
            if key in skip_keys:
                result[key] = value
            else:
                processed_value, mappings = _recursive_process(value, is_anonymize, current_path)
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
                
            processed_item, mappings = _recursive_process(item, is_anonymize, current_path)
            result.append(processed_item)
            all_mappings.update(mappings)
        return result, all_mappings
    
    elif isinstance(data, str):
        processed_text, mapping = _process_text(data, is_anonymize)
        if mapping:
            all_mappings[path] = mapping
        return processed_text, all_mappings
    
    else:
        # Return unchanged for other data types
        return data, all_mappings

def anonymize_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Dict[str, str]]]:
    """
    Anonymize sensitive information in the provided data.
    
    Args:
        data: The data to anonymize
        
    Returns:
        Tuple of (anonymized_data, entity_mappings)
    """
    total_start_time = time.time()
    logger.info("Starting anonymization process")
    
    # Process each part of the data structure
    anonymized_data, entity_mappings = _recursive_process(data, is_anonymize=True)
    
    # Generate a global mapping ID for this request
    global_mapping_id = str(uuid.uuid4())
    entity_mapping_store[global_mapping_id] = entity_mappings
    
    # Add mapping ID to metadata for use during deanonymization
    if "metadata" not in anonymized_data:
        anonymized_data["metadata"] = {}
    anonymized_data["metadata"]["privacy_mapping_id"] = global_mapping_id
    
    # Log mapping summary
    mapping_count = sum(1 for m in entity_mappings.values() if m)
    
    # Make a simple summary of what was anonymized
    if mapping_count > 0:
        for path, mapping_data in entity_mappings.items():
            if mapping_data and "entities" in mapping_data:
                for placeholder, original in mapping_data["entities"].items():
                    entity_type = placeholder.split("_")[0].strip("<")
                    logger.info(f"Anonymized {entity_type}: {original} -> {placeholder}")
    
    total_time = time.time() - total_start_time
    logger.info(f"Anonymization complete. Found {mapping_count} mappings with ID: {global_mapping_id}. Total time: {total_time:.4f} seconds")
    
    return anonymized_data, entity_mappings

def deanonymize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deanonymize data that was previously anonymized.
    
    Args:
        data: The data to deanonymize
        
    Returns:
        Deanonymized data
    """
    total_start_time = time.time()
    logger.info("Starting deanonymization process")
    
    # Extract mapping ID if present
    mapping_id = None
    if "metadata" in data and "privacy_mapping_id" in data["metadata"]:
        mapping_id = data["metadata"]["privacy_mapping_id"]
        logger.info(f"Found mapping ID in metadata: {mapping_id}")
        
        # Check if we have this mapping
        if mapping_id in entity_mapping_store:
            logger.info(f"Found mapping in store with ID {mapping_id}")
        else:
            logger.warning(f"Mapping ID {mapping_id} not found in store")
    else:
        logger.warning("No mapping ID found in metadata")
    
    # Process the data to restore original values
    deanonymized_data, _ = _recursive_process(data, is_anonymize=False)
    
    # Remove the mapping ID from the response after processing is complete
    if "metadata" in deanonymized_data and "privacy_mapping_id" in deanonymized_data["metadata"]:
        del deanonymized_data["metadata"]["privacy_mapping_id"]
    
    total_time = time.time() - total_start_time
    logger.info(f"Deanonymization complete. Total time: {total_time:.4f} seconds")
    return deanonymized_data 