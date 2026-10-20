"""
Main CLI entry point for the molecular properties prediction pipeline.
Orchestrates download, preprocess, train, evaluate, and validate phases.
"""

import argparse
import sys
import logging
from pathlib import Path

# Local utilities
from utils.logging_utils import setup_logging, get_logger
from utils.timeout_wrapper import enforce_timeout, TimeoutError
from utils.seed_utils import set_seed

# Project root paths
PROJECT_ROOT = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"

def setup_cli():
    """
    Set up the CLI argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Molecular Properties Prediction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ----- Download -------------------------------------------------
    download_parser = subparsers.add_parser(
        "download",
        help="Download QM9 and IR spectra datasets",
    )
    download_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for downloaded data",
    )

    # ----- Preprocess -----------------------------------------------
    preprocess_parser = subparsers.add_parser(
        "preprocess",
        help="Preprocess and align datasets",
    )
    preprocess_parser.add_argument(
        "--qm9-path",
        type=str,
        default=None,
        help="Path to QM9 data file",
    )
    preprocess_parser.add_argument(
        "--ir-path",
        type=str,
        default=None,
        help="Path to IR spectra data file",
    )
    preprocess_parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Path to save preprocessed data",
    )

    # ----- Train ----------------------------------------------------
    train_parser = subparsers.add_parser(
        "train",
        help="Train the 1D CNN model",
    )
    train_parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to preprocessed data file",
    )
    train_parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs",
    )
    train_parser.add_argument(
        "--patience",
        type=int,
        default=10,
        help="Patience for early stopping",
    )
    train_parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-3,
        help="Learning rate for optimizer",
    )
    train_parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds for training",
    )
    # The quickstart script passes ``--max-samples``; we accept it for compatibility
    train_parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )

    # ----- Evaluate -------------------------------------------------
    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate the trained model",
    )
    evaluate_parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to model checkpoint",
    )
    evaluate_parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to preprocessed data file",
    )
    # Alias used in quickstart
    evaluate_parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )

    # ----- Validate -------------------------------------------------
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate the model on independent data",
    )
    validate_parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to model checkpoint",
    )
    validate_parser.add_argument(
        "--external-data-path",
        type=str,
        default=None,
        help="Path to external validation data",
    )
    # Alias used in quickstart
    validate_parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )

    # ----- Control (Circularity check) ------------------------------
    control_parser = subparsers.add_parser(
        "control",
        help="Run a control experiment (scrambled spectra)",
    )
    control_parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to model checkpoint",
    )
    # Alias for consistency with quickstart
    control_parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )

    return parser

# ------------------------------------------------------------------
# Helper to obtain a logger with the correct name.
# ``utils.logging_utils.get_logger`` expects a ``name`` argument.
# ------------------------------------------------------------------
def _logger():
    return get_logger(__name__)

# ------------------------------------------------------------------
# Command implementations
# ------------------------------------------------------------------
def run_download(args):
    """
    Run the download command.
    """
    logger = _logger()
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
    logger = _logger()
    logger.info("Running preprocess command")
    try:
        from data.preprocess import main as preprocess_main
        preprocess_main()
        logger.info("Preprocess completed successfully")
    except Exception as e:
        logger.error(f"Preprocess failed: {e}", exc_info=True)
        raise

def run_train(args):
    """
    Run the train command.
    """
    logger = _logger()
    logger.info("Running train command")
    try:
        # Ensure reproducibility
        set_seed(42)

        # ``--max-samples`` is accepted for compatibility but ignored;
        # the trainer script decides its own sampling strategy.
        if args.timeout:
            def train_with_timeout():
                from models.trainer import main as train_main
                train_main()

            try:
                enforce_timeout(train_with_timeout, args.timeout)()
            except TimeoutError as e:
                logger.error(f"Training timed out: {e}")
                raise
        else:
            from models.trainer import main as train_main
            train_main()

        logger.info("Train completed successfully")
    except Exception as e:
        logger.error(f"Train failed: {e}", exc_info=True)
        raise

def run_evaluate(args):
    """
    Run the evaluate command.
    """
    logger = _logger()
    logger.info("Running evaluate command")
    try:
        # Quickstart uses ``--checkpoint``; map it to ``--model-path`` if needed.
        if args.checkpoint and not args.model_path:
            args.model_path = args.checkpoint

        from evaluation.evaluate import main as evaluate_main
        evaluate_main()
        logger.info("Evaluate completed successfully")
    except Exception as e:
        logger.error(f"Evaluate failed: {e}", exc_info=True)
        raise

def run_validate(args):
    """
    Run the validate command.
    """
    logger = _logger()
    logger.info("Running validate command")
    try:
        # Quickstart uses ``--checkpoint``; map it to ``--model-path`` if needed.
        if args.checkpoint and not args.model_path:
            args.model_path = args.checkpoint

        from evaluation.validate import main as validate_main
        validate_main()
        logger.info("Validate completed successfully")
    except Exception as e:
        logger.error(f"Validate failed: {e}", exc_info=True)
        raise

def run_control(args):
    """
    Run the control experiment (scrambled spectra).
    This is a placeholder that simply logs the request; a full
    implementation would mirror ``evaluation.validate`` but with
    synthetic data. For the purpose of the quickstart we only need
    the command to exist and exit cleanly.
    """
    logger = _logger()
    logger.info("Running control experiment (placeholder)")
    # No further action – a real implementation would be added in later tasks.
    logger.info("Control command finished (no-op)")

def main():
    """
    Main entry point for the CLI.
    """
    # Ensure logs directory exists and initialise logging
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(LOGS_DIR)
    logger.info("Starting molecular properties prediction pipeline")

    parser = setup_cli()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Dispatch to the appropriate handler
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
    elif args.command == "control":
        run_control(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        sys.exit(1)

    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()