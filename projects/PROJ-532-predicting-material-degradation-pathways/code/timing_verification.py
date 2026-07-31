"""
Task T030: Verify execution time of full training/eval cycle is ≤ 6 hours on CPU runner.

This script executes the full training and evaluation pipeline (T024-T029) 
and measures the total wall-clock time. It outputs the timing results to 
results/metrics/timing_verification.json.

Requirements:
- Must run on CPU only
- Must complete in ≤ 6 hours (21600 seconds)
- Must use real data from data/processed/train_set.parquet
- Must use real model artifacts from results/artifacts/model.pkl
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Add code directory to path for imports
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from training import run_training_pipeline
from evaluation import run_evaluation_pipeline
from utils import setup_logging, save_json, ensure_dir

# Constants
MAX_EXECUTION_TIME_SECONDS = 6 * 60 * 60  # 6 hours
OUTPUT_DIR = Path("results/metrics")
OUTPUT_FILE = OUTPUT_DIR / "timing_verification.json"

def run_timed_training():
    """Run the training pipeline and return timing info."""
    start_time = time.time()
    
    try:
        # Run training pipeline
        model_artifact = run_training_pipeline()
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "status": "success",
            "duration_seconds": duration,
            "model_artifact": model_artifact
        }
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "status": "error",
            "duration_seconds": duration,
            "error": str(e)
        }

def run_timed_evaluation():
    """Run the evaluation pipeline and return timing info."""
    start_time = time.time()
    
    try:
        # Run evaluation pipeline
        evaluation_result = run_evaluation_pipeline()
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "status": "success",
            "duration_seconds": duration,
            "evaluation_result": evaluation_result
        }
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "status": "error",
            "duration_seconds": duration,
            "error": str(e)
        }

def main():
    """Main function to verify execution time."""
    # Setup logging
    logger = setup_logging("timing_verification", level=logging.INFO)
    logger.info("Starting T030: Execution time verification")
    
    # Ensure output directory exists
    ensure_dir(OUTPUT_DIR)
    
    # Initialize timing report
    timing_report: Dict[str, Any] = {
        "task_id": "T030",
        "max_allowed_seconds": MAX_EXECUTION_TIME_SECONDS,
        "max_allowed_hours": 6.0,
        "pipelines": {},
        "total_duration_seconds": 0.0,
        "total_duration_hours": 0.0,
        "status": "unknown",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }
    
    # Run training pipeline
    logger.info("Running training pipeline...")
    training_result = run_timed_training()
    
    timing_report["pipelines"]["training"] = {
        "status": training_result["status"],
        "duration_seconds": training_result["duration_seconds"],
        "duration_hours": training_result["duration_seconds"] / 3600.0
    }
    
    if training_result["status"] == "error":
        logger.error(f"Training pipeline failed: {training_result['error']}")
        timing_report["status"] = "failed"
        timing_report["total_duration_seconds"] = training_result["duration_seconds"]
        timing_report["total_duration_hours"] = training_result["duration_seconds"] / 3600.0
        save_json(OUTPUT_FILE, timing_report)
        return 1
    
    # Run evaluation pipeline
    logger.info("Running evaluation pipeline...")
    evaluation_result = run_timed_evaluation()
    
    timing_report["pipelines"]["evaluation"] = {
        "status": evaluation_result["status"],
        "duration_seconds": evaluation_result["duration_seconds"],
        "duration_hours": evaluation_result["duration_seconds"] / 3600.0
    }
    
    if evaluation_result["status"] == "error":
        logger.error(f"Evaluation pipeline failed: {evaluation_result['error']}")
        timing_report["status"] = "failed"
        timing_report["total_duration_seconds"] = (
            training_result["duration_seconds"] + evaluation_result["duration_seconds"]
        )
        timing_report["total_duration_hours"] = timing_report["total_duration_seconds"] / 3600.0
        save_json(OUTPUT_FILE, timing_report)
        return 1
    
    # Calculate total duration
    total_duration = (
        training_result["duration_seconds"] + 
        evaluation_result["duration_seconds"]
    )
    
    timing_report["total_duration_seconds"] = total_duration
    timing_report["total_duration_hours"] = total_duration / 3600.0
    
    # Check if within time limit
    if total_duration <= MAX_EXECUTION_TIME_SECONDS:
        timing_report["status"] = "passed"
        logger.info(f"✓ Execution time verification PASSED: {total_duration:.2f}s ≤ {MAX_EXECUTION_TIME_SECONDS}s")
    else:
        timing_report["status"] = "failed"
        logger.error(f"✗ Execution time verification FAILED: {total_duration:.2f}s > {MAX_EXECUTION_TIME_SECONDS}s")
    
    # Save timing report
    save_json(OUTPUT_FILE, timing_report)
    
    logger.info(f"Timing report saved to: {OUTPUT_FILE}")
    logger.info(f"Total execution time: {timing_report['total_duration_hours']:.2f} hours")
    
    return 0 if timing_report["status"] == "passed" else 1

if __name__ == "__main__":
    sys.exit(main())
