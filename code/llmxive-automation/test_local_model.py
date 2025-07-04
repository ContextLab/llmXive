#!/usr/bin/env python3
"""Quick test to verify model loading works locally"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.model_manager import ModelManager
import logging

logging.basicConfig(level=logging.INFO)

def test_model_loading():
    """Test loading different sized models"""
    
    print("Testing model loading capabilities...")
    print("")
    
    # Test 1: Default size limit (3.5GB)
    print("Test 1: Loading model with 3.5GB limit")
    mgr_small = ModelManager(max_size_gb=3.5)
    try:
        model, tokenizer = mgr_small.get_suitable_model()
        print(f"✓ Successfully loaded: {model.name_or_path}")
        print(f"  Model size estimate: {mgr_small._estimate_model_size(mgr_small.hf_api.model_info(model.name_or_path)) / 1e9:.2f}GB")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("")
    
    # Test 2: Larger size limit (20GB)
    print("Test 2: Loading model with 20GB limit")
    mgr_large = ModelManager(max_size_gb=20)
    try:
        model, tokenizer = mgr_large.get_suitable_model()
        print(f"✓ Successfully loaded: {model.name_or_path}")
        print(f"  Model size estimate: {mgr_large._estimate_model_size(mgr_large.hf_api.model_info(model.name_or_path)) / 1e9:.2f}GB")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("")
    
    # Test 3: Specific model
    print("Test 3: Loading specific model (microsoft/Phi-3-medium-4k-instruct)")
    mgr_specific = ModelManager(max_size_gb=20)
    try:
        model, tokenizer = mgr_specific._load_model("microsoft/Phi-3-medium-4k-instruct")
        print(f"✓ Successfully loaded: {model.name_or_path}")
        
        # Test generation
        inputs = tokenizer("Hello, I am", return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=10, do_sample=False)
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"  Test generation: {generated}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        print("  Note: This model requires ~8GB RAM. Falling back to smaller model...")
        
        # Try a smaller specific model
        try:
            model, tokenizer = mgr_specific._load_model("microsoft/phi-2")
            print(f"✓ Successfully loaded fallback: {model.name_or_path}")
        except Exception as e2:
            print(f"✗ Fallback also failed: {e2}")

if __name__ == "__main__":
    test_model_loading()