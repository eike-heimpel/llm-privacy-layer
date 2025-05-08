"""Core anonymization functionality for handling sensitive information in data."""

import logging
import uuid
import time
from typing import Dict, Tuple, Any, List

# Presidio imports
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

# Local imports
from app.utils.anonymizer.store import entity_mapping_store
from app.utils.anonymizer.recursion import process_data_recursively
from app.utils.anonymizer.profiles import load_profiles
from app.utils.anonymizer.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Presidio analyzer engine
def get_analyzer_engine():
    """Initialize and return the Presidio analyzer engine based on config."""
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": config.spacy_models # Use models from config
    })
    nlp_engine = provider.create_engine()
    registry = RecognizerRegistry()
    
    # Load predefined recognizers. These will be aware of all NLP capabilities
    # (e.g., 'en' and 'de') from the nlp_engine.
    registry.load_predefined_recognizers(nlp_engine=nlp_engine)
    
    # TODO: Add any custom recognizers or adjust existing ones here,
    # especially for German (e.g., context words, German-specific patterns).

    # Determine supported languages from the configured models
    supported_languages = list(set(model["lang_code"] for model in config.spacy_models))
    
    logger.info(f"Analyzer engine initialized with models: {config.spacy_models} and supported languages: {supported_languages}")

    return AnalyzerEngine(
        nlp_engine=nlp_engine,
        registry=registry,
        supported_languages=supported_languages
    )

# Initialize engines
analyzer = get_analyzer_engine()
anonymizer = AnonymizerEngine()
profiles = load_profiles()
logger.info("Presidio engines and profiles initialized")

def anonymize_data(data: Dict[str, Any], profile_name: str = None) -> Tuple[Dict[str, Any], Dict[str, Dict[str, str]]]:
    """Anonymize sensitive information in the provided data."""
    # Use provided profile or the default from config
    profile = profile_name or config.default_profile
    
    total_start_time = time.time()
    logger.info(f"Starting anonymization with profile: {profile}")
    
    # Process each part of the data structure
    anonymized_data, entity_mappings = process_data_recursively(
        data=data,
        is_anonymize=True,
        analyzer=analyzer,
        profiles=profiles,
        default_thresholds=config.default_thresholds,
        profile_name=profile
    )
    
    # Generate a global mapping ID for this request
    global_mapping_id = str(uuid.uuid4())
    entity_mapping_store.add(global_mapping_id, entity_mappings)
    
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
    deanonymized_data, _ = process_data_recursively(
        data=data,
        is_anonymize=False
    )
    
    # Remove the mapping ID from the response after processing is complete
    if "metadata" in deanonymized_data and "privacy_mapping_id" in deanonymized_data["metadata"]:
        del deanonymized_data["metadata"]["privacy_mapping_id"]
    
    logger.info(f"Deanonymization complete: {time.time() - total_start_time:.4f}s total")
    return deanonymized_data 