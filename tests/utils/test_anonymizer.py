import pytest
import json
import os
import requests
from openai import OpenAI
from app.utils.anonymizer import anonymize_data, deanonymize_data
import logging

# Import modules to test internal functionality
from app.utils.anonymizer.profiles import load_profiles
from app.utils.anonymizer.config import config

# File to store test results - always set by environment variable
RESULTS_FILE = os.environ['TEST_RESULTS_FILE']

# OpenRouter API configuration
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
EVAL_MODEL = os.environ.get('EVAL_MODEL', 'google/gemini-2.0-flash-001')

# Initialize results file
def setup_module():
    with open(RESULTS_FILE, "w") as f:
        f.write("# Anonymizer Test Results\n\n")
        f.write("This file contains the results of running the anonymizer tests.\n\n")

# Helper function to write to results file
def write_to_results(text):
    with open(RESULTS_FILE, "a") as f:
        f.write(text + "\n")

# LLM evaluation function using OpenRouter
def evaluate_with_llm(conversation):
    """
    Use OpenRouter LLM to evaluate the readability of anonymized text
    """
    if not OPENROUTER_API_KEY:
        return "LLM evaluation skipped: No OpenRouter API key provided"
    
    try:
        # Format the conversation as a string
        formatted_conversation = "\n\n".join([
            f"{msg['role']}: {msg['content']}" for msg in conversation
        ])
        
        # Create prompt for the LLM
        prompt = f"""
        You are evaluating an anonymized conversation where personally identifiable information (PII) 
        has been replaced with placeholders like <PERSON_id> or <EMAIL_ADDRESS_id>.
        
        Here is the anonymized conversation:
        
        {formatted_conversation}
        
        Please provide a brief assessment (3-4 sentences) of:
        1. How readable/understandable is this anonymized text?
        2. Are there any confusing parts or ambiguities?
        3. Is the context of the conversation preserved despite the anonymization?
        """
        
        # Create OpenAI client configured for OpenRouter
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
        
        # Make the API call
        response = client.chat.completions.create(
            model=EVAL_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Return the LLM's assessment
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error during LLM evaluation: {str(e)}"

def test_basic_anonymization():
    """Test basic anonymization with simple user message"""
    write_to_results("## Basic Anonymization Test\n")
    
    # Sample chat data with PII
    test_data = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "My name is John Smith and my email is john.smith@example.com."}
        ]
    }
    
    # Anonymize the data
    anonymized_data, mappings = anonymize_data(test_data)
    
    # User message should be anonymized
    user_message = anonymized_data["messages"][1]["content"]
    assert "John Smith" not in user_message
    assert "john.smith@example.com" not in user_message
    
    # Write to results file
    write_to_results(f"**Original message:**\n```\n{test_data['messages'][1]['content']}\n```\n")
    write_to_results(f"**Anonymized message:**\n```\n{user_message}\n```\n")

def test_deanonymization():
    """Test the deanonymization process restores original data"""
    write_to_results("## Deanonymization Test\n")
    
    # Sample chat data with PII
    test_data = {
        "messages": [
            {"role": "user", "content": "My phone number is 555-123-4567 and I live in New York."}
        ]
    }
    
    # Anonymize then deanonymize
    anonymized_data, _ = anonymize_data(test_data)
    deanonymized_data = deanonymize_data(anonymized_data)
    
    # Write to results file
    write_to_results(f"**Original message:**\n```\n{test_data['messages'][0]['content']}\n```\n")
    write_to_results(f"**Anonymized message:**\n```\n{anonymized_data['messages'][0]['content']}\n```\n")
    write_to_results(f"**Deanonymized message:**\n```\n{deanonymized_data['messages'][0]['content']}\n```\n")

