import os
import logging
import json # Added for parsing JSON env var

logger = logging.getLogger(__name__)

class AnonymizerConfig:
    """Simple configuration class for the anonymizer."""
    
    def __init__(self):
        # Basic configuration
        self.profile_path = os.path.join("app", "config", "profiles.yaml")
        self.default_profile = "default"
        self.cache_mappings = True
        self.cache_ttl = 3600  # 1 hour
        
        # SpaCy models configuration
        # Default models: upgraded English and added German
        self.spacy_models = [
            {"lang_code": "en", "model_name": "en_core_web_lg"},
            {"lang_code": "de", "model_name": "de_core_news_lg"}
        ]
        
        # Entity mapping storage configuration
        # Maximum number of mapping sets to keep in memory - controls memory usage
        # Higher values allow more concurrent anonymization operations but use more memory
        self.mapping_store_max_size = 100
        
        # Entity matching configuration
        # Minimum length for an entity to be considered in fuzzy matching
        # Lower values (like 2) allow matching very short names like "Jo" or "Li" but may increase false positives
        self.min_entity_length = 2
        
        # Maximum number of words to consider in phrase matching
        # Higher values allow matching of longer phrases but increase processing time
        self.max_phrase_words = 5
        
        # UUID validation parameters used to detect and skip UUIDs during processing
        self.uuid_length = 36      # Standard UUID string length
        self.uuid_dash_count = 4   # Number of dashes in a standard UUID
        
        # Default entity detection thresholds (moved from core.py)
        # Values are confidence scores between 0 and 1
        # Higher values = stricter matching (fewer false positives but may miss some entities)
        # Lower values = broader matching (catches more potential entities but more false positives)
        self.default_thresholds = {
            "PERSON": 0.85,         # Person names
            "EMAIL_ADDRESS": 0.75,  # Email addresses
            "PHONE_NUMBER": 0.75,   # Phone numbers
            "LOCATION": 0.90,       # Location names, addresses
            "DATE_TIME": 0.95,      # Dates and times
            "NRP": 0.85,            # Numeric Recognition Patterns
            "IP_ADDRESS": 0.75,     # IP addresses
            "DOMAIN_NAME": 0.80,    # Domain names
            "URL": 0.80,            # Web URLs
            "DEFAULT": 0.85         # Default threshold for other entity types
        }
        
        # Load from environment if present
        if os.environ.get("LLM_PRIVACY_PROFILE_PATH"):
            self.profile_path = os.environ.get("LLM_PRIVACY_PROFILE_PATH")
            
        if os.environ.get("LLM_PRIVACY_DEFAULT_PROFILE"):
            self.default_profile = os.environ.get("LLM_PRIVACY_DEFAULT_PROFILE")
            
        if os.environ.get("LLM_PRIVACY_CACHE_MAPPINGS"):
            self.cache_mappings = os.environ.get("LLM_PRIVACY_CACHE_MAPPINGS").lower() == "true"
            
        if os.environ.get("LLM_PRIVACY_CACHE_TTL"):
            try:
                self.cache_ttl = int(os.environ.get("LLM_PRIVACY_CACHE_TTL"))
            except ValueError:
                logger.warning(f"Invalid cache TTL in environment: {os.environ.get('LLM_PRIVACY_CACHE_TTL')}")
        
        if os.environ.get("LLM_PRIVACY_SPACY_MODELS_JSON"):
            try:
                models_json = os.environ.get("LLM_PRIVACY_SPACY_MODELS_JSON")
                self.spacy_models = json.loads(models_json)
                logger.info(f"Loaded spaCy models from LLM_PRIVACY_SPACY_MODELS_JSON: {self.spacy_models}")
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in LLM_PRIVACY_SPACY_MODELS_JSON: {os.environ.get('LLM_PRIVACY_SPACY_MODELS_JSON')}")
            except Exception as e:
                logger.warning(f"Error loading spaCy models from environment: {e}")

        # Advanced configuration options
        if os.environ.get("LLM_PRIVACY_MAPPING_STORE_SIZE"):
            try:
                self.mapping_store_max_size = int(os.environ.get("LLM_PRIVACY_MAPPING_STORE_SIZE"))
            except ValueError:
                logger.warning(f"Invalid mapping store size: {os.environ.get('LLM_PRIVACY_MAPPING_STORE_SIZE')}")
                
        if os.environ.get("LLM_PRIVACY_MIN_ENTITY_LENGTH"):
            try:
                self.min_entity_length = int(os.environ.get("LLM_PRIVACY_MIN_ENTITY_LENGTH"))
            except ValueError:
                logger.warning(f"Invalid min entity length: {os.environ.get('LLM_PRIVACY_MIN_ENTITY_LENGTH')}")
                
        if os.environ.get("LLM_PRIVACY_MAX_PHRASE_WORDS"):
            try:
                self.max_phrase_words = int(os.environ.get("LLM_PRIVACY_MAX_PHRASE_WORDS"))
            except ValueError:
                logger.warning(f"Invalid max phrase words: {os.environ.get('LLM_PRIVACY_MAX_PHRASE_WORDS')}")
                
        # For backward compatibility, also check old environment variable names
        if os.environ.get("PRIVACY_CONTAINER_PROFILE_PATH"):
            self.profile_path = os.environ.get("PRIVACY_CONTAINER_PROFILE_PATH")
            logger.warning("Using deprecated PRIVACY_CONTAINER_PROFILE_PATH environment variable. Please use LLM_PRIVACY_PROFILE_PATH instead.")
            
        if os.environ.get("PRIVACY_CONTAINER_DEFAULT_PROFILE"):
            self.default_profile = os.environ.get("PRIVACY_CONTAINER_DEFAULT_PROFILE")
            logger.warning("Using deprecated PRIVACY_CONTAINER_DEFAULT_PROFILE environment variable. Please use LLM_PRIVACY_DEFAULT_PROFILE instead.")
            
        if os.environ.get("PRIVACY_CONTAINER_CACHE_MAPPINGS"):
            self.cache_mappings = os.environ.get("PRIVACY_CONTAINER_CACHE_MAPPINGS").lower() == "true"
            logger.warning("Using deprecated PRIVACY_CONTAINER_CACHE_MAPPINGS environment variable. Please use LLM_PRIVACY_CACHE_MAPPINGS instead.")
            
        if os.environ.get("PRIVACY_CONTAINER_CACHE_TTL"):
            try:
                self.cache_ttl = int(os.environ.get("PRIVACY_CONTAINER_CACHE_TTL"))
            except ValueError:
                logger.warning(f"Invalid cache TTL in deprecated environment variable: {os.environ.get('PRIVACY_CONTAINER_CACHE_TTL')}")
            logger.warning("Using deprecated PRIVACY_CONTAINER_CACHE_TTL environment variable. Please use LLM_PRIVACY_CACHE_TTL instead.")
                
        logger.info(f"Anonymizer config initialized: profile_path={self.profile_path}, default_profile={self.default_profile}, spacy_models={self.spacy_models}")

# Create a singleton instance
config = AnonymizerConfig() 