import argparse
import sys
import logging
import os
from pathlib import Path
from utils.logging_utils import setup_logging, get_logger
from utils.timeout_wrapper import enforce_timeout
from utils.update_state import update_task_state
from data.download import main as download_main
from data.preprocess import main as preprocess_main
from models.trainer import main as train_main
from evaluation.evaluate import main as evaluate_main
from evaluation.validate import main as validate_main

def main():
    parser = argparse.ArgumentParser(
        description="llmXive Molecular Property Prediction Pipeline"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download
    download_parser = subparsers.add_parser("download", help="Download QM9 and IR spectra")
    download_parser.add_argument("--data-dir", type=str, default="data/raw", help="Directory to save raw data")

    # Preprocess
    preprocess_parser = subparsers.add_parser("preprocess", help="Preprocess and align data")
    preprocess_parser.add_argument("--input-dir", type=str, default="data/raw", help="Input raw data directory")
    preprocess_parser.add_argument("--output-dir", type=str, default="data/preprocessed", help="Output preprocessed data directory")

    # Train
    train_parser = subparsers.add_parser("train", help="Train the CNN model")
    train_parser.add_argument("--data-path", type=str, default="data/preprocessed/aligned_data.npz", help="Path to preprocessed data")
    train_parser.add_argument("--output-dir", type=str, default="models", help="Directory to save model checkpoints")
    train_parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    train_parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")

    # Evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate the trained model")
    eval_parser.add_argument("--model-path", type=str, default="models/model_best.pt", help="Path to model checkpoint")
    eval_parser.add_argument("--data-path", type=str, default="data/preprocessed/aligned_data.npz", help="Path to test data")
    eval_parser.add_argument("--output-dir", type=str, default="results", help="Directory to save evaluation results")

    # Validate
    validate_parser = subparsers.add_parser("validate", help="Validate on independent data")
    validate_parser.add_argument("--model-path", type=str, default="models/model_best.pt", help="Path to model checkpoint")
    validate_parser.add_argument("--external-data", type=str, default=None, help="Path to external validation data")
    validate_parser.add_argument("--output-dir", type=str, default="results", help="Directory to save validation results")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Setup logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger = setup_logging(level=logging.INFO)

    logger.info(f"Executing command: {args.command}")

    try:
        if args.command == "download":
            download_main(args.data_dir)
        elif args.command == "preprocess":
            preprocess_main(args.input_dir, args.output_dir)
        elif args.command == "train":
            # Wrap training in timeout
            def run_train():
                train_main(args.data_path, args.output_dir, args.epochs)
            enforce_timeout(run_train, timeout_seconds=args.timeout)
        elif args.command == "evaluate":
            evaluate_main(args.model_path, args.data_path, args.output_dir)
        elif args.command == "validate":
            validate_main(args.model_path, args.external_data, args.output_dir)
        
        # Update state on success
        update_task_state(args.command, "completed")
        
    except Exception as e:
        logger.error(f"Error executing {args.command}: {e}")
        update_task_state(args.command, "failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
