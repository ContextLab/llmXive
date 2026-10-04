"""
Main CLI entry point for the molecular properties prediction pipeline.
Orchestrates download, preprocess, train, evaluate, and validate phases.
"""
import argparse
import sys
import logging
import os
from pathlib import Path

# Import from local modules
from utils.logging_utils import setup_logging, get_logger
from utils.timeout_wrapper import enforce_timeout, TimeoutError
from utils.seed_utils import set_seed

# Configure paths
PROJECT_ROOT = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"

def setup_cli():
    """
    Set up the CLI argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Molecular Properties Prediction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download command
    download_parser = subparsers.add_parser(
        "download",
        help="Download QM9 and IR spectra datasets"
    )
    download_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for downloaded data"
    )

    # Preprocess command
    preprocess_parser = subparsers.add_parser(
        "preprocess",
        help="Preprocess and align datasets"
    )
    preprocess_parser.add_argument(
        "--qm9-path",
        type=str,
        default=None,
        help="Path to QM9 data file"
    )
    preprocess_parser.add_argument(
        "--ir-path",
        type=str,
        default=None,
        help="Path to IR spectra data file"
    )
    preprocess_parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Path to save preprocessed data"
    )

    # Train command
    train_parser = subparsers.add_parser(
        "train",
        help="Train the 1D CNN model"
    )
    train_parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to preprocessed data file"
    )
    train_parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs"
    )
    train_parser.add_argument(
        "--patience",
        type=int,
        default=10,
        help="Patience for early stopping"
    )
    train_parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-3,
        help="Learning rate for optimizer"
    )
    train_parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds for training"
    )

    # Evaluate command
    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate the trained model"
    )
    evaluate_parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to model checkpoint"
    )
    evaluate_parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to preprocessed data file"
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate the model on independent data"
    )
    validate_parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to model checkpoint"
    )
    validate_parser.add_argument(
        "--external-data-path",
        type=str,
        default=None,
        help="Path to external validation data"
    )

    return parser

def run_download(args):
    """
    Run the download command.
    """
    logger = get_logger()
    logger.info("Running download command")

    try:
        from data.download import main as download_main
        download_main()
        logger.info("Download completed successfully")
    except Exception as e:
        logger.error(f"Download failed: {str(e)}", exc_info=True)
        raise

def run_preprocess(args):
    """
    Run the preprocess command.
    """
    logger = get_logger()
    logger.info("Running preprocess command")

    try:
        from data.preprocess import main as preprocess_main
        preprocess_main()
        logger.info("Preprocess completed successfully")
    except Exception as e:
        logger.error(f"Preprocess failed: {str(e)}", exc_info=True)
        raise

def run_train(args):
    """
    Run the train command.
    """
    logger = get_logger()
    logger.info("Running train command")

    try:
        # Set seed for reproducibility
        set_seed(42)

        # Optionally enforce timeout
        if args.timeout:
            def train_with_timeout():
                from models.trainer import main as train_main
                train_main()

            try:
                enforce_timeout(train_with_timeout, args.timeout)()
            except TimeoutError as e:
                logger.error(f"Training timed out: {str(e)}")
                raise
        else:
            from models.trainer import main as train_main
            train_main()

        logger.info("Train completed successfully")
    except Exception as e:
        logger.error(f"Train failed: {str(e)}", exc_info=True)
        raise

def run_evaluate(args):
    """
    Run the evaluate command.
    """
    logger = get_logger()
    logger.info("Running evaluate command")

    try:
        from evaluation.evaluate import main as evaluate_main
        evaluate_main()
        logger.info("Evaluate completed successfully")
    except Exception as e:
        logger.error(f"Evaluate failed: {str(e)}", exc_info=True)
        raise

def run_validate(args):
    """
    Run the validate command.
    """
    logger = get_logger()
    logger.info("Running validate command")

    try:
        from evaluation.validate import main as validate_main
        validate_main()
        logger.info("Validate completed successfully")
    except Exception as e:
        logger.error(f"Validate failed: {str(e)}", exc_info=True)
        raise

def main():
    """
    Main entry point for the CLI.
    """
    # Set up logging
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(LOGS_DIR)
    logger.info("Starting molecular properties prediction pipeline")

    # Parse arguments
    parser = setup_cli()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Route to appropriate command
    if args.command == "download":
        run_download(args)
    elif args.command == "preprocess":
        run_preprocess(args)
    elif args.command == "train":
        run_train(args)
    elif args.command == "evaluate":
        run_evaluate(args)
    elif args.command == "validate":
        run_validate(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        sys.exit(1)

    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()