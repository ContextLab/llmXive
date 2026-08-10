"""
Main entry point for the llmXive Follow-up: Extending Improved LAR project.

This script orchestrates the full research pipeline:
1. Setup: Initialize project structure and configuration.
2. Data: Download, tokenize, validate, and split the Micro-Corpus.
3. Training: Run comparative training loops for AR and Diffusion models.
4. Analysis: Perform statistical analysis on overfitting trajectories.

Usage:
    python main.py [--stage <stage_name>] [--config <config_path>]
"""

import argparse
import sys
import time
from pathlib import Path

# Add project root to path to ensure local imports work
# This assumes the script is run from the project root or code directory
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.setup_data_dirs import setup_data_directories
from utils.logging import setup_logging, get_logger, info, error, warning
from utils.config import get_config, reset_config, get_project_root
from utils.monitor import get_resource_snapshot, get_ram_usage_gb

# Import data pipeline stages
# Note: These imports assume the modules exist as per task definitions
try:
    from data.download_micro_corpus import main as download_corpus
    from data.tokenize_and_filter import main as tokenize_corpus
    from data.validate_corpus import main as validate_corpus
    from data.split_data import main as split_data
except ImportError as e:
    # Graceful handling if modules are not yet implemented
    pass

# Import training pipeline stages
try:
    from training.run_experiment import main as run_training
except ImportError as e:
    pass

# Import analysis pipeline stages
try:
    from analysis.statistical_test import main as run_analysis
except ImportError as e:
    pass

def parse_args():
    parser = argparse.ArgumentParser(
        description="llmXive Research Pipeline: Extending Improved LAR"
    )
    parser.add_argument(
        "--stage",
        type=str,
        choices=["setup", "data", "train", "analyze", "all"],
        default="all",
        help="Which stage of the pipeline to run.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a custom configuration YAML file.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (debug level).",
    )
    return parser.parse_args()

def run_setup_stage():
    """Initialize project directories and configuration."""
    info("Starting Setup Stage...")
    try:
        # Ensure data directories exist
        setup_data_directories()
        info("Data directories initialized successfully.")

        # Load configuration
        if get_config() is None:
            reset_config() # Load default config if not set
        info("Configuration loaded.")
        return True
    except Exception as e:
        error(f"Setup stage failed: {e}")
        return False

def run_data_stage():
    """Execute data pipeline: download, tokenize, validate, split."""
    info("Starting Data Stage...")
    try:
        # 1. Download
        info("Step 1/4: Downloading Micro-Corpus...")
        download_corpus()

        # 2. Tokenize
        info("Step 2/4: Tokenizing and filtering...")
        tokenize_corpus()

        # 3. Validate
        info("Step 3/4: Validating corpus...")
        validate_corpus()

        # 4. Split
        info("Step 4/4: Splitting data...")
        split_data()

        info("Data stage completed successfully.")
        return True
    except Exception as e:
        error(f"Data stage failed: {e}")
        return False

def run_train_stage():
    """Execute training pipeline."""
    info("Starting Training Stage...")
    try:
        run_training()
        info("Training stage completed successfully.")
        return True
    except Exception as e:
        error(f"Training stage failed: {e}")
        return False

def run_analyze_stage():
    """Execute analysis pipeline."""
    info("Starting Analysis Stage...")
    try:
        run_analysis()
        info("Analysis stage completed successfully.")
        return True
    except Exception as e:
        error(f"Analysis stage failed: {e}")
        return False

def main():
    args = parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    log_dir = get_project_root() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_level=log_level, log_dir=log_dir)

    logger = get_logger(__name__)
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("llmXive Research Pipeline: Extending Improved LAR")
    logger.info("=" * 60)
    logger.info(f"Project Root: {get_project_root()}")
    logger.info(f"Selected Stage: {args.stage}")

    success = True

    if args.stage in ["setup", "all"]:
        if not run_setup_stage():
            success = False
            error("Aborting pipeline due to setup failure.")
            sys.exit(1)

    if success and args.stage in ["data", "all"]:
        if not run_data_stage():
            success = False
            error("Aborting pipeline due to data stage failure.")
            sys.exit(1)

    if success and args.stage in ["train", "all"]:
        if not run_train_stage():
            success = False
            error("Aborting pipeline due to training stage failure.")
            sys.exit(1)

    if success and args.stage in ["analyze", "all"]:
        if not run_analyze_stage():
            success = False
            error("Aborting pipeline due to analysis stage failure.")
            sys.exit(1)

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    if success:
        logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds.")
    else:
        logger.error("Pipeline failed.")
    logger.info("=" * 60)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())