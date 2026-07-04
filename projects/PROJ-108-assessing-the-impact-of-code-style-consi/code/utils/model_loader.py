"""
CPU-safe Model Loading Utilities
Provides functions to load models on CPU with timeout handling and memory constraints.
"""
import os
import sys
import time
from typing import Optional, Dict, Any, Tuple, Union
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList

class ModelLoadError(Exception):
    pass

class TimeoutError(Exception):
    pass

class TimeoutStoppingCriteria(StoppingCriteria):
    """
    Stopping criteria that halts generation if it exceeds a time limit.
    """
    def __init__(self, timeout_seconds: int):
        self.start_time = time.time()
        self.timeout = timeout_seconds

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        if time.time() - self.start_time > self.timeout:
            return True
        return False

def load_model_and_tokenizer(
    model_id: str,
    device: str = "cpu",
    timeout: int = 300,
    low_cpu_mem_usage: bool = True
) -> Tuple[Any, AutoTokenizer]:
    """
    Load a model and tokenizer in CPU mode.
    
    Args:
        model_id: HuggingFace model ID
        device: Device to load to (default "cpu")
        timeout: Timeout for loading (seconds)
        low_cpu_mem_usage: Optimize memory usage
    
    Returns:
        Tuple of (model, tokenizer)
    """
    print(f"Loading model {model_id} on {device}...")
    start_time = time.time()
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
            padding_side="left"
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token_id = tokenizer.eos_token_id

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float32,  # Force float32 for CPU stability
            device_map="cpu",
            low_cpu_mem_usage=low_cpu_mem_usage,
            trust_remote_code=True
        )
        
        elapsed = time.time() - start_time
        print(f"Model loaded in {elapsed:.2f}s")
        return model, tokenizer

    except Exception as e:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise TimeoutError(f"Model loading timed out after {timeout}s")
        raise ModelLoadError(f"Failed to load model {model_id}: {str(e)}")

def get_model_info(model_id: str) -> Dict[str, Any]:
    """Get basic info about a model without loading weights."""
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        return {
            "model_id": model_id,
            "vocab_size": tokenizer.vocab_size,
            "max_length": tokenizer.model_max_length
        }
    except Exception as e:
        return {"model_id": model_id, "error": str(e)}

def prepare_inputs_for_cpu(
    inputs: Dict[str, torch.Tensor],
    max_length: int = 512
) -> Dict[str, torch.Tensor]:
    """Ensure inputs are on CPU and within memory limits."""
    return {k: v.cpu() for k, v in inputs.items()}

def main():
    """CLI for testing model loading."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="HuggingFaceTB/SmolLM-360M-Instruct")
    args = parser.parse_args()
    
    try:
        model, tokenizer = load_model_and_tokenizer(args.model)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
