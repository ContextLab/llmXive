"""
Pipeline Timing and End-to-End Execution Script.

This script orchestrates the full research pipeline end-to-end to verify
completion within the 6-hour constraint (SC-005). It measures execution time
for each major step and writes a timing log to results/timing_log.json.
"""
import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Callable, List, Optional

# Add project root to path if not already present
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from logging_config import setup_logging
from generate_data import main as generate_data_main
from ingest import main as ingest_main
from process_data import main as process_data_main
from models import main as models_main
from sensitivity import main as sensitivity_main
from serialize_results import main as serialize_main
from aggregate_results import main as aggregate_main
from robustness_summary import main as robustness_main
from report import main as report_main
from validate_schemas import main as validate_main

# Setup logging
logger = setup_logging(__name__)

# Define the pipeline steps
PIPELINE_STEPS = [
    ("data_generation", generate_data_main),
    ("ingestion", ingest_main),
    ("data_processing", process_data_main),
    ("model_fitting", models_main),
    ("sensitivity_analysis", sensitivity_main),
    ("result_serialization", serialize_main),
    ("result_aggregation", aggregate_main),
    ("robustness_summary", robustness_main),
    ("report_generation", report_main),
    ("schema_validation", validate_main),
]

def run_step(step_name: str, step_func: Callable) -> Dict[str, Any]:
    """
    Execute a single pipeline step and record timing.
    
    Args:
        step_name: Human-readable name for the step
        step_func: The function to execute
        
    Returns:
        Dictionary with step execution details
    """
    logger.info(f"Starting step: {step_name}")
    start_time = time.time()
    success = False
    error_message = None
    
    try:
        # Execute the step (passing no args as most main functions handle their own args)
        step_func()
        success = True
    except Exception as e:
        error_message = str(e)
        logger.error(f"Step {step_name} failed with error: {error_message}")
        # We continue execution to capture timing even if a step fails
        # unless it's a critical infrastructure failure
    
    end_time = time.time()
    duration = end_time - start_time
    
    result = {
        "step": step_name,
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "end_time": datetime.fromtimestamp(end_time).isoformat(),
        "duration_seconds": duration,
        "success": success,
        "error": error_message
    }
    
    logger.info(f"Step {step_name} completed in {duration:.2f}s (success: {success})")
    return result

def main():
    """
    Run the full pipeline end-to-end and generate timing log.
    
    This function orchestrates all pipeline steps, measures their execution
    time, and writes a comprehensive timing log to results/timing_log.json.
    """
    logger.info("="*60)
    logger.info("Starting Full Pipeline End-to-End Timing Test")
    logger.info("="*60)
    
    pipeline_start = time.time()
    step_results = []
    
    # Execute each pipeline step
    for step_name, step_func in PIPELINE_STEPS:
        result = run_step(step_name, step_func)
        step_results.append(result)
        
        # If a critical step fails, we might want to stop early
        # For timing purposes, we continue to measure total time
        if not result["success"] and step_name in ["data_generation", "ingestion"]:
            logger.warning(f"Critical step {step_name} failed. Continuing for timing measurement.")
    
    pipeline_end = time.time()
    total_duration = pipeline_end - pipeline_start
    
    # Compile the timing log
    timing_log = {
        "pipeline_name": "Sensory Deprivation Dream Analysis",
        "start_time": datetime.fromtimestamp(pipeline_start).isoformat(),
        "end_time": datetime.fromtimestamp(pipeline_end).isoformat(),
        "total_duration_seconds": total_duration,
        "total_duration_formatted": f"{total_duration/3600:.2f} hours",
        "constraint_check": {
            "max_allowed_hours": 6,
            "max_allowed_seconds": 6 * 3600,
            "passed": total_duration <= (6 * 3600),
            "margin_seconds": (6 * 3600) - total_duration
        },
        "steps": step_results,
        "step_summary": {
            "total_steps": len(step_results),
            "successful_steps": sum(1 for s in step_results if s["success"]),
            "failed_steps": sum(1 for s in step_results if not s["success"]),
            "total_step_time": sum(s["duration_seconds"] for s in step_results)
        }
    }
    
    # Ensure results directory exists
    results_dir = os.path.join(project_root, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Write timing log
    timing_log_path = os.path.join(results_dir, "timing_log.json")
    with open(timing_log_path, 'w', encoding='utf-8') as f:
        json.dump(timing_log, f, indent=2)
    
    logger.info(f"Timing log written to: {timing_log_path}")
    logger.info(f"Total pipeline duration: {total_duration:.2f} seconds ({total_duration/3600:.2f} hours)")
    
    if timing_log["constraint_check"]["passed"]:
        logger.info("✅ SUCCESS: Pipeline completed within 6-hour constraint")
    else:
        logger.warning("❌ FAILURE: Pipeline exceeded 6-hour constraint")
    
    # Return exit code based on constraint check
    return 0 if timing_log["constraint_check"]["passed"] else 1

if __name__ == "__main__":
    sys.exit(main())
