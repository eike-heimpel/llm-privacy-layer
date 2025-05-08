from fastapi import APIRouter, HTTPException
import logging
import json
from typing import Dict, Any
from app.utils.anonymizer import anonymize_data, deanonymize_data

router = APIRouter(prefix="/api", tags=["privacy"])
logger = logging.getLogger(__name__)

# Store the most recent mapping ID to help with consistency
# In a production environment, this would be replaced with a proper database or Redis
latest_mapping_id = None

@router.post("/inlet")
async def process_inlet(payload: Dict[str, Any]):
    """
    Process incoming data from OpenWebUI and anonymize sensitive information.
    
    This endpoint receives the raw body from OpenWebUI, applies privacy filters
    using Presidio to anonymize PII, and returns the modified body.
    """
    global latest_mapping_id
    
    try:
        logger.info("Received inlet request")
        
        # Log keys in the original request for debugging
        logger.info(f"Original request keys: {list(payload.keys())}")
        
        # Process and anonymize the body
        anonymized_body, entities_map = anonymize_data(payload)
        
        # Log keys in the anonymized body for debugging
        logger.info(f"Anonymized response keys: {list(anonymized_body.keys())}")
        
        # Store the mapping ID for potential use in outlet requests
        if "metadata" in anonymized_body and "privacy_mapping_id" in anonymized_body["metadata"]:
            latest_mapping_id = anonymized_body["metadata"]["privacy_mapping_id"]
            logger.info(f"Stored latest mapping ID: {latest_mapping_id}")
        
        # Verify the structure remains consistent
        if set(payload.keys()) != set(anonymized_body.keys()):
            # Log the difference for debugging
            missing_keys = set(payload.keys()) - set(anonymized_body.keys())
            extra_keys = set(anonymized_body.keys()) - set(payload.keys())
            if missing_keys:
                logger.warning(f"Keys missing in anonymized body: {missing_keys}")
            if extra_keys:
                logger.warning(f"Extra keys in anonymized body: {extra_keys}")
            
            # Ensure we retain the original structure
            for key in payload.keys():
                if key not in anonymized_body and key != "metadata":
                    anonymized_body[key] = payload[key]
                    logger.info(f"Restored missing key: {key}")
        
        # Return anonymized data and store the mapping for deanonymization
        logger.info("Successfully anonymized inlet data")
        return anonymized_body
    except Exception as e:
        logger.error(f"Error processing inlet request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.post("/outlet")
async def process_outlet(payload: Dict[str, Any]):
    """
    Process outgoing data from the LLM and deanonymize information.
    
    This endpoint receives the response body, applies deanonymization to restore
    the original sensitive information, and returns the modified body.
    """
    global latest_mapping_id
    
    try:
        logger.info("Received outlet request")
        
        # Log keys in the original response for debugging
        logger.info(f"Original response keys: {list(payload.keys())}")
        
        # If no mapping ID in body but we have a latest one, add it
        if ("metadata" not in payload or "privacy_mapping_id" not in payload.get("metadata", {})) and latest_mapping_id:
            logger.info(f"Adding latest mapping ID to response: {latest_mapping_id}")
            if "metadata" not in payload:
                payload["metadata"] = {}
            payload["metadata"]["privacy_mapping_id"] = latest_mapping_id
        
        # Process and deanonymize the body
        deanonymized_body = deanonymize_data(payload)
        
        # Log keys in the deanonymized response for debugging
        logger.info(f"Deanonymized response keys: {list(deanonymized_body.keys())}")
        
        # Verify the structure remains consistent
        if set(payload.keys()) != set(deanonymized_body.keys()):
            # Log the difference for debugging
            missing_keys = set(payload.keys()) - set(deanonymized_body.keys())
            extra_keys = set(deanonymized_body.keys()) - set(payload.keys())
            if missing_keys:
                logger.warning(f"Keys missing in deanonymized body: {missing_keys}")
            if extra_keys:
                logger.warning(f"Extra keys in deanonymized body: {extra_keys}")
            
            # Ensure we retain the original structure
            for key in payload.keys():
                if key not in deanonymized_body and key != "metadata":
                    deanonymized_body[key] = payload[key]
                    logger.info(f"Restored missing key: {key}")
        
        logger.info("Successfully deanonymized outlet data")
        return deanonymized_body
    except Exception as e:
        logger.error(f"Error processing outlet request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}") 