import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
# This must be called before any os.getenv() calls
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def verify_environment() -> bool:
    """
    Verify that required environment variables are set.
    Returns True if all required variables are present, False otherwise.
    Exits with error message if any required variable is missing.
    """
    required_vars = ["DATA_PATH", "OPENNEURO_API_KEY", "LOG_LEVEL"]
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            logger.error(f"Missing required environment variable: {var}")
        else:
            logger.debug(f"Environment variable '{var}' is set.")

    if missing_vars:
        error_msg = f"ERROR: Missing required environment variables: {', '.join(missing_vars)}. " \
                    f"Please set them in the .env file or your shell environment."
        logger.error(error_msg)
        return False

    # Validate DATA_PATH exists if it's a directory path
    data_path = os.getenv("DATA_PATH")
    if data_path and not os.path.exists(data_path):
        logger.warning(f"DATA_PATH '{data_path}' does not exist. "
                       f"Ensure the directory is created or the path is correct.")

    return True

def run_pipeline():
    """
    Main pipeline execution function.
    Orchestrates the full research pipeline from data loading to analysis.
    """
    logger.info("Starting llmXive research pipeline...")

    # Verify environment before proceeding
    if not verify_environment():
        logger.error("Pipeline aborted due to missing environment configuration.")
        sys.exit(1)

    logger.info("Environment verified successfully.")

    # TODO: Import and run the actual pipeline stages
    # from preprocessing.preprocess import run_preprocessing_pipeline
    # from analysis.analysis import run_full_analysis_pipeline
    # ...

    logger.info("Pipeline execution completed.")

def main():
    parser = argparse.ArgumentParser(
        description="llmXive Automated Science Pipeline - Investigating Pupil Dilation and Cognitive Load"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "preprocess", "analysis"],
        default="full",
        help="Pipeline mode: full (all stages), preprocess only, or analysis only"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    logger.info(f"Running pipeline in '{args.mode}' mode")

    if args.mode == "full":
        run_pipeline()
    elif args.mode == "preprocess":
        logger.info("Preprocessing stage only - implementation pending")
    elif args.mode == "analysis":
        logger.info("Analysis stage only - implementation pending")

    logger.info("Pipeline run finished.")

if __name__ == "__main__":
    main()