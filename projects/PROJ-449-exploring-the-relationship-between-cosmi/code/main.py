"""
Main entry point for the cosmic ray analysis pipeline.

This script orchestrates the various stages of the analysis pipeline:
- retrieve: Fetch and preprocess data
- ratios: Calculate composition ratios
- correlation: Perform lagged correlation analysis
- bootstrap: Run bootstrap resampling
- model: Fit diffusion models
- visualization: Generate plots
- all: Run all stages
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from code.utils.logging import setup_logger

# Initialize logger
logger = setup_logger(__name__)

def run_retrieve_stage():
    """Run the data retrieval and preprocessing stage."""
    logger.info("=== Running Retrieve Stage ===")
    try:
        from code.data.fetch_ams02 import main as fetch_ams02_main
        from code.data.fetch_noaa import main as fetch_noaa_main
        from code.data.align_data import main as align_data_main
        from code.data.preprocess import main as preprocess_main
        from code.data.validate_coverage import main as validate_coverage_main

        # Fetch AMS-02 data
        fetch_ams02_main()
        
        # Fetch NOAA sunspot data
        fetch_noaa_main()
        
        # Align and merge datasets
        align_data_main()
        
        # Calculate composition ratios
        preprocess_main()
        
        # Validate data coverage
        validate_coverage_main()
        
        logger.info("Retrieve stage completed successfully")
        return True
    except Exception as e:
        logger.error(f"Retrieve stage failed: {str(e)}")
        return False

def run_ratios_stage():
    """Run the composition ratios calculation stage."""
    logger.info("=== Running Ratios Stage ===")
    try:
        from code.data.preprocess import main as preprocess_main
        preprocess_main()
        logger.info("Ratios stage completed successfully")
        return True
    except Exception as e:
        logger.error(f"Ratios stage failed: {str(e)}")
        return False

def run_correlation_stage():
    """Run the correlation analysis stage."""
    logger.info("=== Running Correlation Stage ===")
    try:
        from code.analysis.correlation import main as correlation_main
        correlation_main()
        logger.info("Correlation stage completed successfully")
        return True
    except Exception as e:
        logger.error(f"Correlation stage failed: {str(e)}")
        return False

def run_bootstrap_stage():
    """Run the bootstrap resampling stage."""
    logger.info("=== Running Bootstrap Stage ===")
    try:
        from code.analysis.bootstrap import main as bootstrap_main
        bootstrap_main()
        logger.info("Bootstrap stage completed successfully")
        return True
    except Exception as e:
        logger.error(f"Bootstrap stage failed: {str(e)}")
        return False

def run_model_stage():
    """Run the model fitting stage."""
    logger.info("=== Running Model Stage ===")
    try:
        from code.analysis.model_fitting import main as model_fitting_main
        model_fitting_main()
        logger.info("Model stage completed successfully")
        return True
    except Exception as e:
        logger.error(f"Model stage failed: {str(e)}")
        return False

def run_visualization_stage():
    """Run the visualization stage."""
    logger.info("=== Running Visualization Stage ===")
    try:
        from code.analysis.visualization import main as visualization_main
        visualization_main()
        logger.info("Visualization stage completed successfully")
        return True
    except Exception as e:
        logger.error(f"Visualization stage failed: {str(e)}")
        return False

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Cosmic Ray Analysis Pipeline")
    parser.add_argument(
        '--stage',
        type=str,
        choices=['retrieve', 'ratios', 'correlation', 'bootstrap', 'model', 'visualization', 'all'],
        required=True,
        help='Pipeline stage to run'
    )
    
    args = parser.parse_args()
    
    success = False
    
    if args.stage == 'retrieve':
        success = run_retrieve_stage()
    elif args.stage == 'ratios':
        success = run_ratios_stage()
    elif args.stage == 'correlation':
        success = run_correlation_stage()
    elif args.stage == 'bootstrap':
        success = run_bootstrap_stage()
    elif args.stage == 'model':
        success = run_model_stage()
    elif args.stage == 'visualization':
        success = run_visualization_stage()
    elif args.stage == 'all':
        # Run all stages in order
        stages = [
            ('retrieve', run_retrieve_stage),
            ('ratios', run_ratios_stage),
            ('correlation', run_correlation_stage),
            ('bootstrap', run_bootstrap_stage),
            ('model', run_model_stage),
            ('visualization', run_visualization_stage)
        ]
        
        for stage_name, stage_func in stages:
            logger.info(f"Running {stage_name} stage...")
            if not stage_func():
                logger.error(f"Failed at {stage_name} stage")
                sys.exit(1)
        
        success = True
    
    if success:
        logger.info(f"Pipeline stage '{args.stage}' completed successfully")
        sys.exit(0)
    else:
        logger.error(f"Pipeline stage '{args.stage}' failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
