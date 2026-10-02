"""
Main pipeline entry point for the drought tolerance prediction project.
Orchestrates the sequence of data download, generation, ingestion, modeling, and evaluation.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add code directory to path
code_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(code_dir))

from config import get_config, VALIDATION_MODE, ensure_directories, RANDOM_SEED
from data.download import main as download_main, fetch_ncbi_refseq
from data.generate import main as generate_main
from data.ingest import main as ingest_main
from data.split import main as split_main
from models.train import main as train_main
from models.evaluate import main as evaluate_main
from models.compare import main as compare_main
from utils.logging import DataPipelineLog

def setup_logging():
    """Configure basic logging."""
    log_dir = Path(get_config()["paths"]["logs"])
    ensure_directories([log_dir])
    log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("pipeline")

def run_pipeline(logger):
    """Execute the full pipeline."""
    config = get_config()
    logger.info(f"Starting pipeline in {'Validation' if VALIDATION_MODE else 'Production'} mode")
    logger.info(f"Random Seed: {RANDOM_SEED}")

    # Step 1: Download Data (T011a, T011b)
    logger.info("Step 1: Downloading data...")
    try:
        download_main()
    except Exception as e:
        if not VALIDATION_MODE:
            logger.error(f"Critical download failure: {e}")
            raise
        else:
            logger.warning(f"Download failed in validation mode: {e}. Proceeding to synthetic generation.")

    # Step 2: Generate Synthetic Data (T012) if needed
    logger.info("Step 2: Checking/Generating synthetic data...")
    generate_main()

    # Step 3: Ingest and Merge (T013, T014a)
    logger.info("Step 3: Ingesting and merging data...")
    ingest_main()

    # Step 4: Split Data (T015)
    logger.info("Step 4: Splitting data...")
    split_main()

    # Step 5: Train Models (T020, T021)
    logger.info("Step 5: Training models...")
    train_main()

    # Step 6: Evaluate Models (T022, T023)
    logger.info("Step 6: Evaluating models...")
    evaluate_main()

    # Step 7: Compare and Report (T027, T028, T029)
    logger.info("Step 7: Comparing models and generating report...")
    compare_main()

    logger.info("Pipeline completed successfully.")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Drought Tolerance Prediction Pipeline")
    parser.add_argument("--mode", type=str, default="production", choices=["production", "validation"],
                        help="Execution mode: 'production' (fail loudly) or 'validation' (allow synthetic fallback)")
    args = parser.parse_args()

    # Set validation mode
    global VALIDATION_MODE
    if args.mode == "validation":
        VALIDATION_MODE = True
    else:
        VALIDATION_MODE = False

    logger = setup_logging()
    
    try:
        run_pipeline(logger)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()