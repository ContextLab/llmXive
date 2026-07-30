import os
import sys
import gc
import time
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
from src.utils.memory_monitor import MemoryMonitor, check_memory_constraint, force_gc
from src.utils.config import get_config, get_data_processed_path
from src.data.download import download_all_datasets
from src.data.preprocess import (
    create_code_snippets,
    save_snippets_to_csv,
    parse_raw_directory,
    detect_language_from_extension
)
from src.models.code_snippet import CodeSnippet
from src.models.prediction_result import PredictionResult, create_prediction_result
from src.models.llm_inference import (
    load_model_4bit_cpu,
    run_inference_batch,
    process_snippets_zero_shot,
    InferenceConfig
)

logger = get_logger("ingest_pipeline")

# Constants
MAX_BATCH_SIZE = 32
MIN_BATCH_SIZE = 1
MEMORY_THRESHOLD_RATIO = 0.85  # Reduce batch if usage > 85%

def adjust_batch_size(current_batch: int, memory_monitor: MemoryMonitor) -> int:
    """
    Dynamically adjust batch size based on memory usage.
    Returns a new batch size (1 <= size <= current_batch).
    """
    usage_ratio = memory_monitor.get_memory_usage_ratio()
    if usage_ratio > MEMORY_THRESHOLD_RATIO:
        new_size = max(MIN_BATCH_SIZE, current_batch // 2)
        logger.warning(f"High memory usage ({usage_ratio:.2%}). Reducing batch size from {current_batch} to {new_size}.")
        return new_size
    elif usage_ratio < 0.5 and current_batch < MAX_BATCH_SIZE:
        # Can try to increase batch size if memory is low
        new_size = min(MAX_BATCH_SIZE, current_batch * 2)
        logger.info(f"Low memory usage ({usage_ratio:.2%}). Increasing batch size to {new_size}.")
        return new_size
    return current_batch

def save_predictions_to_csv(predictions: List[PredictionResult], output_path: Path):
    """
    Save a list of PredictionResult objects to a CSV file.
    Validates against the schema implicitly by ensuring all fields are present.
    """
    if not predictions:
        logger.warning("No predictions to save.")
        # Create empty file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['snippet_id', 'predicted_label', 'predicted_category', 'is_correct', 'inference_time_ms'])
        return

    # Define expected columns based on PredictionResult schema
    fieldnames = [
        'snippet_id',
        'predicted_label',
        'predicted_category',
        'is_correct',
        'inference_time_ms'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for pred in predictions:
            row = {
                'snippet_id': pred.snippet_id,
                'predicted_label': pred.predicted_label,
                'predicted_category': pred.predicted_category,
                'is_correct': pred.is_correct,
                'inference_time_ms': pred.inference_time_ms
            }
            writer.writerow(row)

    logger.info(f"Saved {len(predictions)} predictions to {output_path}")

def run_ingest_pipeline():
    """
    Orchestrates the full pipeline: Download -> Preprocess -> Inference -> Save.
    Implements dynamic batch sizing and memory monitoring.
    """
    config = get_config()
    memory_monitor = MemoryMonitor()
    output_dir = get_data_processed_path()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    predictions_output = output_dir / "predictions.csv"
    
    log_stage_start("ingest_pipeline", "Starting full ingestion and inference pipeline")

    try:
        # 1. Download Datasets (T011)
        log_stage_start("download", "Downloading datasets (VulDeePecker, BigVul, NIST/Juliet)")
        download_all_datasets()
        log_stage_complete("download", "Datasets downloaded successfully")

        # 2. Preprocess (T012)
        log_stage_start("preprocess", "Preprocessing raw datasets into CodeSnippets")
        raw_dirs = [
            config.data_paths.raw / "vuldeepecker",
            config.data_paths.raw / "bigvul",
            config.data_paths.raw / "juliet"
        ]
        
        all_snippets: List[CodeSnippet] = []
        for raw_dir in raw_dirs:
            if raw_dir.exists():
                snippets = parse_raw_directory(raw_dir)
                all_snippets.extend(snippets)
                logger.info(f"Parsed {len(snippets)} snippets from {raw_dir}")
            else:
                logger.warning(f"Raw directory not found: {raw_dir}")

        # Save intermediate snippets for debugging/auditing (optional but good practice)
        snippets_csv = output_dir / "snippets.csv"
        save_snippets_to_csv(all_snippets, snippets_csv)
        log_stage_complete("preprocess", f"Preprocessed {len(all_snippets)} total snippets")

        # 3. LLM Inference (T013)
        log_stage_start("inference", "Running zero-shot LLM inference")
        
        # Load model (T013 step 1)
        inference_config = InferenceConfig(
            max_tokens=256,
            temperature=0.0,
            top_p=1.0
        )
        model = load_model_4bit_cpu(inference_config)
        
        # Process in batches with dynamic sizing
        predictions: List[PredictionResult] = []
        batch_size = MAX_BATCH_SIZE
        total_snippets = len(all_snippets)
        processed_count = 0
        
        start_time = time.time()

        while processed_count < total_snippets:
            # Check memory constraint before starting batch
            if not check_memory_constraint(memory_monitor, threshold_ratio=MEMORY_THRESHOLD_RATIO):
                logger.warning("Memory constraint approached. Forcing GC and reducing batch.")
                force_gc()
                batch_size = adjust_batch_size(batch_size, memory_monitor)
                if batch_size == MIN_BATCH_SIZE:
                    logger.error("Batch size at minimum. Pipeline may be too memory intensive.")
                    # Continue anyway but log warning
            
            current_batch = all_snippets[processed_count : processed_count + batch_size]
            if not current_batch:
                break

            logger.info(f"Processing batch of {len(current_batch)} snippets (Batch size: {batch_size})")
            
            # Run inference on batch
            batch_predictions = process_snippets_zero_shot(model, current_batch, inference_config)
            predictions.extend(batch_predictions)
            
            processed_count += len(current_batch)
            logger.info(f"Progress: {processed_count}/{total_snippets} ({100*processed_count/total_snippets:.1f}%)")
            
            # Adjust batch size for next iteration based on memory usage
            batch_size = adjust_batch_size(batch_size, memory_monitor)
            
            # Periodic GC
            if processed_count % (batch_size * 4) == 0:
                force_gc()

        total_time = time.time() - start_time
        log_stage_complete("inference", f"Inference complete. Processed {len(predictions)} snippets in {total_time:.2f}s")

        # 4. Save Results (Validation)
        log_stage_start("save", "Saving predictions to CSV")
        save_predictions_to_csv(predictions, predictions_output)
        log_stage_complete("save", f"Predictions saved to {predictions_output}")

        log_stage_complete("ingest_pipeline", "Pipeline completed successfully")
        return predictions

    except Exception as e:
        log_stage_failure("ingest_pipeline", str(e))
        raise

def main():
    """Entry point for the ingest pipeline."""
    logger.info("Starting Ingest Pipeline (T015)")
    try:
        run_ingest_pipeline()
        logger.info("Ingest Pipeline finished successfully.")
    except Exception as e:
        logger.error(f"Ingest Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()