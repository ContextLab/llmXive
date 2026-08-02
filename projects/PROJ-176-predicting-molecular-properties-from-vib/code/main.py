import argparse
import sys
import logging
import os
from pathlib import Path

# Import existing command functions from sibling modules
from data.download import main as download_main
from data.preprocess import main as preprocess_main
from models.trainer import main as train_main
from evaluation.evaluate import main as evaluate_main
from evaluation.validate import main as validate_main
from utils.update_state import update_task_state
from utils.timeout_wrapper import enforce_timeout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def cmd_download(args):
    """Execute the data download and alignment step."""
    logger.info("Starting data download and alignment...")
    try:
        download_main()
        logger.info("Data download and alignment completed successfully.")
    except Exception as e:
        logger.error(f"Data download failed: {e}")
        raise

def cmd_preprocess(args):
    """Execute the data preprocessing step."""
    logger.info("Starting data preprocessing...")
    try:
        preprocess_main()
        logger.info("Data preprocessing completed successfully.")
    except Exception as e:
        logger.error(f"Data preprocessing failed: {e}")
        raise

def cmd_train(args):
    """Execute the model training step."""
    logger.info("Starting model training...")
    try:
        train_main()
        logger.info("Model training completed successfully.")
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise

def cmd_evaluate(args):
    """Execute the model evaluation step."""
    logger.info("Starting model evaluation...")
    try:
        evaluate_main()
        logger.info("Model evaluation completed successfully.")
    except Exception as e:
        logger.error(f"Model evaluation failed: {e}")
        raise

def cmd_validate(args):
    """Execute the independent validation step (T040)."""
    logger.info("Starting independent validation...")
    try:
        # Enforce timeout if specified (default 300s for this stage)
        timeout = args.timeout if hasattr(args, 'timeout') and args.timeout else 300
        
        def run_validation():
            validate_main()
            logger.info("Independent validation completed successfully.")
            # Update state for task T040
            update_task_state("T040", status="completed", artifact_path="results/validation_results.json")
        
        try:
            enforce_timeout(run_validation, timeout_seconds=timeout)
        except TimeoutError as te:
            logger.error(f"Validation timed out after {timeout} seconds: {te}")
            update_task_state("T040", status="failed", reason="timeout")
            raise
        
    except Exception as e:
        logger.error(f"Independent validation failed: {e}")
        update_task_state("T040", status="failed", reason=str(e))
        raise

def main():
    """Main CLI entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Molecular Properties Prediction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Download command
    parser_download = subparsers.add_parser('download', help='Download and align datasets')
    parser_download.set_defaults(func=cmd_download)
    parser_download.add_argument('--timeout', type=int, default=600, help='Timeout in seconds')

    # Preprocess command
    parser_preprocess = subparsers.add_parser('preprocess', help='Preprocess aligned data')
    parser_preprocess.set_defaults(func=cmd_preprocess)
    parser_preprocess.add_argument('--timeout', type=int, default=600, help='Timeout in seconds')

    # Train command
    parser_train = subparsers.add_parser('train', help='Train the CNN model')
    parser_train.set_defaults(func=cmd_train)
    parser_train.add_argument('--timeout', type=int, default=1800, help='Timeout in seconds')

    # Evaluate command
    parser_evaluate = subparsers.add_parser('evaluate', help='Evaluate model on test set')
    parser_evaluate.set_defaults(func=cmd_evaluate)
    parser_evaluate.add_argument('--timeout', type=int, default=600, help='Timeout in seconds')

    # Validate command (T040)
    parser_validate = subparsers.add_parser('validate', help='Independent validation on external data')
    parser_validate.set_defaults(func=cmd_validate)
    parser_validate.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')
    parser_validate.add_argument('--external-data', type=str, default=None, help='Path to external validation data')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user.")
        sys.exit(130)
    except Exception as e:
        logger.critical(f"Pipeline failed with error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()