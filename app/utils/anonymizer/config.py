import os
import logging

logger = logging.getLogger(__name__)

class AnonymizerConfig:
    """Simple configuration class for the anonymizer."""
    
    def __init__(self):
        self.profile_path = os.path.join("app", "config", "profiles.yaml")
        self.default_profile = "default"
        self.cache_mappings = True
        self.cache_ttl = 3600  # 1 hour
        
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
                
        logger.info(f"Anonymizer config initialized: profile_path={self.profile_path}, default_profile={self.default_profile}")

# Create a singleton instance
config = AnonymizerConfig() 