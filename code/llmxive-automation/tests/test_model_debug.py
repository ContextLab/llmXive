#!/usr/bin/env python3
"""Debug model inference to see what's happening"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.model_manager import ModelManager
from src.conversation_manager import ConversationManager

def test_model_inference():
    """Test model inference with debugging"""
    print("Loading model...")
    model_mgr = ModelManager(max_size_gb=1.5)
    model, tokenizer = model_mgr._load_model("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    
    print("Creating conversation manager...")
    conv_mgr = ConversationManager(model, tokenizer)
    
    # Override methods to see what's happening
    original_validate = conv_mgr._validate_response
    original_extract = conv_mgr._extract_response
    
    def debug_extract(full_response, prompt):
        print(f"\n=== DEBUG: Extraction ===")
        print(f"Full response length: {len(full_response)}")
        print(f"Full response (first 500 chars): {repr(full_response[:500])}")
        print(f"Prompt in response: {prompt in full_response}")
        extracted = original_extract(full_response, prompt)
        print(f"Extracted length: {len(extracted)}")
        print(f"Extracted: {repr(extracted[:200])}")
        print("======================\n")
        return extracted
    
    def debug_validate(response, task_type):
        print(f"\n=== DEBUG: Validation ===")
        print(f"Response length: {len(response)}")
        print(f"Response: {repr(response[:200])}")
        print(f"Task type: {task_type}")
        result = original_validate(response, task_type)
        print(f"Validation result: {result}")
        print("=========================\n")
        return result
    
    conv_mgr._validate_response = debug_validate
    conv_mgr._extract_response = debug_extract
    
    print("Querying model...")
    response = conv_mgr.query_model(
        "Generate a brief description of what machine learning is, in 2-3 sentences.",
        task_type=None
    )
    
    print(f"\nFinal response: {response}")

if __name__ == "__main__":
    test_model_inference()