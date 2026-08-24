import argparse
import sys
import logging
import os
from pathlib import Path

from utils.logging_utils import setup_logging, get_logger

logger = get_logger(__name__)

def cmd_download(args):
    """Execute the download and alignment pipeline."""
    logger.info("Starting download command...")
    from data.download import main as download_main
    download_main()
    logger.info("Download command finished.")

def cmd_preprocess(args):
    """Execute the preprocessing pipeline."""
    logger.info("Starting preprocessing command...")
    from data.preprocess import main as preprocess_main
    preprocess_main()
    logger.info("Preprocessing command finished.")

def cmd_train(args):
    """Execute the training pipeline."""
    logger.info("Starting training command...")
    from models.trainer import main as train_main
    train_main()
    logger.info("Training command finished.")

def cmd_evaluate(args):
    """Execute the evaluation pipeline."""
    logger.info("Starting evaluation command...")
    from evaluation.evaluate import main as eval_main
    eval_main()
    logger.info("Evaluation command finished.")

def cmd_validate(args):
    """Execute the validation pipeline."""
    logger.info("Starting validation command...")
    from evaluation.validate import main as val_main
    val_main()
    logger.info("Validation command finished.")

def main():
    parser = argparse.ArgumentParser(description="Molecular Properties Prediction Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Download
    parser_download = subparsers.add_parser('download', help='Download and align data')
    parser_download.set_defaults(func=cmd_download)

    # Preprocess
    parser_preprocess = subparsers.add_parser('preprocess', help='Preprocess data')
    parser_preprocess.set_defaults(func=cmd_preprocess)

    # Train
    parser_train = subparsers.add_parser('train', help='Train model')
    parser_train.set_defaults(func=cmd_train)

    # Evaluate
    parser_evaluate = subparsers.add_parser('evaluate', help='Evaluate model')
    parser_evaluate.set_defaults(func=cmd_evaluate)

    # Validate
    parser_validate = subparsers.add_parser('validate', help='Validate model')
    parser_validate.set_defaults(func=cmd_validate)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Setup global logging
    log_path = Path("logs/pipeline.log")
    setup_logging(log_file=log_path, level=logging.INFO)

    args.func(args)

if __name__ == "__main__":
    main()
