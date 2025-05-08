"""Recursive data processing for anonymization and deanonymization."""

from typing import Dict, Tuple, Any, List

# Local imports
from app.utils.anonymizer.processors import anonymize_text, deanonymize_text


def process_data_recursively(data: Any, is_anonymize: bool, analyzer=None, profiles=None, 
                            default_thresholds=None, profile_name: str = "default", 
                            path: str = "") -> Tuple[Any, Dict[str, Dict[str, str]]]:
    """Recursively process data structure to anonymize or deanonymize text."""
    all_mappings = {}
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            processed_value, mappings = process_data_recursively(
                value, is_anonymize, analyzer, profiles, default_thresholds, profile_name, current_path
            )
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
                
            processed_item, mappings = process_data_recursively(
                item, is_anonymize, analyzer, profiles, default_thresholds, profile_name, current_path
            )
            result.append(processed_item)
            all_mappings.update(mappings)
        return result, all_mappings
    
    elif isinstance(data, str):
        if is_anonymize:
            processed_text, mapping = anonymize_text(
                data, analyzer, profiles, default_thresholds, profile_name
            )
        else:
            processed_text, mapping = deanonymize_text(data)
            
        if mapping:
            all_mappings[path] = mapping
        return processed_text, all_mappings
    
    else:
        # Return unchanged for other data types
        return data, all_mappings 