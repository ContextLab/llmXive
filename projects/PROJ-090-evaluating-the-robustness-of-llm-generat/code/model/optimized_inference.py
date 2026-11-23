"""
Optimized model inference with strict memory management.

This module wraps the standard inference logic with memory monitoring
to ensure the process stays under the 6GB CPU limit.
"""
import os
import sys
import logging
import torch
import gc
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import existing infrastructure
from config import get_model_path, get_seed_global
from utils.logging import get_inference_logger
from utils.memory_monitor import (
    get_current_memory_mb, 
    check_memory_limit, 
    set_soft_memory_limit, 
    MEMORY_LIMIT_GB,
    memory_guard
)

# Constants
MAX_BATCH_SIZE = 1
MEMORY_CHECK_INTERVAL = 5  # Check every N generations

logger = get_inference_logger()

def load_model_optimized(model_path: Optional[str] = None, dtype: torch.dtype = torch.float32):
    """
    Load the model with memory optimization settings.
    
    Args:
        model_path: Path to the model.
        dtype: Data type for model weights.
        
    Returns:
        The loaded model.
        
    Raises:
        MemoryError: If loading the model exceeds the memory limit.
    """
    if model_path is None:
        model_path = get_model_path()
        
    logger.info(f"Loading model from {model_path}...")
    
    # Pre-check memory before loading
    current_mem = get_current_memory_mb()
    logger.info(f"Memory before load: {current_mem:.2f} MB")
    
    if current_mem > (MEMORY_LIMIT_GB * 1024 * 0.8):
        logger.warning(f"High memory usage before load: {current_mem:.2f} MB. Proceeding with caution.")
    
    # Set soft limit to prevent OS OOM kill
    set_soft_memory_limit(MEMORY_LIMIT_GB)
    
    try:
        # Attempt to load model with 4-bit quantization if available
        # Note: The existing inference.py uses bitsandbytes. We wrap that logic here
        # to ensure we don't exceed limits during the load phase.
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from bitsandbytes.nn import Linear4bit
        
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        
        # Force CPU offload and 4-bit quantization to stay under 6GB
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="cpu",  # Force CPU to avoid CUDA memory issues
            load_in_4bit=True,  # 4-bit quantization
            bnb_4bit_compute_dtype=torch.float32,
            bnb_4bit_quant_type="nf4",
            trust_remote_code=True
        )
        
        # Post-load check
        current_mem = get_current_memory_mb()
        logger.info(f"Memory after load: {current_mem:.2f} MB")
        
        if not check_memory_limit(MEMORY_LIMIT_GB):
            raise MemoryError(f"Model load exceeded {MEMORY_LIMIT_GB} GB limit.")
            
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        raise

def generate_code_optimized(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.8,
    top_p: float = 0.95
) -> str:
    """
    Generate code with memory monitoring.
    
    Args:
        model: The loaded model.
        tokenizer: The loaded tokenizer.
        prompt: The input prompt.
        max_new_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature.
        top_p: Top-p sampling parameter.
        
    Returns:
        Generated code string.
    """
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids
    
    with torch.no_grad():
        # Monitor memory before generation
        if not check_memory_limit(MEMORY_LIMIT_GB):
            raise MemoryError(f"Memory limit exceeded before generation.")
        
        outputs = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
    # Post-generation cleanup
    del input_ids, outputs
    gc.collect()
    
    return generated_text

def run_generation_loop_optimized(
    tasks: List[Dict[str, Any]],
    model_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run the generation loop with memory safeguards.
    
    Args:
        tasks: List of task dictionaries.
        model_path: Path to the model.
        output_path: Path to save results.
        
    Returns:
        List of results dictionaries.
    """
    logger.info(f"Starting optimized generation loop for {len(tasks)} tasks.")
    
    model, tokenizer = load_model_optimized(model_path)
    
    results = []
    for i, task in enumerate(tasks):
        logger.info(f"Processing task {i+1}/{len(tasks)}: {task.get('task_id', 'unknown')}")
        
        # Check memory every few tasks
        if i % MEMORY_CHECK_INTERVAL == 0:
            if not check_memory_limit(MEMORY_LIMIT_GB):
                logger.error(f"Memory limit exceeded at task {i+1}. Stopping.")
                break
        
        try:
            with memory_guard(MEMORY_LIMIT_GB):
                prompt = task.get("prompt", "")
                generated_code = generate_code_optimized(model, tokenizer, prompt)
                
                results.append({
                    "task_id": task.get("task_id"),
                    "generated_code": generated_code,
                    "status": "success"
                })
        except MemoryError as e:
            logger.error(f"Memory error at task {i+1}: {e}")
            results.append({
                "task_id": task.get("task_id"),
                "generated_code": "",
                "status": "OOM",
                "error": str(e)
            })
            break
        except Exception as e:
            logger.error(f"Error processing task {i+1}: {e}")
            results.append({
                "task_id": task.get("task_id"),
                "generated_code": "",
                "status": "error",
                "error": str(e)
            })
    
    # Save results
    if output_path:
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_path}")
    
    return results

def main() -> None:
    """CLI entry point for optimized inference."""
    # Example usage
    logger.info("Memory Monitor & Optimized Inference Module Loaded")
    logger.info(f"Memory Limit: {MEMORY_LIMIT_GB} GB")
    logger.info(f"Current Usage: {get_current_memory_mb():.2f} MB")
    
    # Check if limit is set
    if check_memory_limit(MEMORY_LIMIT_GB):
        logger.info("Memory usage is within safe limits.")
    else:
        logger.warning("Memory usage is currently above the safe limit.")

if __name__ == "__main__":
    main()
