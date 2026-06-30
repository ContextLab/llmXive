"""
Benchmark script for the LALM Hallucination Analysis Pipeline.

Executes the full pipeline on a representative set of samples per domain
(Speech, Music, Environment) and records the duration of each stage and
the total execution time.

Output: results/benchmark_duration.json
"""
import json
import logging
import time
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Project imports based on provided API surface
from config import load_config, get_sample_limits, get_dataset_paths
from setup_logging import init_logging, get_logger, log_pipeline_start, log_pipeline_end
from load_audio import load_all_datasets
from preprocess_audio import preprocess_dataset
from run_inference import run_inference_pipeline
from detect_hallucination import detect_hallucinations
from runtime_guard import with_runtime_guards, check_aborted, get_abort_reason

# Ensure output directory exists
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

def run_benchmark():
    """
    Runs the full pipeline and measures time for each stage.
    Returns a dictionary of timing results.
    """
    config = load_config()
    logger = get_logger("benchmark")
    
    # Initialize logging for the pipeline
    log_pipeline_start(logger, "T033a: Benchmark Pipeline")

    results = {
        "task_id": "T033a",
        "stages": {},
        "total_duration_seconds": 0.0,
        "status": "completed"
    }

    start_total = time.time()

    try:
        # Stage 1: Load Datasets
        logger.info("Stage 1: Loading datasets...")
        t_start = time.time()
        
        # Load samples per domain (Speech, Music, Env)
        # The load_all_datasets function handles fetching from HF and converting to JSON
        # It respects sample limits defined in config
        datasets = load_all_datasets()
        
        t_end = time.time()
        results["stages"]["load_datasets"] = {
            "duration_seconds": round(t_end - t_start, 3),
            "domains_loaded": list(datasets.keys()) if datasets else []
        }
        logger.info(f"Stage 1 completed in {t_end - t_start:.3f}s")

        # Stage 2: Preprocessing
        logger.info("Stage 2: Preprocessing audio...")
        t_start = time.time()
        
        processed_data = {}
        for domain, samples in datasets.items():
            # Process each domain's samples
            processed_data[domain] = preprocess_dataset(samples, domain)
        
        t_end = time.time()
        results["stages"]["preprocessing"] = {
            "duration_seconds": round(t_end - t_start, 3),
            "samples_processed": sum(len(v) for v in processed_data.values())
        }
        logger.info(f"Stage 2 completed in {t_end - t_start:.3f}s")

        # Stage 3: Inference (Caption Generation)
        logger.info("Stage 3: Running inference...")
        t_start = time.time()
        
        # Run inference pipeline on processed data
        # This calls the model loading and generation logic
        inference_results = run_inference_pipeline(processed_data)
        
        t_end = time.time()
        results["stages"]["inference"] = {
            "duration_seconds": round(t_end - t_start, 3),
            "samples_inferred": len(inference_results) if isinstance(inference_results, list) else 0
        }
        logger.info(f"Stage 3 completed in {t_end - t_start:.3f}s")

        # Stage 4: Hallucination Detection
        logger.info("Stage 4: Detecting hallucinations...")
        t_start = time.time()
        
        # Detect hallucinations based on captions and ground truth
        detection_results = detect_hallucinations(inference_results)
        
        t_end = time.time()
        results["stages"]["detection"] = {
            "duration_seconds": round(t_end - t_start, 3),
            "samples_analyzed": len(detection_results) if isinstance(detection_results, list) else 0
        }
        logger.info(f"Stage 4 completed in {t_end - t_start:.3f}s")

    except Exception as e:
        logger.error(f"Pipeline failed during execution: {str(e)}", exc_info=True)
        results["status"] = "failed"
        results["error"] = str(e)
    
    finally:
        end_total = time.time()
        results["total_duration_seconds"] = round(end_total - start_total, 3)
        log_pipeline_end(logger, results["status"])

    return results

def main():
    """Main entry point for the benchmark script."""
    init_logging()
    logger = get_logger("benchmark")
    
    logger.info("Starting T033a Benchmark Pipeline...")
    
    # Run the benchmark with runtime guards (time/memory limits)
    # We wrap the main logic to ensure it doesn't hang or OOM
    @with_runtime_guards(time_limit=3600, memory_limit_gb=6) # 1 hour, 6GB RAM
    def run_with_guards():
        return run_benchmark()
    
    try:
        final_results = run_with_guards()
    except Exception as e:
        final_results = {
            "task_id": "T033a",
            "status": "failed",
            "error": str(e),
            "total_duration_seconds": 0.0,
            "stages": {}
        }
    
    # Write results to disk
    output_path = RESULTS_DIR / "benchmark_duration.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Benchmark results written to {output_path}")
    print(json.dumps(final_results, indent=2))
    
    return final_results

if __name__ == "__main__":
    main()
