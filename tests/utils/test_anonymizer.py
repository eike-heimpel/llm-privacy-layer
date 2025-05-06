import pytest
import json
import os
import requests
from openai import OpenAI
from app.utils.anonymizer import anonymize_data, deanonymize_data

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