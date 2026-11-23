"""
Pipeline Integration Script.

This script orchestrates the entire pipeline:
1. Setup directories
2. Download and validate data
3. Compute features
4. Train model
5. Evaluate model
"""
import argparse
import json
import logging
import sys
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        "data/raw",
        "data/processed",
        "results",
        "code",
        "tests"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {dir_path}")

def main():
    """Main entry point for the pipeline integration script."""
    parser = argparse.ArgumentParser(description="Run the complete pipeline")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip data download"
    )
    args = parser.parse_args()
    
    logger.info("Starting pipeline integration...")
    
    # Ensure directories
    ensure_directories()
    
    # Step 1: Download and validate data (if not skipped)
    if not args.skip_download:
        logger.info("Step 1: Downloading and validating data...")
        # Import and run ingest
        from ingest import main as ingest_main
        if ingest_main() != 0:
            logger.error("Data ingestion failed")
            sys.exit(1)
    else:
        logger.info("Step 1: Skipping data download")
    
    # Step 2: Compute features
    logger.info("Step 2: Computing features...")
    from features import main as features_main
    if features_main() != 0:
        logger.error("Feature computation failed")
        sys.exit(1)
    
    # Step 3: Train model
    logger.info("Step 3: Training model...")
    from train import main as train_main
    if train_main() != 0:
        logger.error("Model training failed")
        sys.exit(1)
    
    # Step 4: Evaluate model
    logger.info("Step 4: Evaluating model...")
    from evaluate import main as evaluate_main
    if evaluate_main() != 0:
        logger.error("Model evaluation failed")
        sys.exit(1)
    
    logger.info("Pipeline completed successfully!")
    return 0

if __name__ == "__main__":
    exit(main())
