"""
CLI entry point for model training and analysis pipeline.

Usage:
    python code/cli/model_cli.py
"""
import sys
import logging
import argparse
from pathlib import Path
from logging_config import setup_logging, get_logger
from config import get_config
from modeling import run_modeling_pipeline
from analysis import run_importance_analysis

def main():
    """Main entry point for model CLI."""
    parser = argparse.ArgumentParser(
        description='Run model training and analysis pipeline'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(level=args.log_level)
    config = get_config()
    
    logger.info("Starting model training and analysis pipeline")
    
    try:
        # Run modeling pipeline
        logger.info("Running modeling pipeline...")
        modeling_results = run_modeling_pipeline()
        logger.info("Modeling pipeline completed")
        
        # Run analysis pipeline
        logger.info("Running analysis pipeline...")
        analysis_results = run_importance_analysis()
        logger.info("Analysis pipeline completed")
        
        logger.info("Pipeline completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
