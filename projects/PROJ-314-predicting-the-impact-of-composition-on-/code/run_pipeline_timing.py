"""
Pipeline execution orchestrator with timing and error handling.
This script coordinates the full research pipeline: Ingestion -> Modeling -> Interpretation.
"""
import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path

# Add project root to path to allow relative imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import initialize_config, get_config_value
from ingestion import main as run_ingestion
from modeling import main as run_modeling
from generate_shap_plots import main as run_shap
from logger import logger

def ensure_output_dir():
    """Ensure all required output directories exist."""
    dirs = [
        "data/raw", "data/processed", "data/artifacts",
        "data/results", "data/models", "data/reports",
        "logs"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def save_runtime_metrics(start_time: float, status: str, error_msg: str = None):
    """Save runtime metrics to a JSON file."""
    end_time = time.time()
    duration = end_time - start_time
    
    metrics = {
        "status": status,
        "duration_seconds": duration,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "error": error_msg
    }
    
    output_path = "data/results/runtime_metrics.json"
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Runtime metrics saved to {output_path}")

def run_full_pipeline():
    """Execute the full research pipeline."""
    logger.info("Starting full research pipeline...")
    start_time = time.time()
    
    try:
        # 1. Ingestion
        logger.info("Phase 1: Data Ingestion...")
        run_ingestion()
        
        # 2. Modeling
        logger.info("Phase 2: Predictive Modeling...")
        run_modeling()
        
        # 3. Interpretation
        logger.info("Phase 3: Interpretation & Reporting...")
        run_shap()
        
        logger.info("Pipeline completed successfully.")
        save_runtime_metrics(start_time, "success")
        return 0
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Pipeline failed: {error_msg}")
        logger.error(traceback.format_exc())
        save_runtime_metrics(start_time, "failed", error_msg)
        return 1

def main():
    """Main entry point."""
    initialize_config()
    ensure_output_dir()
    sys.exit(run_full_pipeline())

if __name__ == "__main__":
    main()
