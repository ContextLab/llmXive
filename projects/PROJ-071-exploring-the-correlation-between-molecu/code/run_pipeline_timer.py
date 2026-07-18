"""
T041: Execute full pipeline script and measure total execution time.

This script orchestrates the full research pipeline (Ingestion -> Descriptors ->
Standardization -> Analysis -> Visualization -> Reporting) and measures the
end-to-end wall-clock time.

It imports and calls the `main` functions from the existing pipeline modules
to ensure a single coherent execution flow.
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.ingest import main as ingest_main
from code.descriptors import main as descriptors_main
from code.standardize import main as standardize_main
from code.analysis import main as analysis_main
from code.viz import main as viz_main
from code.report import main as report_main
from code.logging_config import setup_logging, get_logger

# Configure logging
setup_logging()
logger = get_logger(__name__)

def run_stage(name, stage_func):
    """Execute a pipeline stage and return duration."""
    logger.info(f"--- Starting Stage: {name} ---")
    start = time.perf_counter()
    try:
        stage_func()
        end = time.perf_counter()
        duration = end - start
        logger.info(f"--- Completed Stage: {name} in {duration:.2f}s ---")
        return duration
    except Exception as e:
        end = time.perf_counter()
        duration = end - start
        logger.error(f"--- Failed Stage: {name} after {duration:.2f}s ---")
        logger.exception(e)
        raise

def main():
    """Orchestrate the full pipeline and measure total time."""
    logger.info("Starting Full Pipeline Execution (T041)")
    start_time = time.perf_counter()
    start_timestamp = datetime.now().isoformat()

    stages_duration = {}
    total_duration = 0.0

    try:
        # 1. Ingestion & Data Availability Gate
        # Note: ingest_main handles fetching and merging.
        t_ingest = run_stage("Ingestion", ingest_main)
        stages_duration["ingest"] = t_ingest

        # 2. Descriptor Calculation
        # Note: descriptors_main calculates metrics on the merged data.
        t_desc = run_stage("Descriptors", descriptors_main)
        stages_duration["descriptors"] = t_desc

        # 3. Standardization & Stratification
        # Note: standardize_main handles unit conversion and filtering.
        t_std = run_stage("Standardization", standardize_main)
        stages_duration["standardization"] = t_std

        # 4. Correlation & Regression Analysis
        # Note: analysis_main performs stats and modeling.
        t_analysis = run_stage("Analysis", analysis_main)
        stages_duration["analysis"] = t_analysis

        # 5. Visualization
        # Note: viz_main generates plots based on analysis results.
        t_viz = run_stage("Visualization", viz_main)
        stages_duration["visualization"] = t_viz

        # 6. Reporting
        # Note: report_main generates the final markdown and JSON logs.
        t_report = run_stage("Reporting", report_main)
        stages_duration["reporting"] = t_report

        end_time = time.perf_counter()
        total_duration = end_time - start_time

        logger.info(f"Full Pipeline Completed Successfully.")
        logger.info(f"Total Execution Time: {total_duration:.2f} seconds")

        # Save execution metrics
        metrics = {
            "start_timestamp": start_timestamp,
            "end_timestamp": datetime.now().isoformat(),
            "total_duration_seconds": total_duration,
            "stages": stages_duration,
            "status": "completed"
        }

        output_path = project_root / "data" / "output" / "pipeline_metrics.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Metrics saved to {output_path}")
        print(f"Pipeline completed in {total_duration:.2f} seconds.")
        print(f"Metrics written to {output_path}")

    except Exception as e:
        end_time = time.perf_counter()
        total_duration = end_time - start_time
        logger.error(f"Pipeline failed after {total_duration:.2f}s")
        
        metrics = {
            "start_timestamp": start_timestamp,
            "end_timestamp": datetime.now().isoformat(),
            "total_duration_seconds": total_duration,
            "stages": stages_duration,
            "status": "failed",
            "error": str(e)
        }

        output_path = project_root / "data" / "output" / "pipeline_metrics.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)
        
        raise

if __name__ == "__main__":
    main()
