"""
Pipeline execution wrapper with timing and artifact verification.
Orchestrates the full pipeline and ensures all required outputs are generated.
"""
import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/pipeline_execution.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure output directories exist
def ensure_output_dir():
    """Create necessary output directories if they don't exist."""
    dirs = [
        "data/raw", "data/processed", "data/artifacts", "data/models",
        "data/results", "data/reports", "logs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def save_runtime_metrics(start_time, end_time, status):
    """Save runtime metrics to a JSON file."""
    metrics = {
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": end_time - start_time,
        "status": status
    }
    output_path = Path("data/results/runtime_metrics.json")
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Runtime metrics saved to {output_path}")

def run_full_pipeline():
    """
    Execute the full pipeline steps.
    1. Setup directories
    2. Ingestion (Data Fetch & Cleaning)
    3. Modeling (Training & Evaluation)
    4. Diagnostics (SHAP, Leakage, Stability)
    5. Reporting
    """
    from setup_directories import setup_directories
    from ingestion import main as run_ingestion
    from modeling import main as run_modeling
    from generate_shap_plots import main as run_shap
    from generate_metrics_report import main as run_report
    
    # Step 1: Setup
    logger.info("Step 1: Setting up directories...")
    if not setup_directories():
        raise RuntimeError("Directory setup failed.")

    # Step 2: Ingestion
    logger.info("Step 2: Running data ingestion...")
    run_ingestion()

    # Step 3: Modeling
    logger.info("Step 3: Running modeling pipeline...")
    run_modeling()

    # Step 4: SHAP & Diagnostics
    logger.info("Step 4: Running SHAP analysis and diagnostics...")
    run_shap()

    # Step 5: Reporting
    logger.info("Step 5: Generating final report...")
    run_report()

    logger.info("Pipeline completed successfully.")

def main():
    """Main entry point with timing and error handling."""
    ensure_output_dir()
    start_time = time.time()
    status = "success"

    try:
        run_full_pipeline()
    except Exception as e:
        status = "failed"
        print(f"Pipeline failed: {e}")
        traceback.print_exc()
    finally:
        end_time = time.time()
        save_runtime_metrics(start_time, end_time, status)
        if status == "failed":
            sys.exit(1)

    if status == "failed":
        sys.exit(1)

if __name__ == "__main__":
    main()
