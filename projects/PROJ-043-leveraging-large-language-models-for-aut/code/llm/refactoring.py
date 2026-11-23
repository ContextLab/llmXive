"""
LLM-based code refactoring using HuggingFace Inference API.
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import requests

from config import Config, get_secret
from utils.logging import get_logger, LLMRefactoringError, timed_operation
from utils.cache import cache_get, cache_set, compute_hash
from models.entities import FunctionSample

logger = get_logger(__name__)

# Configuration
MAX_ATTEMPTS = 400
MIN_VALID_FUNCTIONS = 100
BATCH_SIZE = 10
TIMEOUT_SECONDS = 60

def _build_prompt(code: str) -> str:
    """Build zero-shot refactoring prompt."""
    return f"""You are an expert Python refactoring assistant.
Refactor the following Python function to improve its quality (readability, maintainability, PEP-8 compliance) while preserving functionality.
Do not change the function signature or behavior.
Only return the refactored code, no explanations.

Original code:
```python
{code}
```

Refactored code:
```python
"""

def _call_llm_api(prompt: str, model: str = "WizardCoder-Python-13B") -> str:
    """
    Call HuggingFace Inference API with retry logic and exponential backoff.
    Raises LLMRefactoringError on failure.
    """
    api_key = get_secret("HF_API_KEY")
    if not api_key:
        raise LLMRefactoringError("HF_API_KEY not configured")

    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {api_key}"}

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.2,
            "do_sample": True,
            "top_p": 0.95,
            "return_full_text": False
        }
    }

    attempt = 0
    while attempt < MAX_ATTEMPTS:
        attempt += 1
        try:
            logger.debug(f"API attempt {attempt}/{MAX_ATTEMPTS}")
            response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS)

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "").strip()
                elif isinstance(result, dict) and "generated_text" in result:
                    return result["generated_text"].strip()
                else:
                    logger.warning(f"Unexpected API response format: {result}")
                    raise LLMRefactoringError("Invalid API response format")

            elif response.status_code == 503:
                # Model loading, wait and retry
                wait_time = min(30 * (2 ** attempt), 300)
                logger.info(f"Model loading (503). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            elif response.status_code == 429:
                # Rate limit
                wait_time = min(60 * (2 ** attempt), 300)
                logger.warning(f"Rate limited (429). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            else:
                # Other errors
                error_msg = f"API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise LLMRefactoringError(error_msg)

        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout on attempt {attempt}")
            time.sleep(5 * attempt)
            continue
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed on attempt {attempt}: {e}")
            time.sleep(5 * attempt)
            continue

    raise LLMRefactoringError(f"Failed after {MAX_ATTEMPTS} attempts")

def _parse_llm_output(output: str, original_code: str) -> str:
    """
    Parse LLM output to extract refactored code.
    Handles markdown code blocks and clean extraction.
    """
    # Remove markdown code block markers if present
    if output.startswith("```python"):
        output = output[9:]
    if output.startswith("```"):
        output = output[3:]
    if output.endswith("```"):
        output = output[:-3]

    output = output.strip()

    # Basic validation: should not be empty and should contain Python-like content
    if not output or len(output) < 10:
        raise LLMRefactoringError("Refactored code is too short or empty")

    return output

def refactor_single_function(sample: Dict[str, Any]) -> Dict[str, Any]:
    """
    Refactor a single function sample with caching.
    Returns a dict with original_code, refactored_code, status, and hash.
    """
    original_code = sample.get("code", "")
    if not original_code:
        raise LLMRefactoringError("Missing code in sample")

    # Compute hash for caching
    func_hash = compute_hash(original_code)

    # Check cache first
    cached_result = cache_get(func_hash)
    if cached_result is not None:
        logger.info(f"Cache hit for hash {func_hash[:8]}...")
        return cached_result

    logger.info(f"Cache miss for hash {func_hash[:8]}...; calling API")

    try:
        prompt = _build_prompt(original_code)
        refactored_raw = _call_llm_api(prompt)
        refactored_code = _parse_llm_output(refactored_raw, original_code)

        result = {
            "original_code": original_code,
            "refactored_code": refactored_code,
            "function_hash": func_hash,
            "status": "success"
        }

        # Cache the result
        cache_set(func_hash, result)

        return result

    except LLMRefactoringError as e:
        logger.error(f"Refactoring failed for hash {func_hash[:8]}...: {e}")
        return {
            "original_code": original_code,
            "refactored_code": None,
            "function_hash": func_hash,
            "status": "failed",
            "error": str(e)
        }

def refactor_batch(samples: List[Dict[str, Any]], batch_size: int = BATCH_SIZE) -> List[Dict[str, Any]]:
    """
    Process a batch of function samples with caching and rate limiting.
    """
    results = []
    total = len(samples)
    processed = 0

    logger.info(f"Starting batch refactoring of {total} functions")

    for i, sample in enumerate(samples):
        processed += 1
        logger.info(f"Processing {processed}/{total}")

        result = refactor_single_function(sample)
        results.append(result)

        # Add small delay between requests to avoid rate limiting
        if i < total - 1:
            time.sleep(1)

    success_count = sum(1 for r in results if r["status"] == "success")
    logger.info(f"Batch complete: {success_count}/{total} successful")

    return results

def main():
    """
    Main entry point for refactoring pipeline.
    Demonstrates caching integration.
    """
    logger.info("Starting refactoring pipeline with caching")

    # Example: load a small set of samples from processed data
    data_path = Path("data/processed/raw_metrics.json")
    if not data_path.exists():
        logger.error(f"Processed data not found at {data_path}")
        return

    with open(data_path, 'r') as f:
        data = json.load(f)

    samples = data.get("samples", [])[:10]  # Process first 10 for demo
    if not samples:
        logger.error("No samples found in processed data")
        return

    results = refactor_batch(samples)

    # Save results
    output_path = Path("data/processed/refactoring_cache_demo.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {output_path}")

    # Summary
    success = sum(1 for r in results if r["status"] == "success")
    cached = sum(1 for r in results if r.get("from_cache", False))
    logger.info(f"Success: {success}, Cached: {cached}")

if __name__ == "__main__":
    import json
    main()