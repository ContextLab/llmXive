"""
JaCoText Model Verification and CPU-Only Inference Wrapper.

This module verifies the JaCoText model size is <= 1GB and performs a CPU-tractability
test by running a dummy inference. It writes verification results to data/jacotext_verification.json.

Source: Hugging Face (https://huggingface.co/declan-lee/jacotext)
"""

import os
import sys
import json
import time
import traceback
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/jacotext_verification.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MODEL_ID = "declan-lee/jacotext"
MAX_MODEL_SIZE_BYTES = 1024 * 1024 * 1024  # 1 GB
MAX_INFERENCE_TIME_SECONDS = 60.0
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "jacotext_verification.json"
DUMMY_PROMPT = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return "

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_model_size_mb(model_id: str = MODEL_ID) -> float:
    """
    Fetches the model size in MB from Hugging Face Hub API.
    Returns the total size of all model files in MB.
    """
    try:
        import requests
        api_url = f"https://huggingface.co/api/models/{model_id}"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # HuggingFace API returns 'siblings' with 'rfilename' and 'size' if available
        # Sometimes size is not directly in the summary, we might need to check specific files
        # or rely on the 'weight' if available in a specific tag, but standard API usually gives file list.
        # If 'siblings' is missing or size is null, we try to fetch file info individually or estimate.
        
        total_bytes = 0
        files_info = []
        
        if 'siblings' in data:
            for sibling in data['siblings']:
                rfilename = sibling.get('rfilename', '')
                size = sibling.get('size', 0)
                if size is None:
                    # If size is not in the summary, we might need to fetch HEAD or skip
                    # For now, assume 0 or try to get from tree API if needed.
                    # Standard HF API usually populates this.
                    logger.warning(f"Size missing for {rfilename}, skipping size count.")
                    continue
                total_bytes += size
                files_info.append({"file": rfilename, "size_mb": size / (1024*1024)})
        
        size_mb = total_bytes / (1024 * 1024)
        logger.info(f"Model {model_id} total size: {size_mb:.2f} MB ({total_bytes} bytes)")
        return size_mb
        
    except Exception as e:
        logger.error(f"Failed to fetch model size from HF API: {e}")
        # Fallback: Try to check if a local cached version exists (optional)
        # But for verification, we need the remote size.
        raise RuntimeError(f"Could not determine model size for {model_id}: {e}")

def load_model():
    """
    Loads the JaCoText model on CPU.
    Returns the model and tokenizer.
    """
    try:
        logger.info("Attempting to load JaCoText model on CPU...")
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        # Force CPU
        device = torch.device("cpu")
        
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, 
            torch_dtype=torch.float32, # Force float32 for CPU compatibility if needed, or auto
            device_map="cpu",
            trust_remote_code=True
        )
        
        model.to(device)
        model.eval()
        logger.info("Model loaded successfully.")
        return model, tokenizer
    except ImportError as e:
        logger.error(f"Missing dependency: {e}. Please install torch and transformers.")
        raise
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        traceback.print_exc()
        raise

def run_inference(model, tokenizer, prompt: str = DUMMY_PROMPT, max_new_tokens: int = 50) -> Dict[str, Any]:
    """
    Runs a dummy inference to measure CPU tractability.
    Returns timing and generation results.
    """
    import torch
    
    logger.info(f"Running inference with prompt: '{prompt[:50]}...'")
    start_time = time.time()
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        # Move inputs to CPU explicitly
        inputs = {k: v.to("cpu") for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=0.9,
                pad_token_id=tokenizer.eos_token_id
            )
        
        generated_ids = outputs[:, inputs['input_ids'].shape[1]:]
        generated_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Inference completed in {duration:.2f} seconds.")
        logger.info(f"Generated text: {generated_text[:100]}...")
        
        return {
            "success": True,
            "duration_seconds": duration,
            "generated_text": generated_text,
            "tokens_generated": len(generated_ids[0])
        }
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "duration_seconds": time.time() - start_time
        }

def verify_cpu_tractability() -> Dict[str, Any]:
    """
    Main verification routine:
    1. Check model size <= 1GB.
    2. Load model.
    3. Run inference.
    4. Check inference time <= 60s.
    5. Write results to data/jacotext_verification.json.
    """
    results = {
        "model_id": MODEL_ID,
        "verification_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "size_check": {
            "passed": False,
            "size_mb": 0.0,
            "limit_mb": 1024.0,
            "error": None
        },
        "load_check": {
            "passed": False,
            "error": None
        },
        "inference_check": {
            "passed": False,
            "duration_seconds": 0.0,
            "limit_seconds": MAX_INFERENCE_TIME_SECONDS,
            "error": None
        },
        "overall_status": "failed",
        "message": ""
    }

    try:
        # 1. Size Check
        size_mb = get_model_size_mb()
        results["size_check"]["size_mb"] = size_mb
        if size_mb <= 1024.0:
            results["size_check"]["passed"] = True
            logger.info(f"Size check PASSED: {size_mb:.2f} MB <= 1024 MB")
        else:
            results["size_check"]["passed"] = False
            results["overall_status"] = "failed"
            results["message"] = f"Model size {size_mb:.2f} MB exceeds 1GB limit."
            logger.error(results["message"])
            return results

        # 2. Load Check
        try:
            model, tokenizer = load_model()
            results["load_check"]["passed"] = True
            logger.info("Model load check PASSED")
        except Exception as e:
            results["load_check"]["error"] = str(e)
            results["overall_status"] = "failed"
            results["message"] = f"Model load failed: {e}"
            logger.error(results["message"])
            return results

        # 3. Inference Check
        inference_result = run_inference(model, tokenizer)
        results["inference_check"]["duration_seconds"] = inference_result["duration_seconds"]
        
        if inference_result["success"]:
            if inference_result["duration_seconds"] <= MAX_INFERENCE_TIME_SECONDS:
                results["inference_check"]["passed"] = True
                results["overall_status"] = "passed"
                results["message"] = "All checks passed. Model is CPU-tractable."
                logger.info("Inference check PASSED")
            else:
                results["inference_check"]["passed"] = False
                results["overall_status"] = "failed"
                results["message"] = f"Inference too slow: {inference_result['duration_seconds']:.2f}s > {MAX_INFERENCE_TIME_SECONDS}s"
                logger.error(results["message"])
        else:
            results["inference_check"]["error"] = inference_result.get("error", "Unknown error")
            results["overall_status"] = "failed"
            results["message"] = f"Inference execution failed: {results['inference_check']['error']}"
            logger.error(results["message"])

    except Exception as e:
        results["overall_status"] = "failed"
        results["message"] = f"Verification process crashed: {e}"
        logger.error(results["message"])
        traceback.print_exc()

    # Write results to file
    try:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Verification results written to {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Failed to write results to {OUTPUT_FILE}: {e}")

    return results

def main():
    """Entry point for the script."""
    logger.info("Starting JaCoText CPU Verification...")
    results = verify_cpu_tractability()
    print(json.dumps(results, indent=2))
    sys.exit(0 if results["overall_status"] == "passed" else 1)

if __name__ == "__main__":
    main()