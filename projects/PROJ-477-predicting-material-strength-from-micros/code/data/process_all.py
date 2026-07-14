"""
Orchestration script to chain the full data processing pipeline:
1. Download raw dataset
2. Preprocess images (resize, normalize)
3. Split into train/val/test sets
4. Validate the resulting splits

This script relies on the following modules:
- code/data/download.py
- code/data/preprocess.py
- code/data/split.py
- code/data/validate.py
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path to ensure imports work correctly
# Assuming this script is run from the project root or code directory
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_project_root, get_data_dir, get_processed_dir, get_raw_dir, get_results_dir, set_seed, get_seed
from utils.logging_config import get_logger

# Import pipeline stages
from data.download import main as download_main
from data.preprocess import main as preprocess_main
from data.split import main as split_main
from data.validate import main as validate_main


def setup_pipeline_logging():
    """Configure logging for the orchestration script."""
    logger = get_logger("process_all")
    logger.setLevel(logging.INFO)
    return logger


def run_download(logger):
    """Execute the download stage."""
    logger.info("Stage 1/4: Starting dataset download...")
    try:
        # Simulate calling the main function of the download module
        # We pass arguments programmatically or rely on defaults if supported
        # The download module expects args or uses defaults. We construct a mock namespace if needed.
        # However, since we are importing 'main', we assume it handles its own argparse or defaults.
        # To ensure it runs in this context, we might need to inject args if it strictly requires CLI.
        # Let's assume the modules are designed to be callable or we replicate the logic.
        
        # Re-implementing the logic from download.py's main to ensure it runs without CLI args
        from data.download import download_and_prepare, calculate_sha256
        raw_dir = get_raw_dir()
        processed_dir = get_processed_dir()
        
        # Ensure directories exist
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Call the core logic. Assuming download_and_prepare handles the download.
        # If it requires specific args, we pass them here.
        # Based on typical patterns:
        download_and_prepare(raw_dir, processed_dir)
        
        logger.info("Stage 1/4: Download completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Stage 1/4: Download failed with error: {e}")
        return False


def run_preprocess(logger):
    """Execute the preprocessing stage."""
    logger.info("Stage 2/4: Starting image preprocessing...")
    try:
        from data.preprocess import preprocess_dataset
        raw_dir = get_raw_dir()
        processed_dir = get_processed_dir()
        
        if not processed_dir.exists():
            processed_dir.mkdir(parents=True, exist_ok=True)

        # Call the core logic
        preprocess_dataset(raw_dir, processed_dir)
        
        logger.info("Stage 2/4: Preprocessing completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Stage 2/4: Preprocessing failed with error: {e}")
        return False


def run_split(logger):
    """Execute the splitting stage."""
    logger.info("Stage 3/4: Starting dataset splitting...")
    try:
        from data.split import generate_split_manifests
        processed_dir = get_processed_dir()
        results_dir = get_results_dir()
        
        if not results_dir.exists():
            results_dir.mkdir(parents=True, exist_ok=True)

        # Call the core logic
        generate_split_manifests(processed_dir, results_dir)
        
        logger.info("Stage 3/4: Splitting completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Stage 3/4: Splitting failed with error: {e}")
        return False


def run_validate(logger):
    """Execute the validation stage."""
    logger.info("Stage 4/4: Starting dataset validation...")
    try:
        from data.validate import run_validation
        results_dir = get_results_dir()
        
        if not results_dir.exists():
            results_dir.mkdir(parents=True, exist_ok=True)

        # Call the core logic
        run_validation(results_dir)
        
        logger.info("Stage 4/4: Validation completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Stage 4/4: Validation failed with error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Orchestrate the full material strength data pipeline.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    # Set seed
    set_seed(args.seed)
    logger = setup_pipeline_logging()
    
    logger.info(f"Starting pipeline with seed: {get_seed()}")
    
    # Execute stages sequentially
    stages = [
        ("Download", run_download),
        ("Preprocess", run_preprocess),
        ("Split", run_split),
        ("Validate", run_validate),
    ]
    
    success = True
    for stage_name, stage_func in stages:
        if not stage_func(logger):
            success = False
            logger.error(f"Pipeline aborted at stage: {stage_name}")
            break
    
    if success:
        logger.info("Pipeline completed successfully.")
        return 0
    else:
        logger.error("Pipeline failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())