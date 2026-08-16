"""
Pipeline execution wrapper with timing and resource monitoring.
Orchestrates the full research pipeline: Ingestion -> Modeling -> Diagnostics -> Reporting.
"""
import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion import main as run_ingestion
from modeling import main as run_modeling
from diagnostics import main as run_diagnostics
from report import main as run_reporting
from logger import setup_citation_logger

def ensure_output_dir(dir_path: str):
    """Ensure the output directory exists."""
    Path(dir_path).mkdir(parents=True, exist_ok=True)

def save_runtime_metrics(metrics: dict, output_path: str):
    """Save runtime metrics to a JSON file."""
    ensure_output_dir(os.path.dirname(output_path))
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logging.info(f"Runtime metrics saved to {output_path}")

def run_full_pipeline():
    """Execute the full pipeline stages sequentially."""
    start_time = time.time()
    stages = []
    errors = []

    # Stage 1: Ingestion
    try:
        logging.info("Starting Ingestion Stage...")
        stage_start = time.time()
        run_ingestion()
        stages.append({
            "stage": "ingestion",
            "status": "success",
            "duration_seconds": time.time() - stage_start
        })
    except Exception as e:
        error_msg = f"Ingestion failed: {str(e)}"
        logging.error(error_msg)
        errors.append({"stage": "ingestion", "error": error_msg})
        stages.append({
            "stage": "ingestion",
            "status": "failed",
            "error": str(e)
        })
        # Do not proceed if ingestion fails
        return stages, errors

    # Stage 2: Modeling
    try:
        logging.info("Starting Modeling Stage...")
        stage_start = time.time()
        run_modeling()
        stages.append({
            "stage": "modeling",
            "status": "success",
            "duration_seconds": time.time() - stage_start
        })
    except Exception as e:
        error_msg = f"Modeling failed: {str(e)}"
        logging.error(error_msg)
        errors.append({"stage": "modeling", "error": error_msg})
        stages.append({
            "stage": "modeling",
            "status": "failed",
            "error": str(e)
        })
        # Do not proceed if modeling fails
        return stages, errors

    # Stage 3: Diagnostics
    try:
        logging.info("Starting Diagnostics Stage...")
        stage_start = time.time()
        run_diagnostics()
        stages.append({
            "stage": "diagnostics",
            "status": "success",
            "duration_seconds": time.time() - stage_start
        })
    except Exception as e:
        error_msg = f"Diagnostics failed: {str(e)}"
        logging.error(error_msg)
        errors.append({"stage": "diagnostics", "error": error_msg})
        stages.append({
            "stage": "diagnostics",
            "status": "failed",
            "error": str(e)
        })
        # Do not proceed if diagnostics fails
        return stages, errors

    # Stage 4: Reporting
    try:
        logging.info("Starting Reporting Stage...")
        stage_start = time.time()
        run_reporting()
        stages.append({
            "stage": "reporting",
            "status": "success",
            "duration_seconds": time.time() - stage_start
        })
    except Exception as e:
        error_msg = f"Reporting failed: {str(e)}"
        logging.error(error_msg)
        errors.append({"stage": "reporting", "error": error_msg})
        stages.append({
            "stage": "reporting",
            "status": "failed",
            "error": str(e)
        })

    total_duration = time.time() - start_time
    return stages, errors, total_duration

def main():
    """Main entry point for the pipeline timing script."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/pipeline_timing.log')
        ]
    )

    # Ensure citation logger is set up
    setup_citation_logger()

    # Ensure output directories exist
    ensure_output_dir('data/reports')
    ensure_output_dir('data/results')
    ensure_output_dir('data/models')
    ensure_output_dir('logs')

    logging.info("Starting Full Pipeline Execution")

    try:
        stages, errors, total_duration = run_full_pipeline()

        # Compile metrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "total_duration_seconds": total_duration,
            "stages": stages,
            "errors": errors,
            "status": "success" if not errors else "partial_failure"
        }

        # Save metrics
        save_runtime_metrics(metrics, 'data/results/pipeline_timing_metrics.json')

        if errors:
            logging.error(f"Pipeline completed with {len(errors)} errors.")
            sys.exit(1)
        else:
            logging.info("Pipeline completed successfully.")
            sys.exit(0)

    except Exception as e:
        logging.critical(f"Pipeline execution failed catastrophically: {str(e)}")
        logging.critical(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
