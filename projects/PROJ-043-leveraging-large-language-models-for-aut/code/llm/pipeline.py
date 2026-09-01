import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from data.download import download_valid_functions
from data.static_analysis import run_static_analysis_on_dataset
from llm.refactoring import refactor_batch
from llm.baseline import generate_identity_baseline, validate_identity_baseline
from llm.quality import compute_deltas, validate_baseline_identity
from utils.logging import get_logger, LLMRefactoringError, ValidationFailedError
from utils.cache import get_cache
from models.entities import FunctionSample

logger = get_logger(__name__)

def load_processed_data(filepath: str) -> List[Dict[str, Any]]:
    """Load the pre-computed raw metrics from the data pipeline."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} samples from {filepath}")
    return data

def process_refactoring_batch(
    samples: List[Dict[str, Any]],
    batch_size: int = 10,
    timeout: int = 60
) -> List[Dict[str, Any]]:
    """
    Orchestrate refactoring and baseline generation for a batch of samples.
    
    1. Refactor functions using LLM (with caching).
    2. Generate identity baselines.
    3. Compute quality deltas.
    4. Handle syntax errors gracefully (mark as "Refactoring Failed").
    """
    results = []
    cache = get_cache()
    
    for i, sample in enumerate(samples):
        logger.info(f"Processing sample {i+1}/{len(samples)}: {sample.get('hash', 'unknown')[:8]}...")
        
        original_code = sample.get('code')
        if not original_code:
            logger.warning("Skipping sample with missing code.")
            continue

        # 1. Refactoring
        try:
            # Check cache first
            cache_key = f"refactor_{sample.get('hash')}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info("Cache hit for refactoring.")
                refactored_code = cached_result
            else:
                # Perform refactoring
                # Note: refactor_batch expects a list of code strings, returns list of (code, success, error)
                # We adapt the single sample to a batch of 1 for the API
                refactor_results = refactor_batch([original_code], batch_size=1, timeout=timeout)
                
                if not refactor_results or len(refactor_results) == 0:
                    raise LLMRefactoringError("No result returned from refactoring API.")
                
                refactored_code, success, error_msg = refactor_results[0]
                
                if not success:
                    logger.warning(f"Refactoring failed for {sample.get('hash')}: {error_msg}")
                    # Mark as failed but continue to baseline
                    refactored_code = None
                else:
                    # Cache the successful result
                    cache.set(cache_key, refactored_code, ttl=86400)
                    
        except Exception as e:
            logger.error(f"Exception during refactoring: {e}")
            refactored_code = None

        # 2. Baseline Generation (Identity)
        try:
            baseline_code = generate_identity_baseline(original_code)
            # Validate identity baseline is truly identical
            if baseline_code != original_code:
                logger.warning(f"Identity baseline mismatch for {sample.get('hash')}.")
                # This is a logic error in baseline generation, but we proceed with the code we got
        except Exception as e:
            logger.error(f"Error generating baseline: {e}")
            baseline_code = None

        # 3. Compute Deltas and Metrics
        # We need to compute metrics for original, refactored, and baseline
        # The quality module functions expect code strings or handle None
        
        entry = {
            "hash": sample.get('hash'),
            "original_metrics": sample.get('metrics', {}),
            "original_code": original_code,
            "refactored_code": refactored_code,
            "baseline_code": baseline_code,
            "status": "Success",
            "deltas": {}
        }

        if refactored_code is None:
            entry["status"] = "Refactoring Failed"
            entry["refactored_metrics"] = None
            entry["baseline_metrics"] = None
            entry["deltas"] = {
                "complexity_delta": None,
                "pylint_delta": None,
                "maintainability_delta": None
            }
        else:
            # Calculate metrics for refactored and baseline
            from llm.quality import calculate_metrics
            
            try:
                refactored_metrics = calculate_metrics(refactored_code)
                entry["refactored_metrics"] = refactored_metrics
            except Exception as e:
                logger.error(f"Could not calculate metrics for refactored code: {e}")
                refactored_metrics = None
                entry["refactored_metrics"] = None

            if baseline_code:
                try:
                    baseline_metrics = calculate_metrics(baseline_code)
                    entry["baseline_metrics"] = baseline_metrics
                except Exception as e:
                    logger.error(f"Could not calculate metrics for baseline code: {e}")
                    baseline_metrics = None
                    entry["baseline_metrics"] = None
            else:
                baseline_metrics = None
                entry["baseline_metrics"] = None

            # Compute deltas
            # Original metrics are in sample['metrics']
            # We need to ensure keys match
            orig_m = sample.get('metrics', {})
            
            if refactored_metrics and orig_m:
                delta_complexity = refactored_metrics.get('cyclomatic_complexity', 0) - orig_m.get('cyclomatic_complexity', 0)
                delta_pylint = refactored_metrics.get('pylint_score', 0) - orig_m.get('pylint_score', 0)
                # Maintainability might be derived or missing in original sample, handle gracefully
                delta_maintainability = refactored_metrics.get('maintainability_index', 0) - orig_m.get('maintainability_index', 0)
                
                entry["deltas"] = {
                    "complexity_delta": delta_complexity,
                    "pylint_delta": delta_pylint,
                    "maintainability_delta": delta_maintainability
                }
            else:
                entry["deltas"] = {
                    "complexity_delta": None,
                    "pylint_delta": None,
                    "maintainability_delta": None
                }

        results.append(entry)

    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """Save the refactoring results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """
    Main entry point for the refactoring pipeline (T022).
    Loads processed raw metrics, runs refactoring and baseline generation,
    and saves results to data/processed/refactoring_results.json.
    """
    # Configuration
    input_file = "data/processed/raw_metrics.json"
    output_file = "data/processed/refactoring_results.json"
    
    # Validate input exists
    if not Path(input_file).exists():
        logger.error(f"Input file not found: {input_file}. Please run T014 first.")
        sys.exit(1)

    logger.info("Starting Refactoring Pipeline (T022)...")
    
    # Load data
    samples = load_processed_data(input_file)
    
    if not samples:
        logger.warning("No samples found in input file.")
        sys.exit(0)

    # Process
    results = process_refactoring_batch(samples)
    
    # Validate results
    success_count = sum(1 for r in results if r["status"] == "Success")
    failed_count = sum(1 for r in results if r["status"] == "Refactoring Failed")
    
    logger.info(f"Pipeline complete. Success: {success_count}, Failed: {failed_count}")
    
    # Save
    save_results(results, output_file)
    
    logger.info("Refactoring Pipeline finished successfully.")

if __name__ == "__main__":
    main()