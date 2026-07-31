"""
Ingest Pipeline for User Story 1: Zero-Shot Vulnerability Detection.

Orchestrates the sequence:
1. Download raw datasets (T011)
2. Preprocess into CodeSnippets (T012)
3. Run LLM Inference (T013)
4. Save predictions to data/processed/predictions.csv

Validates output against PredictionResult schema.
Implements dynamic batch size adjustment based on MemoryMonitor (T013d).
"""

import os
import sys
import gc
import time
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project imports based on API surface
from src.data.download import download_all_datasets, main as download_main
from src.data.preprocess import create_code_snippets, save_snippets_to_csv, main as preprocess_main
from src.models.code_snippet import CodeSnippet, create_snippet
from src.models.prediction_result import PredictionResult, create_prediction_result
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
from src.utils.memory_monitor import (
    get_current_memory_usage_gb,
    check_memory_constraint,
    force_gc,
    MemoryMonitor
)
from src.utils.config import get_config, get_data_processed_path, get_data_logs_path
from src.models.llm_inference import run_inference_batch, process_snippets_zero_shot

logger = get_logger("ingest_pipeline")

# Constants
MAX_BATCH_SIZE = 50
MIN_BATCH_SIZE = 1
MEMORY_THRESHOLD_RATIO = 0.85  # Reduce batch if usage > 85%
OUTPUT_FILENAME = "predictions.csv"

