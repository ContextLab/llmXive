"""
Inference runner for LLM code understanding tasks.

Implements CPU-based inference with low-bit quantization, context truncation,
and integration with progressive sample reduction logic for OOM handling.
"""
import gc
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

# Project imports
from utils.config import get_config, get_path, set_seed
from utils.logger import get_logger, log_event
from extractors.data_loader import load_codexglue_samples

# Constants
MAX_CONTEXT_TOKENS = 2048
DEFAULT_MODEL_ID = "microsoft/CodeBERTa-base"  # Placeholder; can be overridden
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

logger = get_logger(__name__)


def load_model_quantized(
    model_id: str,
    device_map: str = "cpu",
    max_memory: Optional[Dict[str, int]] = None
) -> Tuple[Any, Any]:
    """
    Load a large language model with low-bit quantization on CPU.
    
    Args:
        model_id: HuggingFace model identifier
        device_map: Device placement strategy (default: "cpu")
        max_memory: Optional memory constraints per device
    
    Returns:
        Tuple of (model, tokenizer)
    
    Raises:
        RuntimeError: If model loading fails or OOM occurs
    """
    logger.info(f"Loading model {model_id} on {device_map} with quantization")
    
    # Configure quantization for CPU (4-bit if bitsandbytes available, else fallback)
    try:
        nbits_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float32,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
    except Exception as e:
        logger.warning(f"BitsAndBytesConfig failed ({e}), attempting standard loading")
        nbits_config = None

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        # Set pad token if not exists
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model_kwargs = {
            "device_map": device_map,
            "torch_dtype": torch.float32,  # Force float32 for CPU stability
            "low_cpu_mem_usage": True,
        }
        
        if nbits_config:
            model_kwargs["quantization_config"] = nbits_config

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            **model_kwargs
        )
        
        if max_memory:
            model.set_max_memory(max_memory)

        logger.info(f"Model loaded successfully: {model_id}")
        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {e}")
        raise RuntimeError(f"Model loading failed: {e}")


def truncate_context(
    input_text: str,
    tokenizer: Any,
    max_tokens: int = MAX_CONTEXT_TOKENS
) -> str:
    """
    Truncate input text to fit within max_tokens limit.
    
    Args:
        input_text: Original input text
        tokenizer: Tokenizer instance
        max_tokens: Maximum number of tokens allowed
    
    Returns:
        Truncated input text
    """
    tokens = tokenizer.encode(input_text, return_tensors="pt", truncation=False)
    
    if tokens.shape[1] <= max_tokens:
        return input_text
    
    # Truncate by keeping the first max_tokens - 1 tokens (reserve 1 for EOS)
    truncated_tokens = tokens[:, :max_tokens - 1]
    truncated_text = tokenizer.decode(truncated_tokens[0], skip_special_tokens=True)
    
    logger.debug(f"Context truncated from {tokens.shape[1]} to {max_tokens - 1} tokens")
    return truncated_text


def run_inference_single(
    model: Any,
    tokenizer: Any,
    snippet: str,
    max_new_tokens: int = 50,
    temperature: float = 0.7,
    do_sample: bool = True
) -> Optional[str]:
    """
    Run inference on a single code snippet.
    
    Args:
        model: Loaded model instance
        tokenizer: Loaded tokenizer instance
        snippet: Code snippet to process
        max_new_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        do_sample: Whether to sample or use greedy decoding
    
    Returns:
        Generated text or None if failed
    """
    try:
        # Truncate context
        truncated_input = truncate_context(snippet, tokenizer)
        
        # Tokenize
        inputs = tokenizer(
            truncated_input,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_CONTEXT_TOKENS
        ).to(model.device)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        # Decode
        generated_text = tokenizer.decode(
            outputs[0, inputs.input_ids.shape[1]:],
            skip_special_tokens=True
        )
        
        return generated_text

    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            logger.error(f"OOM during inference: {e}")
            raise  # Re-raise to trigger OOM handling
        logger.error(f"Runtime error during inference: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during inference: {e}")
        return None


