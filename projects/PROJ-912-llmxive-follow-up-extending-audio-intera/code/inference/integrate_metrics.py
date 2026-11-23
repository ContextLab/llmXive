"""
Integration module to combine inference results and metrics into a single robustness report.

This module executes the inference runner for all available student models,
calculates performance metrics (AUC, latency, RAM), and aggregates them
into the final `data/processed/robustness_metrics.csv`.
"""
import os
import sys
import csv
import logging
import time
import tracemalloc
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports based on provided API surface
from config import get_path_config, get_evaluation_config
from utils.logger import get_logger, EvaluationError
from inference.runner import get_model_paths, load_student_model, run_inference_on_model, InferenceRunSummary
from inference.metrics import calculate_auc, get_peak_ram_mb, calculate_latency, check_constraints
from inference.logging_utils import log_inference_start, log_inference_summary, log_resource_usage_detailed

# Ensure path config is initialized
path_config = get_path_config()
logger = get_logger(__name__)

def get_model_metadata(model_paths: Dict[str, Path]) -> List[Dict[str, Any]]:
    """
    Extract metadata for each model to be included in the report.
    
    Args:
        model_paths: Dictionary mapping model_id to model path.
        
    Returns:
        List of dictionaries containing model_id and path.
    """
    metadata_list = []
    for model_id, path in model_paths.items():
        metadata_list.append({
            "model_id": model_id,
            "path": str(path)
        })
    return metadata_list

def run_integration() -> Dict[str, Any]:
    """
    Main integration function:
    1. Discover all student models.
    2. Run inference and metrics calculation for each.
    3. Aggregate results into a list of dictionaries.
    4. Write the final CSV to data/processed/robustness_metrics.csv.
    
    Returns:
        Dictionary containing the list of results and success status.
    """
    logger.info("Starting robustness metrics integration (T024).")
    
    # 1. Get model paths
    # This relies on T015 (checkpoint saving) having populated data/processed/
    model_paths = get_model_paths()
    
    if not model_paths:
        raise EvaluationError("No student models found. Ensure T015 (checkpoint saving) has been executed.")
    
    logger.info(f"Found {len(model_paths)} student models to evaluate.")
    
    results = []
    
    # 2. Iterate over models
    for model_id, model_path in model_paths.items():
        logger.info(f"Evaluating model: {model_id}")
        
        # Start tracking for this model
        tracemalloc.start()
        start_time = time.perf_counter()
        
        try:
            # Load model
            model = load_student_model(model_path)
            
            # Run inference (this returns InferenceRunSummary with logits/labels if needed for AUC)
            # Note: run_inference_on_model handles the batch processing and returns summary
            inference_summary: InferenceRunSummary = run_inference_on_model(model, model_id)
            
            # Calculate latency
            end_time = time.perf_counter()
            latency_ms = calculate_latency(start_time, end_time)
            
            # Calculate peak RAM
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            ram_gb = get_peak_ram_mb(peak) / 1024.0
            
            # Calculate AUC
            # The summary should contain logits and ground truth labels
            auc_score = calculate_auc(inference_summary.logits, inference_summary.labels)
            
            # Check constraints (logging side-effect)
            check_constraints(latency_ms, ram_gb, auc_score, logger)
            
            # Prepare result row
            result_row = {
                "model_id": model_id,
                "auc": round(auc_score, 4),
                "latency_ms": round(latency_ms, 2),
                "ram_gb": round(ram_gb, 4)
            }
            results.append(result_row)
            
            logger.info(f"Completed {model_id}: AUC={auc_score:.4f}, Latency={latency_ms:.2f}ms, RAM={ram_gb:.4f}GB")
            
        except Exception as e:
            logger.error(f"Failed to evaluate model {model_id}: {e}", exc_info=True)
            # We continue to next model, but we could also raise if strict mode is needed
            # For this task, we log and continue to ensure we generate as much data as possible
        finally:
            if tracemalloc.is_tracing():
                tracemalloc.stop()
    
    if not results:
        raise EvaluationError("No successful model evaluations occurred. Check logs for errors.")
    
    # 3. Write CSV
    output_dir = path_config.processed_data_dir
    output_path = output_dir / "robustness_metrics.csv"
    
    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    schema = ["model_id", "auc", "latency_ms", "ram_gb"]
    
    with open(output_path, mode='w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=schema)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Successfully wrote robustness metrics to {output_path}")
    
    # 4. Verify
    if not output_path.exists():
        raise EvaluationError(f"Verification failed: Output file {output_path} does not exist.")
    
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if len(rows) == 0:
            raise EvaluationError("Verification failed: Output CSV has 0 rows.")
        if set(reader.fieldnames) != set(schema):
            raise EvaluationError(f"Verification failed: CSV columns {reader.fieldnames} do not match schema {schema}.")
    
    logger.info(f"Verification passed: {len(rows)} rows, correct schema.")
    
    return {
        "success": True,
        "output_path": str(output_path),
        "row_count": len(results)
    }

def main():
    """Entry point for script execution."""
    try:
        result = run_integration()
        logger.info(f"Integration completed successfully. Output: {result['output_path']}")
        return 0
    except Exception as e:
        logger.critical(f"Integration failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
