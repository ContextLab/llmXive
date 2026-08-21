"""
Main pipeline orchestrator for molecular property prediction.
Executes the full pipeline end-to-end as specified in quickstart.md.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Import pipeline components
from fetch_data import main as fetch_data_main
from confound_analysis import main as confound_main
from descriptor_pipeline import main as descriptor_pipeline_main
from dft_calculator import main as dft_main
from train_models import main as train_models_main
from evaluate_models import main as evaluate_models_main

def setup_logging():
    """Setup logging for the main pipeline."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "pipeline.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("main_pipeline")

def run_pipeline():
    """Execute the full pipeline end-to-end."""
    logger = setup_logging()
    logger.info("Starting full pipeline execution")
    
    try:
        # Step 1: Fetch data
        logger.info("Step 1: Fetching data")
        fetch_data_main()
        
        # Step 2: Confound analysis
        logger.info("Step 2: Running confound analysis")
        confound_main()
        
        # Step 3: Generate semi-empirical descriptors
        logger.info("Step 3: Generating semi-empirical descriptors")
        descriptor_pipeline_main()
        
        # Step 4: Select subset and run DFT calculations
        logger.info("Step 4: Running DFT calculations on subset")
        dft_main()
        
        # Step 5: Train models
        logger.info("Step 5: Training models")
        train_models_main()
        
        # Step 6: Evaluate models
        logger.info("Step 6: Evaluating models")
        evaluate_models_main()
        
        logger.info("Pipeline execution complete")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run full molecular property prediction pipeline")
    parser.add_argument('--skip-fetch', action='store_true', help='Skip data fetching')
    args = parser.parse_args()
    
    if not args.skip_fetch:
        run_pipeline()
    else:
        logger = setup_logging()
        logger.warning("Skipping data fetching as requested")
        # Continue with other steps if needed

if __name__ == "__main__":
    main()