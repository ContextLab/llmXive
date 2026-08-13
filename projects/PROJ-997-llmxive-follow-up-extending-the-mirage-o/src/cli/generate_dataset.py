import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Local imports matching API surface
from src.config.logging_config import setup_logger
from src.config.env_config import load_config, get_dataset_id
from src.services.feature_extractor import (
    load_dataset_streaming, 
    extract_features_for_sample, 
    FeatureResult
)
from src.services.quantized_inference import (
    load_quantized_model, 
    run_quantized_inference, 
    InferenceResult
)
from src.services.gap_calculator import calculate_gap
from src.models.entities import TrainingSample

@dataclass
class GenerationStats:
    total_processed: int = 0
    successful: int = 0
    skipped_feature_extraction: int = 0
    skipped_inference: int = 0
    skipped_gap_calc: int = 0
    quantization_errors: int = 0
    feature_extraction_errors: int = 0
    gap_calc_errors: int = 0

def setup_logger(name: str, log_file: str = "logs/pipeline.log") -> logging.Logger:
    """Configures a logger that writes to both console and file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Ensure log directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

def run_generation_pipeline(
    dataset_id: str, 
    output_path: str, 
    quantization_levels: List[str] = ["INT4", "INT8", "FP8"],
    sample_limit: Optional[int] = None
) -> GenerationStats:
    """
    Orchestrates the generation of the training dataset.
    Performs paired feature extraction and quantized inference for every sample.
    """
    logger = setup_logger("DataGeneration")
    stats = GenerationStats()
    
    logger.info(f"Starting dataset generation for {dataset_id}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Quantization levels: {quantization_levels}")
    
    # Initialize output directory
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Load dataset stream
    logger.info("Loading dataset stream...")
    dataset_stream = load_dataset_streaming(dataset_id)
    
    # Prepare quantized model loaders (lazy load per level to save memory)
    # Note: In a real heavy-load scenario, we might reload per batch, 
    # but for this pipeline we load once per level if possible or handle errors gracefully.
    # Given the constraint to fail loudly on fetch but skip on inference error:
    
    quant_models = {}
    for level in quantization_levels:
        try:
            logger.info(f"Loading quantized model for level: {level}")
            model = load_quantized_model(level)
            quant_models[level] = model
            logger.info(f"Successfully loaded model for {level}")
        except Exception as e:
            logger.error(f"Failed to load model for {level}: {e}")
            logger.warning(f"Skipping level {level} for this run.")
    
    if not quant_models:
        logger.error("No quantized models loaded. Cannot proceed.")
        raise RuntimeError("No quantized models available.")

    samples_written = []
    start_time = time.time()
    
    for idx, item in enumerate(dataset_stream):
        stats.total_processed += 1
        
        # Progress logging every 10 samples or if limit reached
        if idx % 10 == 0:
            elapsed = time.time() - start_time
            logger.info(f"Progress: Processed {stats.total_processed} samples. "
                        f"Successful: {stats.successful}. Skipped: {stats.skipped_feature_extraction + stats.skipped_inference}. "
                        f"Time: {elapsed:.2f}s")
        
        if sample_limit and stats.total_processed >= sample_limit:
            logger.info(f"Sample limit {sample_limit} reached. Stopping.")
            break

        # 1. Feature Extraction
        feature_result: Optional[FeatureResult] = None
        try:
            feature_result = extract_features_for_sample(item)
        except Exception as e:
            logger.error(f"Feature extraction failed for sample {idx}: {e}")
            stats.feature_extraction_errors += 1
            stats.skipped_feature_extraction += 1
            continue # Skip to next sample

        if feature_result is None:
            logger.warning(f"Feature extraction returned None for sample {idx}")
            stats.skipped_feature_extraction += 1
            continue

        # 2. Quantized Inference (Paired Loop)
        quantized_logits = {}
        inference_success = True
        
        for level, model in quant_models.items():
            try:
                logger.debug(f"Running inference for sample {idx} at level {level}")
                inf_result: InferenceResult = run_quantized_inference(
                    model, 
                    item.get("prompt", ""), 
                    level
                )
                quantized_logits[level] = inf_result.logits
            except Exception as e:
                logger.error(f"Quantized inference failed for sample {idx} at level {level}: {e}")
                stats.quantization_errors += 1
                stats.skipped_inference += 1
                # We continue to next level, but if ALL levels fail, we skip the sample
                if len(quantized_logits) == 0 and len(quant_models) > 0:
                    # Check if this was the first failure in the loop
                    pass # We'll check at the end of the loop if we have any logits
        
        # If no logits were generated for any level, skip sample
        if not quantized_logits:
            logger.warning(f"No inference results for sample {idx}. Skipping.")
            continue

        # 3. Gap Calculation
        try:
            kl_divergences = {}
            for level, q_logits in quantized_logits.items():
                # Assuming feature_result has full precision logits or we compute them here
                # For this implementation, we assume extract_features_for_sample returns full precision logits
                # or we compute them. The API surface implies feature_result has the necessary data.
                # Let's assume feature_result contains 'full_precision_logits'
                if hasattr(feature_result, 'full_precision_logits') and feature_result.full_precision_logits is not None:
                    kl = calculate_gap(feature_result.full_precision_logits, q_logits)
                    kl_divergences[level] = kl
                else:
                    logger.warning(f"Full precision logits missing for sample {idx}. Skipping gap calc.")
                    stats.gap_calc_errors += 1
                    continue
            
            if not kl_divergences:
                continue

            # 4. Construct TrainingSample
            # We take the first available level for the main record or create multiple rows?
            # The task says: write `data/processed/training_sample.parquet` with columns including `quantization_level`.
            # This implies one row per level per sample.
            
            for level, kl_val in kl_divergences.items():
                sample = TrainingSample(
                    input_id=f"{idx}_{level}",
                    gradient_norms=feature_result.gradient_norms,
                    local_curvature=feature_result.local_curvature,
                    quantized_logits=quantized_logits[level], # Storing as list/array
                    calculated_kl_divergence=kl_val,
                    quantization_level=level
                )
                samples_written.append(sample)

            stats.successful += 1

        except Exception as e:
            logger.error(f"Gap calculation failed for sample {idx}: {e}")
            stats.gap_calc_errors += 1
            continue

    # Write to Parquet
    if samples_written:
        logger.info(f"Writing {len(samples_written)} samples to {output_path}")
        # Convert to pandas for parquet writing
        import pandas as pd
        import numpy as np
        
        data = []
        for s in samples_written:
            row = {
                "input_id": s.input_id,
                "gradient_norms": s.gradient_norms,
                "local_curvature": s.local_curvature,
                # Convert tensor to list for serialization
                "quantized_logits": s.quantized_logits.tolist() if hasattr(s.quantized_logits, 'tolist') else s.quantized_logits,
                "calculated_kl_divergence": s.calculated_kl_divergence,
                "quantization_level": s.quantization_level
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_parquet(output_path, index=False)
        logger.info(f"Successfully wrote {output_path}")
    else:
        logger.warning("No samples were successfully processed. Output file not created.")

    # Final Stats Log
    logger.info("=" * 50)
    logger.info("DATASET GENERATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total Processed: {stats.total_processed}")
    logger.info(f"Successful: {stats.successful}")
    logger.info(f"Skipped (Feature Extraction): {stats.skipped_feature_extraction}")
    logger.info(f"Skipped (Inference): {stats.skipped_inference}")
    logger.info(f"Skipped (Gap Calc): {stats.skipped_gap_calc}")
    logger.info(f"Quantization Errors: {stats.quantization_errors}")
    logger.info(f"Feature Extraction Errors: {stats.feature_extraction_errors}")
    logger.info(f"Gap Calculation Errors: {stats.gap_calc_errors}")
    logger.info("=" * 50)
    
    return stats

def main():
    config = load_config()
    dataset_id = get_dataset_id()
    output_path = config.get("OUTPUT_PATH", "data/processed/training_sample.parquet")
    
    # Default levels
    levels = ["INT4", "INT8", "FP8"]
    
    run_generation_pipeline(dataset_id, output_path, levels)

if __name__ == "__main__":
    main()