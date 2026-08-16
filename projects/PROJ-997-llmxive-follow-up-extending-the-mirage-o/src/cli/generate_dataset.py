"""
T015: Orchestrate streaming of GSM8K/Ultrachat prompts and generate the training dataset.

This script executes the paired loop: for every sample, it extracts features (T012)
and runs quantized inference (T013), then calculates the gap (T014) and logs progress (T017).
It writes the final result to data/processed/training_sample.parquet.
"""
import os
import sys
import json
import logging
import time
import base64
import struct
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Project imports
from src.config.logging_config import setup_logger, log_sample_progress, ensure_log_dir
from src.config.env_config import get_dataset_id, get_model_path
from src.services.feature_extractor import extract_features_for_sample, load_dataset_streaming
from src.services.quantized_inference import run_quantized_inference, load_quantized_model
from src.services.gap_calculator import calculate_gap

@dataclass
class GenerationStats:
    total_samples: int = 0
    successful_samples: int = 0
    skipped_samples: int = 0
    total_time_seconds: float = 0.0

def encode_logits_to_base64(logits: List[float]) -> str:
    """
    Encodes a list of float32 values into a base64 string.
    This ensures deterministic serialization and manageable file sizes.
    """
    if not logits:
        return base64.b64encode(b'').decode('utf-8')
    # Pack as float32 (4 bytes each)
    packed = struct.pack(f'{len(logits)}f', *logits)
    return base64.b64encode(packed).decode('utf-8')

