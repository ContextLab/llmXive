import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

import pandas as pd
import numpy as np

from src.config.logging_config import setup_logger, log_sample_progress, ensure_log_dir
from src.config.env_config import get_dataset_id, load_config
from src.services.feature_extractor import extract_features_for_sample, load_dataset_streaming, FeatureResult
from src.services.quantized_inference import run_quantized_inference, InferenceResult
from src.services.gap_calculator import compute_kl_divergence

@dataclass
class GenerationStats:
    total_samples: int
    successful_samples: int
    skipped_samples: int
    error_samples: int
    non_zero_divergence_count: int

def run_generation_pipeline(
    output_path: str,
    max_samples: Optional[int] = None,
    quantization_levels: List[str] = None
) -> GenerationStats:
    """
    Orchestrate streaming of GSM8K/Ultrachat prompts.
    For every sample, execute feature extraction and quantized inference in a paired loop.
    Write the results to a parquet file.
    """
    logger = setup_logger("dataset_generation")
    ensure_log_dir()

    if quantization_levels is None:
        quantization_levels = ["INT4", "INT8", "FP8"]

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Initialize storage for results
    results: List[Dict[str, Any]] = []

    # Load dataset stream
    dataset_id = get_dataset_id()
    logger.info(f"Starting generation pipeline for dataset: {dataset_id}")
    logger.info(f"Output path: {output_path}")

    try:
        dataset_stream = load_dataset_streaming(dataset_id)
    except Exception as e:
        logger.error(f"Failed to load dataset stream: {e}")
        raise

    sample_count = 0
    success_count = 0
    skip_count = 0
    error_count = 0
    non_zero_div_count = 0

    start_time = time.time()

    for batch in dataset_stream:
        # Process batch items
        prompts = batch.get("prompt", [])
        input_ids = batch.get("input_id", list(range(len(prompts))))

        for i, (prompt, input_id) in enumerate(zip(prompts, input_ids)):
            if max_samples and sample_count >= max_samples:
                logger.info(f"Reached max_samples limit ({max_samples}). Stopping.")
                break

            sample_id = f"{input_id}_{sample_count}"
            logger.debug(f"Processing sample {sample_id}")

            try:
                # 1. Feature Extraction (T012)
                feature_result: FeatureResult = extract_features_for_sample(prompt)
                gradient_norms = feature_result.gradient_norms
                local_curvature = feature_result.local_curvature

                # 2. Quantized Inference (T013) - Paired Loop
                # We run inference for all requested levels for this specific prompt
                # to ensure alignment.
                quantized_logits_all = []
                for level in quantization_levels:
                    try:
                        inf_result: InferenceResult = run_quantized_inference(prompt, level=level)
                        quantized_logits_all.append({
                            "level": level,
                            "logits": inf_result.logits
                        })
                    except Exception as q_err:
                        # T013 requirement: Log and skip specific sample/level, continue others
                        logger.warning(f"Quantized inference failed for level {level} on sample {sample_id}: {q_err}")
                        # We continue to next level, but if all fail, we might skip the whole sample later
                        # For this task, we assume at least one level usually works or we skip the row entirely if critical
                        # Here we just log and move to next level. If no logits collected, we skip the row.
                        continue

                if not quantized_logits_all:
                    logger.warning(f"No quantized logits generated for sample {sample_id}. Skipping row.")
                    skip_count += 1
                    log_sample_progress(sample_id, "skipped", "NO_LOGITS")
                    sample_count += 1
                    continue

                # 3. Gap Calculation (T014)
                # We assume feature_result.full_precision_logits is available or we compute it if not in FeatureResult
                # Based on T012/T014 API surface, we need to ensure we have full precision logits.
                # If extract_features_for_sample doesn't return them, we might need to call a helper.
                # Assuming feature_result contains full precision logits or we can derive them.
                # For safety, if not present, we might need to re-run full precision or assume it's part of the result.
                # Let's assume FeatureResult has full_precision_logits or we compute gap per level.
                
                # Re-reading T012/T014: T014 computes KL between full-precision and quantized.
                # We need full precision logits.
                full_prec_logits = feature_result.full_precision_logits if hasattr(feature_result, 'full_precision_logits') else None
                
                if full_prec_logits is None:
                    # Fallback: if not in result, we might need to compute it or it's a design flaw in T012.
                    # For this implementation, we assume T012 returns it. If not, we raise or skip.
                    # Let's assume it's there. If not, we skip.
                    logger.error(f"Full precision logits missing for sample {sample_id}. Skipping.")
                    skip_count += 1
                    log_sample_progress(sample_id, "skipped", "MISSING_FULL_PREC")
                    sample_count += 1
                    continue

                for q_data in quantized_logits_all:
                    level = q_data["level"]
                    q_logits = q_data["logits"]

                    try:
                        kl_div = compute_kl_divergence(full_prec_logits, q_logits)
                        if kl_div > 1e-9:
                            non_zero_div_count += 1
                        
                        row = {
                            "input_id": sample_id,
                            "gradient_norms": float(gradient_norms),
                            "local_curvature": float(local_curvature),
                            "quantized_logits": json.dumps(q_logits.tolist() if hasattr(q_logits, 'tolist') else list(q_logits)),
                            "calculated_kl_divergence": float(kl_div),
                            "quantization_level": level
                        }
                        results.append(row)
                        success_count += 1
                        log_sample_progress(sample_id, "success", None)
                    except Exception as gap_err:
                        logger.error(f"Gap calculation failed for sample {sample_id}, level {level}: {gap_err}")
                        error_count += 1
                        log_sample_progress(sample_id, "error", "GAP_CALC_ERROR")

            except Exception as e:
                logger.error(f"Critical error processing sample {sample_id}: {e}", exc_info=True)
                error_count += 1
                log_sample_progress(sample_id, "error", "CRITICAL_ERROR")

            sample_count += 1
            if max_samples and sample_count >= max_samples:
                break
        if max_samples and sample_count >= max_samples:
            break

    elapsed = time.time() - start_time
    logger.info(f"Pipeline finished in {elapsed:.2f}s")
    logger.info(f"Total: {sample_count}, Success: {success_count}, Skipped: {skip_count}, Errors: {error_count}")
    logger.info(f"Non-zero divergence count: {non_zero_div_count} ({non_zero_div_count/success_count*100 if success_count > 0 else 0:.2f}%)")

    stats = GenerationStats(
        total_samples=sample_count,
        successful_samples=success_count,
        skipped_samples=skip_count,
        error_samples=error_count,
        non_zero_divergence_count=non_zero_div_count
    )

    # Write to Parquet
    if results:
        df = pd.DataFrame(results)
        df.to_parquet(output_path, index=False)
        logger.info(f"Successfully wrote {len(results)} rows to {output_path}")
    else:
        logger.warning("No results to write. Creating empty parquet file.")
        pd.DataFrame(columns=["input_id", "gradient_norms", "local_curvature", "quantized_logits", "calculated_kl_divergence", "quantization_level"]).to_parquet(output_path, index=False)

    return stats

def main():
    logger = setup_logger("generate_dataset_main")
    ensure_log_dir()
    
    # Default paths from project structure
    output_path = "data/processed/training_sample.parquet"
    max_samples = int(os.getenv("MAX_SAMPLES", "100")) # Default to 100 for testing, adjust as needed
    
    # Quantization levels
    levels = os.getenv("QUANTIZATION_LEVELS", "INT4,INT8,FP8").split(",")
    
    logger.info(f"Running dataset generation with max_samples={max_samples}, levels={levels}")
    
    try:
        stats = run_generation_pipeline(output_path, max_samples=max_samples, quantization_levels=levels)
        logger.info(f"Generation complete. Stats: {stats}")
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()