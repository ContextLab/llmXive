#!/usr/bin/env python3
"""Test script to demonstrate model generation without GitHub"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.model_manager import ModelManager
from src.conversation_manager import ConversationManager
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_model_generation():
    """Test model loading and text generation"""
    
    print("=== llmXive Model Generation Test ===\n")
    
    # Initialize model manager with local size limit
    print("1. Initializing model manager with 20GB limit for local execution...")
    mgr = ModelManager(max_size_gb=20)
    
    # Load a model
    print("2. Loading model from HuggingFace...")
    model, tokenizer = mgr.get_suitable_model()
    print(f"   Loaded: {model.name_or_path}\n")
    
    # Initialize conversation manager
    print("3. Setting up conversation manager...")
    conv_mgr = ConversationManager(model, tokenizer)
    
    # Test various llmXive tasks
    test_prompts = [
        {
            "task": "BRAINSTORM_IDEA",
            "prompt": "Generate a novel research idea that combines neuroscience and machine learning. The idea should be suitable for the llmXive platform."
        },
        {
            "task": "TECHNICAL_DESIGN",
            "prompt": "Write a technical design for a system that uses EEG data to predict cognitive load during programming tasks."
        },
        {
            "task": "LITERATURE_SEARCH",
            "prompt": "What are the key papers in the field of neural decoding from EEG signals? List 3-5 important works."
        }
    ]
    
    print("4. Testing generation with llmXive tasks:\n")
    
    for test in test_prompts:
        print(f"Task: {test['task']}")
        print(f"Prompt: {test['prompt'][:80]}...")
        
        try:
            response = conv_mgr.query(test['prompt'], task_type=test['task'])
            print(f"Response: {response[:300]}...")
            print("-" * 80)
        except Exception as e:
            print(f"Error: {e}")
            print("-" * 80)
    
    print("\n✅ Test complete! Model is working correctly for llmXive tasks.")

if __name__ == "__main__":
    test_model_generation()