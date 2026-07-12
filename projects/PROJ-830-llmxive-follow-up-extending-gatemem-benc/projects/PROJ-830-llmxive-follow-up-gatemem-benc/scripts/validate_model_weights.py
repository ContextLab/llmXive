"""
Validate frozen DistilBERT weights for intent classification.

This script:
1. Loads the frozen DistilBERT model (CPU-only, default precision).
2. Runs a forward pass on a sample input.
3. Verifies no GPU tensors or quantization libraries are required.
4. Outputs validation results to data/logs/model_validation.json.
"""

import json
import os
import sys
import time
from pathlib import Path

import torch
from transformers import DistilBertModel, DistilBertTokenizer

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_LOGS_DIR = PROJECT_ROOT / "data" / "logs"
OUTPUT_FILE = DATA_LOGS_DIR / "model_validation.json"

# Ensure output directory exists
DATA_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def check_no_gpu():
    """Verify CUDA is not available or not used."""
    if torch.cuda.is_available():
        # If CUDA is available, ensure we are not using it
        if torch.cuda.device_count() > 0:
            return False, "CUDA is available but model should be CPU-only"
    return True, "No GPU allocation detected"

def check_no_quantization():
    """Verify no quantization libraries are imported or used."""
    # Check for common quantization imports that shouldn't be present
    forbidden_imports = ["bitsandbytes", "accelerate.utils", "optimum"]
    for mod in forbidden_imports:
        if mod in sys.modules:
            return False, f"Quantization library {mod} is loaded"
    return True, "No quantization libraries detected"

def load_model_and_tokenizer():
    """Load the frozen DistilBERT model and tokenizer."""
    model_name = "distilbert-base-uncased"
    try:
        tokenizer = DistilBertTokenizer.from_pretrained(model_name)
        model = DistilBertModel.from_pretrained(model_name)
        model.eval()  # Set to evaluation mode (frozen weights)
        
        # Ensure model is on CPU
        model = model.cpu()
        for param in model.parameters():
            param.requires_grad = False
        
        return model, tokenizer
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {e}")

def run_forward_pass(model, tokenizer):
    """Run a forward pass on a sample input."""
    sample_text = "This is a test sentence for intent classification."
    inputs = tokenizer(sample_text, return_tensors="pt", padding=True, truncation=True)
    
    # Ensure inputs are on CPU
    inputs = {k: v.cpu() for k, v in inputs.items()}
    
    start_time = time.time()
    with torch.no_grad():
        outputs = model(**inputs)
    end_time = time.time()
    
    return {
        "last_hidden_state_shape": list(outputs.last_hidden_state.shape),
        "pooler_output_shape": list(outputs.pooler_output.shape) if hasattr(outputs, 'pooler_output') else None,
        "inference_time_ms": round((end_time - start_time) * 1000, 2)
    }

def validate_weights(model):
    """Validate that model weights are properly loaded and frozen."""
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    # Check for any GPU tensors in model parameters
    for name, param in model.named_parameters():
        if param.is_cuda:
            return False, f"GPU tensor detected in parameter: {name}"
        if param.dtype != torch.float32:
            return False, f"Non-default precision detected in parameter: {name} ({param.dtype})"
    
    return True, {
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "all_frozen": trainable_params == 0
    }

def main():
    results = {
        "status": "success",
        "checks": {},
        "model_info": {},
        "forward_pass": {},
        "validation_details": {}
    }

    try:
        # Check 1: No GPU
        gpu_ok, gpu_msg = check_no_gpu()
        results["checks"]["no_gpu"] = {"passed": gpu_ok, "message": gpu_msg}
        if not gpu_ok:
            raise RuntimeError(gpu_msg)

        # Check 2: No quantization
        quant_ok, quant_msg = check_no_quantization()
        results["checks"]["no_quantization"] = {"passed": quant_ok, "message": quant_msg}
        if not quant_ok:
            raise RuntimeError(quant_msg)

        # Load model
        print("Loading DistilBERT model...")
        model, tokenizer = load_model_and_tokenizer()
        
        # Validate weights
        weights_ok, weights_info = validate_weights(model)
        if isinstance(weights_info, dict):
            results["validation_details"]["weights"] = weights_info
        else:
            results["checks"]["weights_valid"] = {"passed": weights_ok, "message": str(weights_info)}
            if not weights_ok:
                raise RuntimeError(str(weights_info))
        results["checks"]["weights_valid"] = {"passed": True, "message": "Weights are valid and frozen"}

        # Run forward pass
        print("Running forward pass...")
        forward_info = run_forward_pass(model, tokenizer)
        results["forward_pass"] = forward_info

        # Model info
        results["model_info"] = {
            "name": "distilbert-base-uncased",
            "precision": "float32",
            "device": "cpu",
            "frozen": True
        }

        print("Validation completed successfully.")

    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        print(f"Validation failed: {e}")

    # Write results to JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results written to {OUTPUT_FILE}")
    return 0 if results["status"] == "success" else 1

if __name__ == "__main__":
    sys.exit(main())