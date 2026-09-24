import os
import sys
import logging
import argparse
from pathlib import Path

# Import project modules
from setup_structure import create_directories
from ingestion import main as ingestion_main
from descriptors import main as descriptors_main
from imbalance import main as imbalance_main
from training import main as training_main
from evaluation import main as evaluation_main
from resampling import main as resampling_main
from shap_analysis import main as shap_main
from correlation_analysis import main as correlation_main

def setup_logging():
    """Configure logging for the pipeline."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "pipeline.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def run_pipeline(args):
    """
    Main entry point for the pipeline.
    Orchestrates the full pipeline flow based on CLI arguments.
    """
    logger = setup_logging()
    logger.info("Starting pipeline execution...")

    # Ensure project structure exists
    logger.info("Initializing project structure...")
    create_directories()

    # Check MP availability if --include-mp is set
    if args.include_mp:
        logger.info("Materials Project inclusion requested. Checking availability...")
        try:
            from ingestion import detect_mp_availability
            if not detect_mp_availability():
                logger.warning("Materials Project API unavailable. Proceeding in fallback mode.")
                args.fallback_mode = True
        except Exception as e:
            logger.error(f"Error checking MP availability: {e}")
            args.fallback_mode = True

    # Execution flow
    if args.full_pipeline:
        try:
            # Step 1: Ingestion
            logger.info("Step 1: Data Ingestion...")
            ingestion_main(streaming=args.streaming, fallback_mode=args.fallback_mode)

            # Step 2: Descriptors
            logger.info("Step 2: Computing Descriptors...")
            descriptors_main()

            # Step 3: Imbalance Analysis
            logger.info("Step 3: Calculating Imbalance Scores...")
            imbalance_main()

            # Step 4: Resampling (if needed)
            logger.info("Step 4: Resampling Dataset...")
            resampling_main()

            # Step 5: Training
            logger.info("Step 5: Training Models...")
            training_main()

            # Step 6: Evaluation
            logger.info("Step 6: Evaluating Models...")
            evaluation_main()

            # Step 7: SHAP Analysis
            logger.info("Step 7: SHAP Analysis...")
            shap_main()

            # Step 8: Correlation Analysis
            logger.info("Step 8: Correlation Analysis...")
            correlation_main()

            logger.info("Full pipeline completed successfully.")
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise
    else:
        logger.info("No pipeline execution flag provided. Use --full-pipeline to run.")

    return 0

def main():
    parser = argparse.ArgumentParser(
        description="llmXive Automated Science Pipeline for Materials Property Predictions"
    )
    parser.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Execute the full pipeline: ingestion -> descriptors -> imbalance -> training -> evaluation -> SHAP"
    )
    parser.add_argument(
        "--include-mp",
        action="store_true",
        help="Include Materials Project data in ingestion (requires valid API key)"
    )
    parser.add_argument(
        "--fallback-mode",
        action="store_true",
        help="Force fallback mode (skip MP, use OQMD/AFLOW only) if MP is unavailable"
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Use streaming mode for dataset loading to reduce memory usage"
    )
    
    args = parser.parse_args()
    
    if args.fallback_mode and args.include_mp:
        logging.warning("Both --fallback-mode and --include-mp set. Fallback mode takes precedence.")
        args.include_mp = False

    return run_pipeline(args)

if __name__ == "__main__":
    sys.exit(main())
