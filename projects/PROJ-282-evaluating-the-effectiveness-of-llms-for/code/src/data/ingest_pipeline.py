"""
Ingest Pipeline: Orchestrates download, preprocessing, and LLM inference.

This script runs the full User Story 1 pipeline:
1. Downloads raw datasets (T011)
2. Preprocesses them into CodeSnippets (T012)
3. Runs Zero-Shot LLM Inference (T013, T014)
4. Outputs predictions.csv conforming to PredictionResult schema.

Memory Safety: Implements dynamic batch size adjustment based on available RAM.
"""
import os
import sys
import gc
import time
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports matching API surface
from src.data.download import download_all_datasets, validate_dataset
from src.data.preprocess import create_code_snippets, save_snippets_to_csv
from src.models.llm_inference import (
    InferenceConfig, 
    get_available_ram_gb, 
    check_memory_constraint,
    load_model_4bit_cpu,
    run_inference_batch,
    process_snippets_zero_shot,
    parse_llm_response
)
from src.models.prediction_result import PredictionResult, create_prediction_result, prediction_result_to_dict
from src.models.code_snippet import CodeSnippet
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure, create_project_logger
from src.utils.config import get_config

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = DATA_PROCESSED_DIR / "predictions.csv"
LOG_FILE = PROJECT_ROOT / "logs" / "ingest_pipeline.log"

# Ensure directories exist
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "logs").mkdir(parents=True, exist_ok=True)

logger = create_project_logger("ingest_pipeline", LOG_FILE)