def run_inference_with_retry(
    model: Any,
    tokenizer: Any,
    snippet: str,
    max_retries: int = MAX_RETRIES
) -> Optional[str]:
    """
    Run inference with retry logic for transient failures.
    
    Args:
        model: Loaded model instance
        tokenizer: Loaded tokenizer instance
        snippet: Code snippet to process
        max_retries: Maximum number of retry attempts
    
    Returns:
        Generated text or None if all retries failed
    """
    for attempt in range(max_retries):
        try:
            result = run_inference_single(model, tokenizer, snippet)
            if result is not None:
                return result
            
            logger.warning(f"Inference attempt {attempt + 1}/{max_retries} failed, retrying...")
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                # Don't retry OOM - it requires sample reduction
                logger.error(f"OOM on attempt {attempt + 1}, not retrying")
                raise
            logger.warning(f"Runtime error on attempt {attempt + 1}: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(RETRY_DELAY)
    
    logger.error(f"All {max_retries} inference attempts failed")
    return None


def cleanup_memory():
    """
    Clear GPU/CPU memory and run garbage collection.
    """
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.debug("Memory cleanup completed")


def run_inference_stage(
    model_id: str = DEFAULT_MODEL_ID,
    max_samples_per_repo: int = 5,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute the full inference stage on CodeXGLUE samples.
    
    Args:
        model_id: HuggingFace model identifier
        max_samples_per_repo: Maximum samples to process per repository
        output_path: Path to save results (default: data/results/inference_results.json)
    
    Returns:
        Dictionary containing inference results and metadata
    """
    start_time = time.time()
    config = get_config()
    
    # Set random seed for reproducibility
    set_seed(config.get("seed", 42))
    
    # Load data
    logger.info("Loading CodeXGLUE samples...")
    try:
        samples = load_codexglue_samples(max_samples_per_repo)
    except Exception as e:
        logger.error(f"Failed to load samples: {e}")
        return {"success": False, "error": str(e), "samples_processed": 0}
    
    if not samples:
        logger.warning("No samples found to process")
        return {"success": True, "samples_processed": 0, "results": []}
    
    # Load model
    model, tokenizer = load_model_quantized(model_id)
    
    results = []
    successful_count = 0
    failed_count = 0
    
    for sample in samples:
        snippet = sample.get("code", "")
        repo_id = sample.get("repo_id", "unknown")
        sample_id = sample.get("id", "unknown")
        
        if not snippet:
            logger.warning(f"Empty snippet for {repo_id}/{sample_id}, skipping")
            failed_count += 1
            continue
        
        logger.info(f"Processing {repo_id}/{sample_id}...")
        
        try:
            # Run inference with retry
            generated = run_inference_with_retry(model, tokenizer, snippet)
            
            if generated:
                results.append({
                    "repo_id": repo_id,
                    "sample_id": sample_id,
                    "input_snippet": snippet[:500],  # Truncate for storage
                    "generated_code": generated,
                    "status": "success",
                    "timestamp": time.time()
                })
                successful_count += 1
            else:
                results.append({
                    "repo_id": repo_id,
                    "sample_id": sample_id,
                    "status": "failed",
                    "error": "Inference returned None",
                    "timestamp": time.time()
                })
                failed_count += 1
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.critical(f"OOM encountered for {repo_id}/{sample_id}")
                # Trigger progressive sample reduction via main.py logic
                log_event("oom_detected", {
                    "repo_id": repo_id,
                    "sample_id": sample_id,
                    "action": "trigger_sample_reduction"
                })
                raise  # Re-raise to let main.py handle reduction
            else:
                logger.error(f"Runtime error for {repo_id}/{sample_id}: {e}")
                failed_count += 1
        
        # Cleanup after each sample
        cleanup_memory()
    
    # Save results
    if output_path is None:
        output_path = str(get_path("data/results/inference_results.json"))
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        import json
        json.dump({
            "model_id": model_id,
            "max_samples_per_repo": max_samples_per_repo,
            "successful_count": successful_count,
            "failed_count": failed_count,
            "total_processed": len(samples),
            "duration_seconds": time.time() - start_time,
            "results": results
        }, f, indent=2, default=str)
    
    logger.info(f"Inference stage complete: {successful_count} successful, {failed_count} failed")
    return {
        "success": True,
        "samples_processed": len(samples),
        "successful": successful_count,
        "failed": failed_count,
        "output_path": str(output_file)
    }


def main():
    """
    Main entry point for the inference runner.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run LLM inference on code snippets")
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_ID,
        help="HuggingFace model ID"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=5,
        help="Maximum samples per repository"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_inference_stage(
            model_id=args.model,
            max_samples_per_repo=args.max_samples,
            output_path=args.output
        )
        
        if result.get("success"):
            print(f"Success: {result['successful']} / {result['samples_processed']} samples processed")
            sys.exit(0)
        else:
            print(f"Failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print("CRITICAL: Out of memory - sample reduction required")
            # Signal to main.py to trigger progressive reduction
            sys.exit(2)  # Special exit code for OOM
        else:
            print(f"Runtime error: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()