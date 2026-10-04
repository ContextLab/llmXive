"""
Main orchestrator for the Pupil Dilation and Cognitive Load Pipeline.
Executes the full pipeline: data loading, preprocessing, feature extraction,
correlation analysis, and model fitting.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import load_config
from preprocessing.load_data import run_loading_pipeline
from preprocessing.preprocess import run_preprocessing_pipeline
from preprocessing.features import process_dataset_features
from analysis.metrics import run_metrics_pipeline
from analysis.correlations import run_correlation_pipeline
from analysis.lme_model import run_lme_part3_lrt_and_output
from logging_config import setup_logging, initialize_quality_report

def verify_environment():
    """Verify that required environment variables and directories exist."""
    load_dotenv()
    
    required_dirs = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "results",
        PROJECT_ROOT / "state"
    ]
    
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Verify config exists
    config_path = PROJECT_ROOT / "code" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    return True

def run_pipeline():
    """Execute the full analysis pipeline."""
    logger = logging.getLogger(__name__)
    config = load_config(PROJECT_ROOT / "code" / "config.yaml")
    
    # Initialize quality report
    initialize_quality_report(PROJECT_ROOT / "results" / "quality_report.csv")
    
    try:
        # Step 1: Load raw data
        logger.info("Step 1: Loading raw data...")
        run_loading_pipeline(config)
        
        # Step 2: Preprocess data (filter blinks, low-pass)
        logger.info("Step 2: Preprocessing data...")
        run_preprocessing_pipeline(config)
        
        # Step 3: Extract features (metadata + salience)
        logger.info("Step 3: Extracting features...")
        process_dataset_features(config)
        
        # Step 4: Compute pupil metrics
        logger.info("Step 4: Computing pupil metrics...")
        run_metrics_pipeline(config)
        
        # Step 5: Run correlation analysis
        logger.info("Step 5: Running correlation analysis...")
        run_correlation_pipeline(config)
        
        # Step 6: Fit LME model and perform LRT
        logger.info("Step 6: Fitting LME model...")
        run_lme_part3_lrt_and_output(config)
        
        logger.info("Pipeline completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        raise

def main():
    """Entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Pupil Dilation Cognitive Load Pipeline")
    parser.add_argument("--config", type=str, default="code/config.yaml", 
                      help="Path to configuration file")
    parser.add_argument("--verbose", "-v", action="store_true", 
                      help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Pupil Dilation Cognitive Load Pipeline")
    
    try:
        verify_environment()
        run_pipeline()
        logger.info("Pipeline execution completed successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()