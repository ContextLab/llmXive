"""
Main entry point for the molecular properties prediction pipeline.
Orchestrates the full workflow: data fetching, confound analysis,
descriptor generation (semi-empirical and DFT), model training, and evaluation.
"""
import argparse
import logging
import sys
from pathlib import Path

# Import main functions from existing modules
from fetch_data import main as fetch_data_main
from confound_analysis import main as confound_analysis_main
from generate_descriptors import main as generate_descriptors_main
from dft_calculator import main as dft_calculator_main
from train_models import main as train_models_main
from evaluate_models import main as evaluate_models_main
from utils.logging_utils import setup_logger

def setup_logging():
    """Configure logging for the pipeline."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "pipeline_execution.log"
    
    logger = setup_logger("pipeline", log_file)
    logger.info("Starting molecular properties prediction pipeline")
    return logger

def run_pipeline():
    """Execute the full pipeline end-to-end."""
    logger = setup_logging()
    
    try:
        # Step 1: Fetch and verify data
        logger.info("Step 1: Fetching and verifying data")
        fetch_data_main()
        
        # Step 2: Analyze confounds
        logger.info("Step 2: Analyzing molecular confounds")
        confound_analysis_main()
        
        # Step 3: Generate semi-empirical descriptors
        logger.info("Step 3: Generating semi-empirical descriptors (DFTB+)")
        generate_descriptors_main()
        
        # Step 4: Generate DFT descriptors for subset
        logger.info("Step 4: Generating DFT descriptors (Psi4) for subset")
        dft_calculator_main()
        
        # Step 5: Train models
        logger.info("Step 5: Training Random Forest models")
        train_models_main()
        
        # Step 6: Evaluate models
        logger.info("Step 6: Evaluating models and running paired t-test")
        evaluate_models_main()
        
        logger.info("Pipeline completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        return 1

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Molecular Properties Prediction Pipeline"
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip data fetching step"
    )
    parser.add_argument(
        "--skip-confounds",
        action="store_true",
        help="Skip confound analysis step"
    )
    parser.add_argument(
        "--skip-semi",
        action="store_true",
        help="Skip semi-empirical descriptor generation"
    )
    parser.add_argument(
        "--skip-dft",
        action="store_true",
        help="Skip DFT descriptor generation"
    )
    parser.add_argument(
        "--skip-train",
        action="store_true",
        help="Skip model training"
    )
    parser.add_argument(
        "--skip-eval",
        action="store_true",
        help="Skip model evaluation"
    )
    
    args = parser.parse_args()
    logger = setup_logging()
    
    try:
        if not args.skip_fetch:
            logger.info("Step 1: Fetching and verifying data")
            fetch_data_main()
        else:
            logger.info("Step 1: Skipping data fetching")
        
        if not args.skip_confounds:
            logger.info("Step 2: Analyzing molecular confounds")
            confound_analysis_main()
        else:
            logger.info("Step 2: Skipping confound analysis")
        
        if not args.skip_semi:
            logger.info("Step 3: Generating semi-empirical descriptors (DFTB+)")
            generate_descriptors_main()
        else:
            logger.info("Step 3: Skipping semi-empirical descriptor generation")
        
        if not args.skip_dft:
            logger.info("Step 4: Generating DFT descriptors (Psi4) for subset")
            dft_calculator_main()
        else:
            logger.info("Step 4: Skipping DFT descriptor generation")
        
        if not args.skip_train:
            logger.info("Step 5: Training Random Forest models")
            train_models_main()
        else:
            logger.info("Step 5: Skipping model training")
        
        if not args.skip_eval:
            logger.info("Step 6: Evaluating models and running paired t-test")
            evaluate_models_main()
        else:
            logger.info("Step 6: Skipping model evaluation")
        
        logger.info("Pipeline completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
