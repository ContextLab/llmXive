"""
End-to-End Pipeline Timing Test (T038).

Executes the full simulation study pipeline:
1. Data Generation (T011)
2. Data Ingestion (T012)
3. Data Processing (T017)
4. Model Fitting (T020, T021, T024)
5. Sensitivity Analysis (T031, T034)
6. Report Generation (T035)

Measures total wall-clock time and writes results to:
results/timing_log.json

This script satisfies SC-005: Verify completion within 6 hours on GitHub Actions free-tier.
"""
import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

# Add project root to path to allow imports from code/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import pipeline components based on provided API surface
from code.generate_data import main as generate_data_main
from code.ingest import main as ingest_main
from code.process_data import main as process_data_main
from code.models import main as models_main
from code.sensitivity import main as sensitivity_main
from code.report import main as report_main
from code.logging_config import setup_logging
from code.save_synthetic_data import main as save_synthetic_main
from code.validate_data import main as validate_data_main
from code.serialize_results import main as serialize_main
from code.aggregate_results import main as aggregate_main
from code.robustness_summary import main as robustness_main

# Setup logging
logger = setup_logging()

def run_step(step_name: str, func, *args, **kwargs) -> Dict[str, Any]:
    """Execute a pipeline step and measure its duration."""
    logger.info(f"--- Starting Step: {step_name} ---")
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"--- Completed Step: {step_name} in {duration:.2f}s ---")
        return {
            "step": step_name,
            "status": "success",
            "duration_seconds": duration,
            "result": result
        }
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"--- Failed Step: {step_name} after {duration:.2f}s --- Error: {str(e)}")
        return {
            "step": step_name,
            "status": "failed",
            "duration_seconds": duration,
            "error": str(e)
        }

def main():
    """Run the full pipeline and generate timing log."""
    logger.info("Starting End-to-End Pipeline Timing Test (T038)")
    start_total = time.time()
    
    results = []
    
    # Step 1: Generate Synthetic Data
    # Note: We call the main functions directly. They handle their own arguments/defaults.
    # In a real scenario, these might take CLI args, but for the timing test we assume defaults 
    # or environment configuration as per the project's standard run.
    results.append(run_step("Data Generation", generate_data_main))
    
    # Step 2: Save Synthetic Data
    results.append(run_step("Save Synthetic Data", save_synthetic_main))
    
    # Step 3: Ingest Data
    results.append(run_step("Data Ingestion", ingest_main))
    
    # Step 4: Validate Data
    results.append(run_step("Data Validation", validate_data_main))
    
    # Step 5: Process Data (Thresholds)
    results.append(run_step("Data Processing", process_data_main))
    
    # Step 6: Run Models
    results.append(run_step("Model Fitting", models_main))
    
    # Step 7: Serialize Results
    results.append(run_step("Result Serialization", serialize_main))
    
    # Step 8: Run Sensitivity Analysis
    results.append(run_step("Sensitivity Analysis", sensitivity_main))
    
    # Step 9: Aggregate Results
    results.append(run_step("Result Aggregation", aggregate_main))
    
    # Step 10: Robustness Summary
    results.append(run_step("Robustness Summary", robustness_main))
    
    # Step 11: Generate Report
    results.append(run_step("Report Generation", report_main))
    
    end_total = time.time()
    total_duration = end_total - start_total
    
    # Check for failures
    failed_steps = [r for r in results if r["status"] == "failed"]
    pipeline_status = "failed" if failed_steps else "success"
    
    # Prepare timing log
    timing_log = {
        "timestamp": datetime.now().isoformat(),
        "project": "PROJ-146-the-effect-of-sensory-deprivation-on-dre",
        "task_id": "T038",
        "total_duration_seconds": total_duration,
        "status": pipeline_status,
        "steps": results,
        "constraints": {
            "max_duration_hours": 6,
            "max_duration_seconds": 6 * 3600,
            "passed": total_duration <= (6 * 3600)
        }
    }
    
    # Ensure output directory exists
    output_dir = os.path.join(project_root, "results")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "timing_log.json")
    
    # Write timing log
    with open(output_path, "w") as f:
        json.dump(timing_log, f, indent=2)
    
    logger.info(f"Timing log written to: {output_path}")
    logger.info(f"Total Pipeline Duration: {total_duration:.2f} seconds ({total_duration/3600:.2f} hours)")
    
    if not timing_log["constraints"]["passed"]:
        logger.error("Pipeline exceeded 6-hour limit!")
        return 1
    
    if failed_steps:
        logger.error(f"Pipeline failed at steps: {[r['step'] for r in failed_steps]}")
        return 1
        
    logger.info("Pipeline completed successfully within time limit.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
