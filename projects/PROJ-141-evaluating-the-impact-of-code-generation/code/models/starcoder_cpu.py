"""
StarCoder CPU-only inference wrapper and verification script.

This module implements:
1. Verification that the selected StarCoder model size is <= 1GB
2. CPU-tractability verification (inference time < 60s for a standard prompt)
3. A CPU-only inference wrapper for use in the experiment pipeline
"""
import os
import sys
import json
import time
import traceback
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Configuration
MODEL_REPO = "bigcode/starcoderbase-1b"  # 1B parameter model, expected ~2GB in FP16, ~1GB in INT8
MAX_MODEL_SIZE_MB = 1024  # 1GB limit
MAX_INFERENCE_TIME_S = 60  # 60 second limit for CPU tractability
OUTPUT_DIR = Path("data")
VERIFICATION_OUTPUT = OUTPUT_DIR / "starcoder_verification.json"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_model_size_mb(repo_id: str = MODEL_REPO) -> Tuple[float, Optional[str]]:
    """
    Calculate the total size of the model files in MB.
    
    Args:
        repo_id: HuggingFace model repository ID
        
    Returns:
        Tuple of (size_in_mb, error_message)
        If successful, error_message is None.
    """
    try:
        from huggingface_hub import snapshot_download
        import tempfile
        
        # Download model files to a temporary directory to measure size
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Download only necessary files (skip training artifacts)
                allow_patterns = ["*.safetensors", "*.bin", "*.json", "*.txt", "tokenizer*"]
                snapshot_download(
                    repo_id=repo_id,
                    cache_dir=temp_dir,
                    allow_patterns=allow_patterns
                )
                
                # Calculate total size
                total_size = 0
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                
                size_mb = total_size / (1024 * 1024)
                logger.info(f"Model {repo_id} size: {size_mb:.2f} MB")
                return size_mb, None
            except Exception as e:
                logger.error(f"Error downloading model for size check: {e}")
                return 0.0, str(e)
                
    except ImportError:
        logger.error("huggingface_hub not installed. Install with: pip install huggingface_hub")
        return 0.0, "huggingface_hub not installed"
    except Exception as e:
        logger.error(f"Error checking model size: {e}")
        return 0.0, str(e)


def load_model(repo_id: str = MODEL_REPO):
    """
    Load the StarCoder model for CPU-only inference.
    
    Args:
        repo_id: HuggingFace model repository ID
        
    Returns:
        Loaded model and tokenizer
    """
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        # Check for GPU availability and force CPU
        if torch.cuda.is_available():
            logger.warning("GPU detected but forcing CPU-only mode as per task requirements")
        
        device = torch.device("cpu")
        
        logger.info(f"Loading model {repo_id} on CPU...")
        start_time = time.time()
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(repo_id)
        
        # Load model with appropriate settings for CPU
        # Use float32 for stability on CPU, or float16 if memory allows
        try:
            model = AutoModelForCausalLM.from_pretrained(
                repo_id,
                torch_dtype=torch.float32,  # CPU friendly
                low_cpu_mem_usage=True,
                device_map="cpu"
            )
        except Exception as e:
            # Fallback to default dtype if float32 fails
            logger.warning(f"Could not load with float32, trying default: {e}")
            model = AutoModelForCausalLM.from_pretrained(
                repo_id,
                low_cpu_mem_usage=True,
                device_map="cpu"
            )
        
        load_time = time.time() - start_time
        logger.info(f"Model loaded in {load_time:.2f} seconds")
        
        return model, tokenizer
        
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Install required packages: pip install torch transformers")
        raise
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        traceback.print_exc()
        raise


