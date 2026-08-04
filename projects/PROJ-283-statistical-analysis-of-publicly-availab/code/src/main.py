import sys
import logging
import argparse
from pathlib import Path
import json
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_download_stage():
    """Run the data download stage."""
    from src.data.download import download_dataset, DataFetchError
    
    logger.info("Starting download stage")
    try:
        output_path = download_dataset()
        logger.info(f"Download completed: {output_path}")
        return output_path
    except DataFetchError as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Download stage error: {e}")
        sys.exit(1)

def run_processing_stage():
    """Run the data processing stage."""
    from src.data.parse import main as parse_main
    from src.data.process import main as process_main
    
    logger.info("Starting processing stage")
    try:
        parse_main()
        process_main()
        logger.info("Processing stage completed")
    except Exception as e:
        logger.error(f"Processing stage error: {e}")
        sys.exit(1)

def run_modeling_stage():
    """Run the modeling stage."""
    from src.models.fit import main as fit_main
    
    logger.info("Starting modeling stage")
    try:
        fit_main()
        logger.info("Modeling stage completed")
    except Exception as e:
        logger.error(f"Modeling stage error: {e}")
        sys.exit(1)

def run_validation_stage():
    """Run the validation and reporting stage."""
    from src.validation.validate_contracts import main as validate_main
    from src.models.validate import main as validate_model_main
    from src.reports.generate_plots import main as plots_main
    
    logger.info("Starting validation stage")
    try:
        # Validate data contracts
        validate_main()
        
        # Run model validation
        validate_model_main()
        
        # Generate diagnostic plots
        plots_main()
        
        logger.info("Validation stage completed")
    except Exception as e:
        logger.error(f"Validation stage error: {e}")
        sys.exit(1)

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description='Chess Elo Analysis Pipeline')
    parser.add_argument('--config', type=str, default='config.yaml',
                      help='Path to configuration file')
    
    args = parser.parse_args()
    
    logger.info("Starting Chess Elo Analysis Pipeline")
    
    # Run all stages
    run_download_stage()
    run_processing_stage()
    run_modeling_stage()
    run_validation_stage()
    
    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()