def adjust_batch_size(initial_batch: int, min_batch: int = 1) -> int:
    """
    Dynamic batch size adjustment based on available RAM.
    Checks current RAM usage and reduces batch size if constraints are violated.
    """
    current_batch = initial_batch
    ram_gb = get_available_ram_gb()
    
    # Safety threshold: ensure we don't exceed 70% of available RAM for safety margin
    # T004 specifies a hard limit of ~7GB, but we check dynamically
    if ram_gb < 2.0:
        logger.warning(f"Very low RAM detected ({ram_gb:.2f}GB). Setting batch size to {min_batch}.")
        return min_batch
    
    # Heuristic: If RAM is tight (< 4GB), reduce batch size
    if ram_gb < 4.0:
        current_batch = max(min_batch, initial_batch // 2)
        logger.info(f"Low RAM ({ram_gb:.2f}GB). Reduced batch size to {current_batch}.")
    elif ram_gb < 6.0:
        current_batch = max(min_batch, initial_batch // 4)
        logger.info(f"Moderate RAM ({ram_gb:.2f}GB). Reduced batch size to {current_batch}.")
    
    return current_batch

def run_ingest_pipeline(
    batch_size: int = 8, 
    max_retries: int = 3,
    force_redownload: bool = False
) -> List[PredictionResult]:
    """
    Main orchestration function for the ingest pipeline.
    
    Args:
        batch_size: Initial batch size for LLM inference.
        max_retries: Number of retries for memory failures.
        force_redownload: If True, re-downloads datasets.
        
    Returns:
        List of PredictionResult objects.
    """
    log_stage_start(logger, "Ingest Pipeline", batch_size=batch_size)
    
    all_predictions: List[PredictionResult] = []
    
    # Step 1: Download Datasets
    log_stage_start(logger, "Step 1: Downloading Datasets")
    try:
        download_all_datasets(DATA_RAW_DIR, force=force_redownload)
        # Validate integrity
        if not validate_dataset(DATA_RAW_DIR):
            raise RuntimeError("Dataset validation failed.")
        log_stage_complete(logger, "Step 1: Downloading Datasets")
    except Exception as e:
        log_stage_failure(logger, "Step 1: Downloading Datasets", str(e))
        raise e
    
    # Step 2: Preprocess Data
    log_stage_start(logger, "Step 2: Preprocessing Datasets")
    try:
        # This function is expected to return a list of CodeSnippet objects
        # based on the API surface provided in T012
        snippets = create_code_snippets(DATA_RAW_DIR)
        if not snippets:
            raise RuntimeError("No snippets extracted from datasets.")
        
        logger.info(f"Extracted {len(snippets)} code snippets.")
        
        # Save intermediate CSV for debugging/audit (optional but good practice)
        save_snippets_to_csv(snippets, DATA_PROCESSED_DIR / "snippets_raw.csv")
        log_stage_complete(logger, "Step 2: Preprocessing Datasets")
    except Exception as e:
        log_stage_failure(logger, "Step 2: Preprocessing Datasets", str(e))
        raise e
    
    # Step 3: LLM Inference with Dynamic Batch Sizing
    log_stage_start(logger, "Step 3: Running LLM Inference")
    
    # Load model once
    try:
        logger.info("Loading model in 4-bit quantized mode on CPU...")
        model, tokenizer = load_model_4bit_cpu()
        log_stage_complete(logger, "Model Loaded")
    except Exception as e:
        log_stage_failure(logger, "Model Loading", str(e))
        raise e
    
    inference_config = InferenceConfig(
        temperature=0.0,
        max_new_tokens=256,
        top_p=1.0,
        do_sample=False
    )
    
    current_batch = adjust_batch_size(batch_size)
    retry_count = 0
    total_processed = 0
    
    while total_processed < len(snippets):
        gc.collect()
        if not check_memory_constraint(threshold_gb=6.5): # Safety margin
            if retry_count < max_retries:
                logger.warning("Memory constraint violated. Reducing batch size and retrying.")
                current_batch = max(1, current_batch // 2)
                retry_count += 1
                gc.collect()
                time.sleep(2)
                continue
            else:
                raise MemoryError(f"Memory constraint violated after {max_retries} retries. Current batch size: {current_batch}")
        
        # Slice batch
        batch_snippets = snippets[total_processed : total_processed + current_batch]
        batch_ids = [s.id for s in batch_snippets]
        
        logger.info(f"Processing batch {total_processed//current_batch + 1}: {len(batch_snippets)} samples (Batch Size: {current_batch})")
        
        try:
            # Run inference on the batch
            # process_snippets_zero_shot returns a list of raw LLM outputs or dicts
            # We assume it handles the prompt construction internally based on T013
            raw_outputs = process_snippets_zero_shot(
                model=model, 
                tokenizer=tokenizer, 
                snippets=batch_snippets, 
                config=inference_config
            )
            
            # Parse and map to PredictionResult
            for snippet, raw_output in zip(batch_snippets, raw_outputs):
                # Parse the LLM response to get label/category
                parsed = parse_llm_response(raw_output)
                
                # Determine correctness
                is_correct = (
                    parsed.get('predicted_label') == snippet.ground_truth_label and
                    parsed.get('predicted_category') == snippet.ground_truth_category
                )
                
                # Create PredictionResult
                pred_result = create_prediction_result(
                    snippet=snippet,
                    predicted_label=parsed.get('predicted_label'),
                    predicted_category=parsed.get('predicted_category'),
                    is_correct=is_correct,
                    inference_time_ms=parsed.get('inference_time_ms', 0.0)
                )
                all_predictions.append(pred_result)
            
            total_processed += len(batch_snippets)
            retry_count = 0 # Reset retry on success
            
        except MemoryError:
            logger.warning("MemoryError during batch processing. Reducing batch size.")
            current_batch = max(1, current_batch // 2)
            retry_count += 1
            continue
        except Exception as e:
            log_stage_failure(logger, f"Inference Batch {total_processed//current_batch}", str(e))
            raise e
    
    log_stage_complete(logger, "Step 3: Running LLM Inference", samples_processed=len(all_predictions))
    
    return all_predictions

def save_predictions_to_csv(predictions: List[PredictionResult], output_path: Path):
    """
    Saves predictions to CSV strictly conforming to the PredictionResult schema.
    """
    if not predictions:
        logger.warning("No predictions to save.")
        return
    
    # Define headers based on PredictionResult dataclass fields
    # Fields: snippet_id, predicted_label, predicted_category, is_correct, inference_time_ms
    fieldnames = ['snippet_id', 'predicted_label', 'predicted_category', 'is_correct', 'inference_time_ms']
    
    logger.info(f"Saving {len(predictions)} predictions to {output_path}")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for pred in predictions:
            row = {
                'snippet_id': pred.snippet_id,
                'predicted_label': pred.predicted_label,
                'predicted_category': pred.predicted_category,
                'is_correct': str(pred.is_correct), # CSV boolean as string
                'inference_time_ms': pred.inference_time_ms
            }
            writer.writerow(row)
    
    logger.info(f"Successfully saved predictions to {output_path}")

def main():
    """Entry point for the ingest pipeline."""
    logger.info("Starting Ingest Pipeline...")
    
    try:
        # Run the pipeline
        predictions = run_ingest_pipeline(batch_size=4) # Conservative start
        
        # Save output
        if not OUTPUT_FILE.parent.exists():
            OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        save_predictions_to_csv(predictions, OUTPUT_FILE)
        
        logger.info("Ingest Pipeline completed successfully.")
        print(f"Pipeline complete. Output saved to: {OUTPUT_FILE}")
        
    except Exception as e:
        logger.error(f"Ingest Pipeline failed: {str(e)}")
        log_stage_failure(logger, "Ingest Pipeline", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()