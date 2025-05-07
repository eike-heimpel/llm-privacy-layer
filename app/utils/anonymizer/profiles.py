import os
import yaml
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Import config singleton
from app.utils.anonymizer.config import config

def load_profiles(profile_path: Optional[str] = None) -> Dict[str, Any]:
    """Load profiles from YAML configuration file."""
    # Use provided path or default from config
    path = profile_path or config.profile_path
    
    if not os.path.exists(path):
        logger.warning(f"Profile file not found: {path}")
        return _get_default_profile()
        
    try:
        with open(path, 'r') as file:
            logger.info(f"Loading profiles from {path}")
            profiles_data = yaml.safe_load(file)
            
            if not profiles_data or "profiles" not in profiles_data:
                logger.warning(f"No profiles found in {path}")
                return _get_default_profile()
                
            logger.info(f"Loaded {len(profiles_data['profiles'])} profiles")
            return profiles_data["profiles"]
    except Exception as e:
        logger.error(f"Error loading profiles from {path}: {e}")
        return _get_default_profile()

def _get_default_profile() -> Dict[str, Any]:
    """Return a default profile when none is found."""
    logger.warning("Using default in-memory profile")
    return {
        "default": {
            "thresholds": {
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
            },
            "custom_entities": {
                "PERSON": [],
                "ORGANIZATION": [],
                "LOCATION": []
            },
            "skip_terms": []
        }
    }

def create_default_profile_file(path: Optional[str] = None) -> bool:
    """Create a default profile file if one doesn't exist."""
    profile_path = path or config.profile_path
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(profile_path), exist_ok=True)
    
    if os.path.exists(profile_path):
        logger.info(f"Profile file already exists at {profile_path}")
        return False
        
    default_profile = {
        "version": 1,
        "profiles": {
            "default": {
                "thresholds": {
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
                },
                "custom_entities": {
                    "PERSON": [
                        "John Doe",
                        "Jane Smith"
                    ],
                    "ORGANIZATION": [
                        "Acme Corporation",
                        "Example Company LLC"
                    ],
                    "LOCATION": [
                        "123 Main Street, Anytown, USA",
                        "456 Elm Avenue, Springfield"
                    ],
                    "PHONE_NUMBER": [
                        "+1 (555) 123-4567",
                        "800-555-0100"
                    ],
                    "EMAIL_ADDRESS": [
                        "contact@example.com",
                        "support@testcompany.org"
                    ]
                },
                "fuzzy_match": {
                    "enabled": True,
                    "thresholds": {
                        "PERSON": 85,
                        "ORGANIZATION": 90,
                        "LOCATION": 85,
                        "DEFAULT": 80
                    }
                },
                "skip_terms": [
                    "en", "de", "en-US", "en-GB", "de-DE",
                    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
                    "january", "february", "march", "april", "may", "june", "july", 
                    "august", "september", "october", "november", "december"
                ]
            },
            "high_security": {
                "description": "Profile with lower thresholds to catch more potential PII",
                "thresholds": {
                    "DEFAULT": 0.6
                },
                "custom_entities": {
                    "PERSON": [
                        "John Doe",
                        "Jane Smith"
                    ]
                },
                "fuzzy_match": {
                    "enabled": True,
                    "thresholds": {
                        "DEFAULT": 75
                    }
                },
                "skip_terms": []
            }
        }
    }
    
    try:
        with open(profile_path, 'w') as file:
            yaml.dump(default_profile, file, default_flow_style=False)
        logger.info(f"Created default profile file at {profile_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create default profile file: {e}")
        return False

# Create an example profile file if running this module directly
if __name__ == "__main__":
    create_default_profile_file() 