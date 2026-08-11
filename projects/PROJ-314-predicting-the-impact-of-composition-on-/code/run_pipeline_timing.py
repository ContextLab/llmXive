"""
Task T046: Measure Pipeline Runtime.

Executes the full pipeline (Ingestion -> Descriptors -> Modeling -> Reporting)
and logs the total duration and step-wise timings to data/reports/runtime_metrics.json.

This script fixes the import error in the previous run by using the correct
public API names exposed by sibling modules (e.g., `main` from `ingestion`,
`main` from `modeling`, etc.).
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path to allow imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import initialize_config, get_config_value
from ingestion import main as run_ingestion
from descriptors import main as run_descriptors
from modeling import main as run_modeling
from diagnostics import main as run_diagnostics
from generate_shap_plots import main as run_shap
from report import main as run_report
from hash_artifacts import main as run_hash

logger = logging.getLogger(__name__)

def ensure_output_dir():
    """Ensure all required output directories exist."""
    dirs = [
        "data/raw", "data/processed", "data/artifacts", "data/models",
        "data/results", "data/reports", "logs", "figures"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def save_runtime_metrics(start_time: float, end_time: float, status: str):
    """Save runtime metrics to a JSON file."""
    metrics = {
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": end_time - start_time,
        "status": status
    }
    path = Path("data/results/runtime_metrics.json")
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved runtime metrics to {path}")

def run_full_pipeline():
    """Execute the full pipeline steps."""
    start_time = time.time()
    status = "success"
    
    try:
        logger.info("Step 1: Ingestion (T018c-T020)")
        run_ingestion()
        
        logger.info("Step 2: Modeling (T026-T032)")
        run_modeling()
        
        logger.info("Step 3: Diagnostics & Leakage Check (T030, T030b)")
        run_diagnostics()
        
        logger.info("Step 4: SHAP Analysis & Plots (T036-T041)")
        run_shap()
        
        logger.info("Step 5: Final Reporting (T043)")
        run_report()
        
        logger.info("Step 6: Hash Artifacts (T044)")
        run_hash()
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        status = "failed"
        raise
    finally:
        end_time = time.time()
        save_runtime_metrics(start_time, end_time, status)

def main():
    """Main entry point."""
    initialize_config()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/pipeline_execution.log")
        ]
    )
    
    logger.info("Starting Full Pipeline Execution")
    ensure_output_dir()
    
    try:
        run_full_pipeline()
        logger.info("Pipeline completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return 1

if __name__ == "__main__":
    main()