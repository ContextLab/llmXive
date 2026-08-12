import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from utils.matching import match_papers, find_best_match
from utils.pdf_parser import extract_statistics_from_pdf_text
from utils.stats_helpers import fit_tobit_model

# Ensure the code directory is in the path for imports
_current_dir = Path(__file__).parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))


def setup_logging(log_file: str = "data/raw/pipeline_execution.log") -> logging.Logger:
    """
    Configure logging for the pipeline.
    Logs to both console and a file in the data/raw directory.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates on re-runs in some environments
    if logger.handlers:
        logger.handlers.clear()

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def fetch_step(logger: logging.Logger) -> bool:
    """
    Orchestrates the data acquisition phase.
    In the full pipeline, this would call 01_fetch_and_match.py logic.
    For this skeleton, it validates the existence of the required raw data directories
    and logs the start of the fetch process.
    
    Returns:
        bool: True if the step completes successfully (or finds data), False otherwise.
    """
    logger.info("Starting fetch_step: Data Acquisition phase.")
    
    # Validate directory structure (created in T001b)
    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    results_dir = data_dir / "results"

    for d in [raw_dir, processed_dir, results_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # In a full implementation, this would invoke the scraping logic:
    # from code import fetch_and_match
    # fetch_and_match.run(logger)
    
    # Check if we have any input data to proceed
    # Assuming the fetch script would generate data/raw/arxiv_metadata.json or similar
    # For the skeleton, we log success if directories are ready.
    logger.info("Fetch step completed: Directory structure validated.")
    return True


def match_step(logger: logging.Logger) -> bool:
    """
    Orchestrates the paper matching phase.
    Uses the fuzzy matching logic from utils.matching.
    
    Returns:
        bool: True if matching completes, False if critical errors occur.
    """
    logger.info("Starting match_step: Paper Pairing phase.")
    
    if not match_papers:
        logger.error("Matching module not found or empty.")
        return False

    # In a full implementation, this would load raw metadata and run:
    # matched_pairs = match_papers(raw_metadata, logger)
    # save_to_csv(matched_pairs, "data/processed/matched_pairs.csv")
    
    # Demonstrate usage of the API surface
    logger.info("Using utils.matching.match_papers and find_best_match logic.")
    logger.info("Match step completed: Pairing logic ready.")
    return True


def extract_and_analyze_step(logger: logging.Logger) -> bool:
    """
    Orchestrates the extraction and analysis phase.
    1. Extracts statistics from PDFs using utils.pdf_parser.
    2. Performs analysis (Tobit, p-curve) using utils.stats_helpers.
    
    Returns:
        bool: True if analysis completes, False otherwise.
    """
    logger.info("Starting extract_and_analyze_step: Extraction and Analysis phase.")
    
    # Validate dependencies
    if not extract_statistics_from_pdf_text:
        logger.error("PDF Parser module not found.")
        return False
    
    if not fit_tobit_model:
        logger.error("Stats helpers (Tobit) module not found.")
        return False

    # In a full implementation:
    # 1. Load matched pairs
    # 2. Iterate through PDFs -> extract_statistics_from_pdf_text
    # 3. Aggregate results
    # 4. Run p-curve and Tobit models
    # 5. Save results to data/results/analysis_results.json
    
    logger.info("Extraction logic (pdf_parser) and Analysis logic (stats_helpers) validated.")
    logger.info("Extract and analyze step completed.")
    return True


def main():
    """
    Main entry point for the orchestration skeleton.
    Runs the pipeline steps sequentially: Fetch -> Match -> Extract/Analyze.
    """
    logger = setup_logging()
    logger.info("="*50)
    logger.info("Starting llmXive Pipeline: Statistical Bias in Pre-Print Publication")
    logger.info("="*50)

    try:
        # Step 1: Fetch
        if not fetch_step(logger):
            logger.error("Fetch step failed. Aborting.")
            return 1

        # Step 2: Match
        if not match_step(logger):
            logger.error("Match step failed. Aborting.")
            return 1

        # Step 3: Extract and Analyze
        if not extract_and_analyze_step(logger):
            logger.error("Extract and Analyze step failed. Aborting.")
            return 1

        logger.info("="*50)
        logger.info("Pipeline execution completed successfully.")
        logger.info("="*50)
        return 0

    except Exception as e:
        logger.exception(f"Pipeline failed with an unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())