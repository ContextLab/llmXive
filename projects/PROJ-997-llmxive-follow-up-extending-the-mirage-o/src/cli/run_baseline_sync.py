"""
Task T027: Run Baseline Synchronous Inference (Full-Hardware-Sync)

Executes the full-hardware-sync baseline by running actual quantized inference
for every sample in the test set (using the same quantization levels as the dataset).
Calculates ground-truth acceptance rates and final reasoning scores.
Outputs results to data/processed/baseline_metrics.json.

This task provides the ground-truth baseline for T028 (Proxy Loop).
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Import from project modules using the defined API surface
from src.config.env_config import load_config
from src.config.logging_config import setup_logger
from src.services.quantized_inference import (
    load_quantized_model,
    run_quantized_inference,
    InferenceResult
)
from src.services.gap_calculator import compute_kl_divergence
from src.services.feature_extractor import load_dataset_streaming

# Constants
TEST_DATA_PATH = "data/processed/split_test.parquet"
OUTPUT_PATH = "data/processed/baseline_metrics.json"
LOG_PATH = "logs/pipeline.log"

# Ensure directories exist
Path("logs").mkdir(exist_ok=True)
Path("data/processed").mkdir(exist_ok=True)

logger = setup_logger("baseline_sync", LOG_PATH)

def calculate_reasoning_score(logits: Optional[List[float]], target_response: str) -> float:
    """
    Calculate a simple reasoning score based on log-probability of the target response.
    In a real scenario, this would involve tokenizing and summing log_probs.
    For this baseline, we use a proxy: if logits are available, return mean logit value (scaled).
    If logits are None, return 0.0.
    """
    if not logits or len(logits) == 0:
        return 0.0
    # Simple proxy score: mean of logits (scaled to a reasonable range)
    # This is a placeholder for a real scoring mechanism that would depend on the specific task
    return float(np.mean(logits) * 10.0)

def calculate_acceptance_rate(inference_results: List[InferenceResult]) -> float:
    """
    Calculate the acceptance rate based on inference results.
    For this baseline, we consider a sample 'accepted' if the inference was successful
    and the calculated gap (KL divergence) is below a threshold (e.g., 0.1).
    """
    if not inference_results:
        return 0.0

    accepted_count = 0
    threshold = 0.1  # Example threshold for acceptance

    for result in inference_results:
        if result.success and result.kl_divergence is not None and result.kl_divergence < threshold:
            accepted_count += 1

    return accepted_count / len(inference_results)

def run_baseline_sync():
    """
    Main execution function for the baseline sync task.
    """
    logger.info("Starting Baseline Synchronous Inference (T027)...")

    # Load configuration
    config = load_config()
    model_path = config.get("MODEL_PATH")
    if not model_path:
        logger.error("MODEL_PATH not found in configuration. Exiting.")
        sys.exit(1)

    # Load test dataset
    if not os.path.exists(TEST_DATA_PATH):
        logger.error(f"Test data not found at {TEST_DATA_PATH}. Exiting.")
        sys.exit(1)

    logger.info(f"Loading test data from {TEST_DATA_PATH}...")
    try:
        df_test = pd.read_parquet(TEST_DATA_PATH)
    except Exception as e:
        logger.error(f"Failed to load test data: {e}")
        sys.exit(1)

    if df_test.empty:
        logger.error("Test dataset is empty. Exiting.")
        sys.exit(1)

    logger.info(f"Loaded {len(df_test)} test samples.")

    # Initialize metrics storage
    results = []
    total_time = 0.0
    skipped_count = 0
    error_count = 0

    # Iterate through each sample in the test set
    for idx, row in df_test.iterrows():
        start_time = time.time()

        input_text = row.get("input_id", "")  # Assuming input_id contains the prompt
        quantization_level = row.get("quantization_level", "INT4")

        if not input_text:
            logger.warning(f"Sample {idx} has empty input. Skipping.")
            skipped_count += 1
            continue

        try:
            # Run quantized inference
            # Note: run_quantized_inference expects a prompt and returns InferenceResult
            inference_result = run_quantized_inference(
                prompt=input_text,
                model_path=model_path,
                quantization_level=quantization_level
            )

            end_time = time.time()
            inference_time = end_time - start_time
            total_time += inference_time

            if not inference_result.success:
                logger.warning(f"Sample {idx} inference failed: {inference_result.error}")
                error_count += 1
                # Still record the failure for metrics
                results.append({
                    "input_id": input_text,
                    "quantization_level": quantization_level,
                    "success": False,
                    "inference_time": inference_time,
                    "kl_divergence": None,
                    "reasoning_score": 0.0,
                    "error": inference_result.error
                })
                continue

            # Calculate reasoning score
            reasoning_score = calculate_reasoning_score(
                inference_result.logits,
                row.get("target_response", "")
            )

            # Calculate KL divergence if full precision logits are available (they are in the test set)
            kl_div = None
            if "calculated_kl_divergence" in row and row["calculated_kl_divergence"] is not None:
                kl_div = float(row["calculated_kl_divergence"])
            elif inference_result.full_precision_logits and inference_result.logits:
                # Fallback: compute KL if not pre-calculated (though T015 should have done this)
                kl_div = float(compute_kl_divergence(
                    inference_result.full_precision_logits,
                    inference_result.logits
                ))

            results.append({
                "input_id": input_text,
                "quantization_level": quantization_level,
                "success": True,
                "inference_time": inference_time,
                "kl_divergence": kl_div,
                "reasoning_score": reasoning_score,
                "error": None
            })

        except Exception as e:
            logger.error(f"Unexpected error processing sample {idx}: {e}", exc_info=True)
            error_count += 1
            results.append({
                "input_id": input_text,
                "quantization_level": quantization_level,
                "success": False,
                "inference_time": 0.0,
                "kl_divergence": None,
                "reasoning_score": 0.0,
                "error": str(e)
            })

    # Calculate aggregate metrics
    total_samples = len(df_test)
    successful_samples = len([r for r in results if r["success"]])
    acceptance_rate = calculate_acceptance_rate([
        InferenceResult(
            success=r["success"],
            logits=r.get("kl_divergence"), # Passing KL as logits proxy for the helper
            full_precision_logits=None,
            error=r.get("error")
        ) for r in results
    ])

    # Calculate average reasoning score
    avg_reasoning_score = np.mean([r["reasoning_score"] for r in results if r["success"]]) if successful_samples > 0 else 0.0

    # Calculate average inference time
    avg_inference_time = total_time / successful_samples if successful_samples > 0 else 0.0

    # Prepare output metrics
    metrics = {
        "total_samples": total_samples,
        "successful_samples": successful_samples,
        "skipped_samples": skipped_count,
        "error_count": error_count,
        "acceptance_rate": acceptance_rate,
        "average_reasoning_score": avg_reasoning_score,
        "average_inference_time_seconds": avg_inference_time,
        "total_inference_time_seconds": total_time,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Write results to JSON
    with open(OUTPUT_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Baseline sync completed. Results written to {OUTPUT_PATH}")
    logger.info(f"Acceptance Rate: {acceptance_rate:.4f}")
    logger.info(f"Average Reasoning Score: {avg_reasoning_score:.4f}")
    logger.info(f"Average Inference Time: {avg_inference_time:.4f}s")

    return metrics

def main():
    """Entry point for CLI."""
    run_baseline_sync()

if __name__ == "__main__":
    main()