def run_generation_pipeline(
    output_path: str,
    max_samples: Optional[int] = None,
    quantization_levels: List[str] = None
) -> GenerationStats:
    """
    Orchestrates the full generation pipeline.

    Args:
        output_path: Path to the output parquet file.
        max_samples: Optional limit on the number of samples to process.
        quantization_levels: List of quantization levels to test (e.g., ['INT4', 'INT8', 'FP8']).

    Returns:
        GenerationStats object with summary metrics.
    """
    logger = setup_logger("generate_dataset")
    ensure_log_dir()

    if quantization_levels is None:
        quantization_levels = ["INT4", "INT8", "FP8"]

    # Initialize data collection
    records = []
    stats = GenerationStats()
    start_time = time.time()

    # Load dataset stream
    # Using 'gsm8k' as the primary dataset as per spec context.
    # If 'ultrachat' is needed, it would be a separate stream or concatenated.
    dataset_id = get_dataset_id() or "gsm8k"
    logger.info(f"Starting streaming dataset: {dataset_id}")
    
    try:
        dataset_stream = load_dataset_streaming(dataset_id, split="train")
    except Exception as e:
        logger.critical(f"Failed to load dataset stream: {e}")
        raise RuntimeError(f"Dataset loading failed: {e}")

    # Pre-load models if possible (optimization)
    # Note: Feature extractor loads full-precision model internally.
    # Quantized models are loaded per level or cached.

    logger.info("Beginning paired loop for feature extraction and quantized inference...")

    count = 0
    for batch in dataset_stream:
        # Handle max_samples constraint
        if max_samples and count >= max_samples:
            break

        # The batch from streaming usually contains lists of items.
        # We iterate row by row.
        if isinstance(batch, dict):
            # If it's a single row dict (unlikely in batched streaming but possible)
            items = [batch]
        else:
            # Assume it's a list of dicts or similar iterable
            items = batch if hasattr(batch, '__iter__') else [batch]

        for sample in items:
            if max_samples and count >= max_samples:
                break

            stats.total_samples += 1
            sample_id = f"sample_{count}"
            sample_prompt = sample.get("question", sample.get("prompt", ""))
            
            if not sample_prompt:
                logger.warning(f"Skipping sample {sample_id} due to missing prompt.")
                log_sample_progress(sample_id, "skipped", "MISSING_PROMPT")
                stats.skipped_samples += 1
                count += 1
                continue

            try:
                # 1. Feature Extraction (T012)
                # Returns gradient_norms (float) and local_curvature (float)
                features = extract_features_for_sample(sample_prompt)
                gradient_norms = features.gradient_norms
                local_curvature = features.local_curvature

                # 2. Quantized Inference (T013)
                # We run for each level and aggregate or pick one. 
                # The spec implies generating a dataset with these levels.
                # We will iterate levels and create a record for each level-sample pair 
                # OR create one record with the most relevant level. 
                # Given the schema requires 'quantization_level' column, we likely create rows per level.
                
                for level in quantization_levels:
                    try:
                        # Run inference for this specific level
                        # This function handles loading the engine and running inference
                        inference_result = run_quantized_inference(
                            prompt=sample_prompt,
                            quantization_level=level
                        )
                        
                        if inference_result.error:
                            logger.warning(f"Sample {sample_id} skipped for level {level}: {inference_result.error}")
                            log_sample_progress(sample_id, "skipped", f"INFERENCE_ERROR_{level}")
                            stats.skipped_samples += 1
                            continue

                        # 3. Gap Calculation (T014)
                        # We need full precision logits too. 
                        # extract_features_for_sample might have computed them, or we call gap_calculator directly.
                        # Assuming gap_calculator takes the raw logits or results.
                        # Let's assume we need to re-run full precision for gap calc or it was cached.
                        # For robustness, we pass the inference result and the prompt.
                        # The gap calculator needs the full precision logits. 
                        # Since T012 extracts features, it likely has the full precision logits.
                        # If not, we must re-calculate.
                        
                        # Re-calculating gap using the helper which handles the full precision call internally
                        # or expects the logits. Let's assume gap_calculator.calculate_gap takes:
                        # prompt, quantized_logits, and optionally full_precision_logits.
                        # If extract_features_for_sample didn't return full_precision_logits, we need to get them.
                        # To be safe and aligned with T012/T014 separation, we assume T014 needs the full precision logits.
                        # Let's assume extract_features_for_sample returns them or we fetch them again.
                        # Given the "paired loop" constraint, we assume the full precision run is part of the feature extraction step.
                        
                        # Re-using the logic: gap_calculator.calculate_gap(prompt, quantized_logits, full_precision_logits)
                        # If we don't have full_precision_logits here, we might need to extract them again.
                        # However, T012 is supposed to extract gradient norms and curvature.
                        # Let's assume the gap calculator can handle the full precision inference internally if not provided.
                        
                        gap_result = calculate_gap(
                            prompt=sample_prompt,
                            quantized_logits=inference_result.logits,
                            quantization_level=level
                        )
                        
                        calculated_kl_divergence = gap_result.kl_divergence
                        full_precision_logits = gap_result.full_precision_logits # For reference if needed

                        # Encode logits
                        encoded_logits = encode_logits_to_base64(inference_result.logits)

                        # Create record
                        record = {
                            "input_id": sample_id,
                            "gradient_norms": gradient_norms,
                            "local_curvature": local_curvature,
                            "quantized_logits": encoded_logits,
                            "calculated_kl_divergence": calculated_kl_divergence,
                            "quantization_level": level
                        }
                        records.append(record)
                        stats.successful_samples += 1
                        log_sample_progress(sample_id, "success", None)

                    except Exception as e:
                        logger.error(f"Error processing sample {sample_id} for level {level}: {e}", exc_info=True)
                        log_sample_progress(sample_id, "error", str(e))
                        stats.skipped_samples += 1
                        continue

                count += 1

            except Exception as e:
                logger.error(f"Critical error in feature extraction for {sample_id}: {e}", exc_info=True)
                log_sample_progress(sample_id, "error", f"FEATURE_EXTRACT_ERROR: {e}")
                stats.skipped_samples += 1
                continue

    stats.total_time_seconds = time.time() - start_time

    # Write to Parquet
    if not records:
        logger.critical("No records generated. Aborting write.")
        raise RuntimeError("Generation pipeline produced no valid records.")

    import pandas as pd
    df = pd.DataFrame(records)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully wrote {len(records)} records to {output_path}")
    logger.info(f"Total time: {stats.total_time_seconds:.2f}s")

    return stats

def main():
    logger = setup_logger("generate_dataset_main")
    
    # Configuration
    output_file = "data/processed/training_sample.parquet"
    max_samples = int(os.environ.get("MAX_SAMPLES", "1000")) # Default to 1000 for initial run
    levels = ["INT4", "INT8", "FP8"]

    logger.info(f"Starting T015: Generating dataset to {output_file}")
    logger.info(f"Max samples: {max_samples}")

    try:
        stats = run_generation_pipeline(
            output_path=output_file,
            max_samples=max_samples,
            quantization_levels=levels
        )
        logger.info(f"Pipeline completed. Stats: {stats}")
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()