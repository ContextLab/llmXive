"""
T042a: Run full pipeline end-to-end and capture timestamps.

This script orchestrates the entire pipeline execution and logs
start/end timestamps to outputs/pipeline_run.json.
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# Add project root to path if needed
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_output_path
from logging_config import setup_logging, get_logger

def log_pipeline_step(step_name: str, status: str, message: str = "") -> None:
    """Log a pipeline step with timestamp."""
    logger = get_logger(__name__)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "step": step_name,
        "status": status,
        "message": message
    }
    
    logger.info(json.dumps(log_entry))

def save_run_info(start_time: str, end_time: str, status: str = "completed") -> None:
    """Save pipeline run information to a JSON file."""
    run_info = {
        "start_time": start_time,
        "end_time": end_time,
        "status": status,
        "pipeline_version": "1.0.0"
    }
    
    run_info_path = get_output_path("pipeline_run.json")
    
    with open(run_info_path, 'w') as f:
        json.dump(run_info, f, indent=2)

def run_pipeline() -> None:
    """
    Execute the full pipeline end-to-end.
    
    This function orchestrates all pipeline stages in the correct order:
    1. Data download and verification (T010-T012)
    2. Preprocessing and alignment (T014-T020)
    3. Model training and evaluation (T024-T029)
    4. Feature importance and reporting (T033-T040)
    """
    logger = get_logger(__name__)
    
    # Import pipeline modules
    from download_data import main as download_main
    from preprocess import main as preprocess_main
    from generate_aligned_dataset import main as generate_dataset_main
    from train import main as train_main
    from evaluate import main as evaluate_main
    from report import main as report_main
    
    steps = [
        ("download_data", download_main, "Downloading and verifying OC20 data"),
        ("preprocess", preprocess_main, "Preprocessing and aligning dataset"),
        ("generate_aligned_dataset", generate_dataset_main, "Generating final aligned dataset"),
        ("train", train_main, "Training models with nested cross-validation"),
        ("evaluate", evaluate_main, "Evaluating models and performing statistical tests"),
        ("report", report_main, "Generating final report and feature importance analysis")
    ]
    
    for step_name, step_func, step_description in steps:
        log_pipeline_step(step_name, "started", step_description)
        logger.info(f"Executing {step_name}: {step_description}")
        
        try:
            step_func()
            log_pipeline_step(step_name, "completed", f"{step_description} - Success")
        except Exception as e:
            log_pipeline_step(step_name, "failed", f"{step_description} - Error: {str(e)}")
            raise

def main() -> None:
    """Main entry point for T042a."""
    setup_logging()
    logger = get_logger(__name__)
    
    # Capture start time
    start_time = datetime.now(timezone.utc).isoformat()
    logger.info(f"Pipeline started at {start_time}")
    
    try:
        run_pipeline()
        
        # Capture end time
        end_time = datetime.now(timezone.utc).isoformat()
        logger.info(f"Pipeline completed at {end_time}")
        
        # Save run info
        save_run_info(start_time, end_time, "completed")
        
        logger.info("Pipeline run information saved to outputs/pipeline_run.json")
        
    except Exception as e:
        end_time = datetime.now(timezone.utc).isoformat()
        save_run_info(start_time, end_time, "failed")
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()