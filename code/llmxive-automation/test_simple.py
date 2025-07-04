#!/usr/bin/env python3
"""Simple test showing the llmXive automation system working locally"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.model_manager import ModelManager
from transformers import pipeline
import logging

logging.basicConfig(level=logging.INFO)

print("=== llmXive Local Execution Test ===\n")

# 1. Load model with higher size limit
print("1. Loading model with 20GB limit (for local execution)...")
mgr = ModelManager(max_size_gb=20)
model, tokenizer = mgr.get_suitable_model()
print(f"✓ Loaded: {model.name_or_path}")
print(f"✓ Model size: ~{model.num_parameters() / 1e9:.1f}B parameters\n")

# 2. Create a pipeline for easy generation
print("2. Creating generation pipeline...")
generator = pipeline("text-generation", model=model, tokenizer=tokenizer)

# 3. Test llmXive tasks
print("3. Testing llmXive task generation:\n")

tasks = [
    {
        "name": "Brainstorm Research Idea",
        "prompt": "Generate a novel research idea combining EEG signals and language models. Title:"
    },
    {
        "name": "Technical Design",
        "prompt": "Design a system for real-time cognitive load detection. Architecture:"
    },
    {
        "name": "Implementation Plan", 
        "prompt": "Create a 3-phase implementation plan for building an EEG analysis pipeline. Phase 1:"
    }
]

for task in tasks:
    print(f"Task: {task['name']}")
    print(f"Prompt: {task['prompt']}")
    
    # Generate response
    result = generator(
        task['prompt'],
        max_new_tokens=100,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id
    )
    
    response = result[0]['generated_text']
    # Remove the prompt from response
    if response.startswith(task['prompt']):
        response = response[len(task['prompt']):].strip()
    
    print(f"Response: {response[:200]}...")
    print("-" * 80 + "\n")

print("✅ Test complete! The system can generate responses for llmXive tasks.")
print("\nNote: When running with GitHub access, the full automation pipeline")
print("would execute these tasks and update the repository automatically.")