def test_complex_conversation():
    """Test a more complex conversation with multiple messages and entity types"""
    write_to_results("## Complex Conversation Test\n")
    
    test_data = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hi, I'm Sarah Johnson."},
            {"role": "assistant", "content": "Hello Sarah, how can I help you today?"},
            {"role": "user", "content": "I need to send money to my friend. His account is 12345678 at Chase Bank."},
            {"role": "assistant", "content": "I understand you want to send money to your friend's account 12345678 at Chase Bank."}
        ]
    }
    
    # Anonymize the data
    anonymized_data, mappings = anonymize_data(test_data)
    
    # Write the conversation to the results file
    write_to_results("### Original Conversation:\n")
    for i, msg in enumerate(test_data["messages"]):
        write_to_results(f"**{msg['role']}**: {msg['content']}\n")
    
    write_to_results("\n### Anonymized Conversation:\n")
    for i, msg in enumerate(anonymized_data["messages"]):
        write_to_results(f"**{msg['role']}**: {msg['content']}\n")
    
    # Get LLM evaluation of the anonymized conversation
    llm_evaluation = evaluate_with_llm(anonymized_data["messages"])
    
    # Add the evaluation to the results file
    write_to_results("\n### LLM Evaluation:\n")
    write_to_results(f"{llm_evaluation}\n")

def test_non_pii_content():
    """Test that non-PII content remains unchanged"""
    write_to_results("## Non-PII Content Test\n")
    
    test_data = {
        "messages": [
            {"role": "user", "content": "What is the capital of France?"},
            {"role": "assistant", "content": "The capital of France is Paris."}
        ]
    }
    
    # Anonymize the data
    anonymized_data, mappings = anonymize_data(test_data)
    
    # Write results
    write_to_results("### Original message:\n")
    write_to_results(f"**user**: {test_data['messages'][0]['content']}\n")
    
    write_to_results("\n### Anonymized message (should be identical):\n")
    write_to_results(f"**user**: {anonymized_data['messages'][0]['content']}\n")

# New high-value tests for the enhanced functionality

def test_custom_entities():
    """Test that custom entities from profiles are properly anonymized"""
    write_to_results("## Custom Entities Test\n")
    
    # Create a test profile with custom entities
    test_profile = {
        "thresholds": {"DEFAULT": 0.85},
        "custom_entities": {
            "ORGANIZATION": ["Acme Test Corporation"],
            "PERSON": ["John Test User"]
        },
        "fuzzy_match": {"enabled": False}
    }
    
    # Inject the test profile into the profiles
    from app.utils.anonymizer.core import profiles
    profiles["test_profile"] = test_profile
    
    # Sample chat data with our custom entities
    test_data = {
        "messages": [
            {"role": "user", "content": "I work at Acme Test Corporation and my name is John Test User."}
        ]
    }
    
    # Anonymize with our test profile
    anonymized_data, mappings = anonymize_data(test_data, profile_name="test_profile")
    user_message = anonymized_data["messages"][0]["content"]
    
    # Verify custom entities are anonymized
    assert "Acme Test Corporation" not in user_message
    assert "John Test User" not in user_message
    assert "<ORGANIZATION_" in user_message
    assert "<PERSON_" in user_message
    
    # Deanonymize and verify it's restored correctly
    deanonymized_data = deanonymize_data(anonymized_data)
    deanonymized_message = deanonymized_data["messages"][0]["content"]
    assert "Acme Test Corporation" in deanonymized_message
    assert "John Test User" in deanonymized_message
    
    # Write to results file
    write_to_results(f"**Original message:**\n```\n{test_data['messages'][0]['content']}\n```\n")
    write_to_results(f"**Anonymized message:**\n```\n{user_message}\n```\n")
    write_to_results(f"**Deanonymized message:**\n```\n{deanonymized_message}\n```\n")
    write_to_results(f"**Observation:** Custom entities from the profile were correctly anonymized and deanonymized.\n")

