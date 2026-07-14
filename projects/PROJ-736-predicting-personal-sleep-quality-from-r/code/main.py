"""Main orchestration script for the sleep quality prediction pipeline."""
import os
import sys
import json
import time
from pathlib import Path
from config import get_paths, ensure_dirs

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.download_hcp import download_hcp_data, main as download_main
from data.preprocess import main as preprocess_main
from data.feature_engineering import main as feature_main
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, setup_logging


def run_pipeline() -> bool:
    """Run the full data pipeline: download -> preprocess -> feature engineering."""
    paths = get_paths()
    log_dir = paths["logs"]
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "pipeline_run.json")
    
    # Setup logging
    setup_logging(log_file)
    log_stage_start("full_pipeline")
    
    success = True
    
    # Step 1: Download HCP data
    log_stage_start("Download HCP Data")
    if not download_hcp_data():
        log_stage_error("Download HCP Data", "Failed to download HCP data")
        success = False
    else:
        log_stage_complete("Download HCP Data")
    
    if not success:
        log_stage_complete("full_pipeline", {"status": "failed", "stage": "download"})
        return False
    
    # Step 2: Preprocess data
    # T014b: Import and invoke the preprocessing function from code/data/preprocess.py
    log_stage_start("Preprocessing")
    if not preprocess_main():
        log_stage_error("Preprocessing", "Failed to preprocess data")
        success = False
    else:
        log_stage_complete("Preprocessing")
    
    if not success:
        log_stage_complete("full_pipeline", {"status": "failed", "stage": "preprocessing"})
        return False
    
    # Step 3: Feature engineering (T014c)
    # Import and invoke the feature engineering function from code/data/feature_engineering.py
    # This processes the filtered subjects identified in T007b and produces the final connectivity vectors.
    log_stage_start("Feature Engineering")
    if not feature_main():
        log_stage_error("Feature Engineering", "Failed to compute features")
        success = False
    else:
        log_stage_complete("Feature Engineering")
    
    if success:
        log_stage_complete("full_pipeline", {"status": "success"})
    else:
        log_stage_complete("full_pipeline", {"status": "failed", "stage": "feature_engineering"})
        
    return success


def main() -> bool:
    """Main entry point."""
    success = run_pipeline()
    return success



if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