def run_inference(
    model, 
    tokenizer, 
    prompt: str, 
    max_new_tokens: int = 50,
    temperature: float = 0.7,
    top_p: float = 0.95
) -> Dict[str, Any]:
    """
    Run CPU-only inference with the loaded model.
    
    Args:
        model: Loaded model
        tokenizer: Loaded tokenizer
        prompt: Input prompt
        max_new_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        top_p: Top-p sampling parameter
        
    Returns:
        Dictionary with generated text and timing information
    """
    import torch
    
    try:
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Move to CPU (should already be there, but explicit)
        inputs = {k: v.to("cpu") for k, v in inputs.items()}
        
        # Generate
        start_time = time.time()
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        inference_time = time.time() - start_time
        
        # Decode output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the generated part (remove prompt)
        generated_part = generated_text[len(prompt):] if generated_text.startswith(prompt) else generated_text
        
        return {
            "generated_text": generated_part,
            "inference_time_s": inference_time,
            "tokens_generated": len(outputs[0]) - len(inputs["input_ids"][0]),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        traceback.print_exc()
        return {
            "generated_text": None,
            "inference_time_s": None,
            "tokens_generated": None,
            "success": False,
            "error": str(e)
        }


def verify_cpu_tractability(
    model, 
    tokenizer, 
    test_prompt: str = "def fibonacci(n):\n    if n <= 1:\n        return n\n    else:\n        return",
    max_time: float = MAX_INFERENCE_TIME_S
) -> Dict[str, Any]:
    """
    Verify that the model can perform inference within the time limit on CPU.
    
    Args:
        model: Loaded model
        tokenizer: Loaded tokenizer
        test_prompt: Prompt to use for testing
        max_time: Maximum allowed inference time in seconds
        
    Returns:
        Dictionary with verification results
    """
    logger.info("Running CPU tractability verification...")
    
    # Run inference
    result = run_inference(model, tokenizer, test_prompt)
    
    if not result["success"]:
        return {
            "tractable": False,
            "reason": "Inference failed",
            "error": result.get("error", "Unknown error"),
            "inference_time_s": None
        }
    
    inference_time = result["inference_time_s"]
    tractable = inference_time <= max_time
    
    logger.info(f"Inference completed in {inference_time:.2f}s (limit: {max_time}s)")
    
    return {
        "tractable": tractable,
        "reason": "Inference completed within time limit" if tractable else f"Inference took {inference_time:.2f}s, exceeding limit of {max_time}s",
        "inference_time_s": inference_time,
        "tokens_generated": result["tokens_generated"],
        "test_prompt": test_prompt
    }


def main():
    """
    Main entry point for StarCoder CPU verification.
    
    Performs:
    1. Model size verification (<= 1GB)
    2. CPU tractability verification (inference < 60s)
    3. Writes results to data/starcoder_verification.json
    """
    logger.info("=" * 60)
    logger.info("StarCoder CPU Verification Script")
    logger.info("=" * 60)
    
    results = {
        "model_repo": MODEL_REPO,
        "size_check": {},
        "tractability_check": {},
        "overall_status": "unknown",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    }
    
    # Step 1: Check model size
    logger.info("Step 1: Checking model size...")
    size_mb, size_error = get_model_size_mb(MODEL_REPO)
    
    if size_error:
        results["size_check"] = {
            "passed": False,
            "size_mb": None,
            "error": size_error
        }
        results["overall_status"] = "failed"
        logger.error(f"Size check failed: {size_error}")
        
        # Write results and exit
        with open(VERIFICATION_OUTPUT, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results written to {VERIFICATION_OUTPUT}")
        return 1
    
    size_passed = size_mb <= MAX_MODEL_SIZE_MB
    results["size_check"] = {
        "passed": size_passed,
        "size_mb": size_mb,
        "limit_mb": MAX_MODEL_SIZE_MB
    }
    
    if not size_passed:
        logger.error(f"Model size {size_mb:.2f}MB exceeds limit {MAX_MODEL_SIZE_MB}MB")
        results["overall_status"] = "failed"
        
        # Write results and exit
        with open(VERIFICATION_OUTPUT, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results written to {VERIFICATION_OUTPUT}")
        return 1
    
    logger.info(f"Model size check passed: {size_mb:.2f}MB <= {MAX_MODEL_SIZE_MB}MB")
    
    # Step 2: Load model and check tractability
    logger.info("Step 2: Loading model and checking CPU tractability...")
    try:
        model, tokenizer = load_model(MODEL_REPO)
    except Exception as e:
        results["tractability_check"] = {
            "passed": False,
            "error": str(e)
        }
        results["overall_status"] = "failed"
        logger.error(f"Failed to load model: {e}")
        
        # Write results and exit
        with open(VERIFICATION_OUTPUT, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results written to {VERIFICATION_OUTPUT}")
        return 1
    
    # Run tractability check
    tractability_result = verify_cpu_tractability(model, tokenizer)
    results["tractability_check"] = tractability_result
    
    if not tractability_result["tractable"]:
        logger.error(f"Tractability check failed: {tractability_result['reason']}")
        results["overall_status"] = "failed"
    else:
        logger.info("Tractability check passed")
        results["overall_status"] = "passed"
    
    # Write results
    with open(VERIFICATION_OUTPUT, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("=" * 60)
    logger.info(f"Verification complete: {results['overall_status']}")
    logger.info(f"Results written to {VERIFICATION_OUTPUT}")
    logger.info("=" * 60)
    
    return 0 if results["overall_status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())