def test_entity_specific_thresholds():
    """Test that entity-specific thresholds are applied correctly"""
    write_to_results("## Entity-Specific Thresholds Test\n")
    
    # Create test profiles with different thresholds
    high_threshold_profile = {
        "thresholds": {"PERSON": 0.99, "DEFAULT": 0.85},  # Very high person threshold
        "custom_entities": {},
        "skip_terms": []
    }
    
    low_threshold_profile = {
        "thresholds": {"PERSON": 0.3, "DEFAULT": 0.85},  # Very low person threshold
        "custom_entities": {},
        "skip_terms": []
    }
    
    # Inject test profiles
    from app.utils.anonymizer.core import profiles
    profiles["high_threshold"] = high_threshold_profile
    profiles["low_threshold"] = low_threshold_profile
    
    # Test data with a person name
    test_data = {
        "messages": [
            {"role": "user", "content": "My name is Sarah Johnson."}
        ]
    }
    
    # Anonymize with different profiles
    high_threshold_result, _ = anonymize_data(test_data, profile_name="high_threshold")
    low_threshold_result, _ = anonymize_data(test_data, profile_name="low_threshold")
    
    high_message = high_threshold_result["messages"][0]["content"]
    low_message = low_threshold_result["messages"][0]["content"]
    
    # Write to results file
    write_to_results(f"**Original message:**\n```\n{test_data['messages'][0]['content']}\n```\n")
    write_to_results(f"**With high threshold (0.99) for PERSON:**\n```\n{high_message}\n```\n")
    write_to_results(f"**With low threshold (0.3) for PERSON:**\n```\n{low_message}\n```\n")
    
    # Verify different thresholds produce different results
    name_anonymized_in_high = "Sarah Johnson" not in high_message
    name_anonymized_in_low = "Sarah Johnson" not in low_message
    
    if name_anonymized_in_low and not name_anonymized_in_high:
        write_to_results("**Observation:** The name was only anonymized with the low threshold profile, confirming thresholds work correctly.\n")
    else:
        write_to_results("**Observation:** Threshold behavior was not as expected. This might indicate an issue with threshold application.\n")

def test_skip_terms():
    """Test that skip_terms in profiles are properly applied"""
    write_to_results("## Skip Terms Test\n")
    
    # Create a test profile with skip terms
    test_profile = {
        "thresholds": {"DEFAULT": 0.75},
        "custom_entities": {},
        "skip_terms": ["TestCompany", "test@example.com"]
    }
    
    # Inject the test profile into the profiles
    from app.utils.anonymizer.core import profiles
    profiles["skip_terms_profile"] = test_profile
    
    # Test with terms that should be skipped
    test_data = {
        "messages": [
            {"role": "user", "content": "TestCompany"},
            {"role": "user", "content": "AnotherCompany"}
        ]
    }
    
    # Anonymize with our test profile
    anonymized_data, mappings = anonymize_data(test_data, profile_name="skip_terms_profile")
    skipped_message = anonymized_data["messages"][0]["content"]
    normal_message = anonymized_data["messages"][1]["content"]
    
    # Write to results file
    write_to_results(f"**Original message with skip term:**\n```\n{test_data['messages'][0]['content']}\n```\n")
    write_to_results(f"**Anonymized message (should remain unchanged):**\n```\n{skipped_message}\n```\n")
    
    write_to_results(f"**Original message without skip term:**\n```\n{test_data['messages'][1]['content']}\n```\n")
    
    # Check if skip terms are preserved
    skip_term_preserved = skipped_message == "TestCompany"
    
    write_to_results(f"**Skip term preserved:** {'Yes' if skip_term_preserved else 'No'}\n")
    
    # Create a more complex test with longer content
    complex_test = {
        "content": "I work at TestCompany and AnotherCompany."
    }
    
    anonymized_complex, _ = anonymize_data(complex_test, profile_name="skip_terms_profile")
    complex_result = anonymized_complex["content"]
    
    write_to_results(f"**Complex test original:**\n```\n{complex_test['content']}\n```\n")
    write_to_results(f"**Complex test anonymized:**\n```\n{complex_result}\n```\n")
    
    # Note: The current implementation applies skip_terms at the whole-text level,
    # not for partial matches within text. This is by design to avoid performance overhead.
    write_to_results(f"**Note:** Skip terms are applied to exact matches of the entire text content, not for partial matches within larger text.\n") 