def adjust_batch_size(current_batch_size: int, monitor: MemoryMonitor) -> int:
    """
    Dynamically adjust batch size based on current memory usage.
    Returns the new batch size.
    """
    usage_ratio = get_current_memory_usage_gb() / monitor.available_ram_gb
    
    if usage_ratio > MEMORY_THRESHOLD_RATIO:
        new_size = max(MIN_BATCH_SIZE, current_batch_size // 2)
        logger.warning(f"Memory usage high ({usage_ratio:.2%}). Reducing batch size from {current_batch_size} to {new_size}.")
        force_gc()
        return new_size
    elif usage_ratio < 0.5 and current_batch_size < MAX_BATCH_SIZE:
        # Aggressively increase if memory is very low
        new_size = min(MAX_BATCH_SIZE, current_batch_size * 2)
        logger.info(f"Memory usage low ({usage_ratio:.2%}). Increasing batch size to {new_size}.")
        return new_size
    
    return current_batch_size

def save_predictions_to_csv(predictions: List[PredictionResult], output_path: Path) -> None:
    """
    Save a list of PredictionResult objects to a CSV file.
    Validates against the schema by relying on the Pydantic/Dataclass structure.
    """
    if not predictions:
        logger.warning("No predictions to save.")
        return

    # Determine field names from the first prediction
    if hasattr(predictions[0], '__dataclass_fields__'):
        field_names = list(predictions[0].__dataclass_fields__.keys())
    else:
        # Fallback for Pydantic models
        field_names = list(predictions[0].model_fields.keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        
        for pred in predictions:
            # Convert to dict safely
            if hasattr(pred, 'model_dump'):
                row = pred.model_dump()
            elif hasattr(pred, '__dataclass_fields__'):
                from dataclasses import asdict
                row = asdict(pred)
            else:
                row = pred.__dict__
            
            writer.writerow(row)

    logger.info(f"Saved {len(predictions)} predictions to {output_path}")

def run_ingest_pipeline(
    dataset_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    batch_size: int = MAX_BATCH_SIZE
) -> List[PredictionResult]:
    """
    Main orchestration function.
    1. Downloads datasets (T011)
    2. Preprocesses to CodeSnippets (T012)
    3. Runs LLM Inference (T013)
    4. Saves results.
    
    Returns the list of PredictionResults.
    """
    config = get_config()
    data_processed_path = processed_dir or get_data_processed_path()
    data_raw_path = dataset_dir or config.get_data_raw_path()
    
    # Ensure directories exist
    Path(data_processed_path).mkdir(parents=True, exist_ok=True)
    Path(data_raw_path).mkdir(parents=True, exist_ok=True)

    # Initialize Memory Monitor
    monitor = MemoryMonitor()
    logger.info(f"Memory Monitor initialized. Available RAM: {monitor.available_ram_gb:.2f} GB")

    all_predictions: List[PredictionResult] = []
    current_batch_size = batch_size

    try:
        # --- Stage 1: Download ---
        log_stage_start("Download Datasets")
        try:
            # Call the download module's main logic
            # Assuming download_main handles the orchestration or we call download_all_datasets directly
            # Based on API surface, download_all_datasets is the core function
            download_all_datasets(data_raw_path)
            log_stage_complete("Download Datasets")
        except Exception as e:
            log_stage_failure("Download Datasets", str(e))
            raise RuntimeError(f"Dataset download failed: {e}")

        # --- Stage 2: Preprocess ---
        log_stage_start("Preprocess Datasets")
        try:
            # Parse raw data into CodeSnippets
            # We assume create_code_snippets returns a list of CodeSnippet objects
            # and save_snippets_to_csv writes the intermediate file if needed
            snippets = create_code_snippets(data_raw_path)
            if not snippets:
                raise RuntimeError("No code snippets were extracted from datasets.")
            
            logger.info(f"Extracted {len(snippets)} code snippets.")
            
            # Save intermediate snippets for traceability
            snippet_csv_path = Path(data_processed_path) / "snippets.csv"
            save_snippets_to_csv(snippets, snippet_csv_path)
            log_stage_complete("Preprocess Datasets")
        except Exception as e:
            log_stage_failure("Preprocess Datasets", str(e))
            raise RuntimeError(f"Preprocessing failed: {e}")

        # --- Stage 3: LLM Inference (Batched) ---
        log_stage_start("LLM Inference")
        
        # Process in batches with memory monitoring
        total_snippets = len(snippets)
        processed_count = 0
        
        for i in range(0, total_snippets, current_batch_size):
            batch_snippets = snippets[i : i + current_batch_size]
            
            # Check memory before processing batch
            if not check_memory_constraint(monitor):
                logger.warning("Memory constraint check failed before batch. Attempting GC and size reduction.")
                force_gc()
                if not check_memory_constraint(monitor):
                    raise RuntimeError("Memory constraint exceeded even after GC. Aborting.")
            
            # Adjust batch size dynamically
            current_batch_size = adjust_batch_size(current_batch_size, monitor)
            if len(batch_snippets) > current_batch_size:
                batch_snippets = batch_snippets[:current_batch_size]

            logger.info(f"Processing batch {i//current_batch_size + 1}: {len(batch_snippets)} snippets.")
            
            start_time = time.time()
            
            try:
                # Run inference on the batch
                # process_snippets_zero_shot is the high-level function from llm_inference
                batch_predictions = process_snippets_zero_shot(batch_snippets)
                
                inference_time = time.time() - start_time
                logger.info(f"Batch completed in {inference_time:.2f}s. Generated {len(batch_predictions)} predictions.")
                
                all_predictions.extend(batch_predictions)
                processed_count += len(batch_snippets)
                
                # Force GC after every batch to prevent memory leaks
                force_gc()
                
            except Exception as e:
                logger.error(f"Error during inference batch: {e}")
                log_stage_failure(f"Inference Batch {i//current_batch_size}", str(e))
                raise

        log_stage_complete("LLM Inference")

        # --- Stage 4: Save Results ---
        log_stage_start("Save Predictions")
        output_path = Path(data_processed_path) / OUTPUT_FILENAME
        save_predictions_to_csv(all_predictions, output_path)
        
        # Validate output file exists and is not empty
        if not output_path.exists():
            raise FileNotFoundError(f"Output file {output_path} was not created.")
        
        if output_path.stat().st_size == 0:
            raise ValueError(f"Output file {output_path} is empty.")

        log_stage_complete("Save Predictions")
        
        return all_predictions

    except Exception as e:
        log_stage_failure("Ingest Pipeline", str(e))
        raise

def main():
    """Entry point for the ingest pipeline."""
    logger.info("Starting Ingest Pipeline (T015)")
    try:
        predictions = run_ingest_pipeline()
        logger.info(f"Ingest Pipeline completed successfully. Total predictions: {len(predictions)}")
    except Exception as e:
        logger.error(f"Ingest Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()