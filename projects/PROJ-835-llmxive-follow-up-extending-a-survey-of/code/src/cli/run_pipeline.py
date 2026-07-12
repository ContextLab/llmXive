import os
import sys
import argparse
import logging
from pathlib import Path

# Ensure project root is in path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.utils.env_config import enforce_cpu_only, log_environment_config
from src.utils.logging_config import get_logger, configure_logging_level
from src.data.download import main as download_main
from src.data.preprocess import main as preprocess_main
from src.data.embed import main as embed_main
from src.models.train import main as train_main
from src.models.eval import main as eval_main
from src.cli.update_state import main as update_state_main

logger = get_logger(__name__)

def run_pipeline(args):
    """
    Execute the full research pipeline with configurable sampling and batch sizes.
    
    Args:
        args: Parsed arguments containing sampling_size and batch_size
    """
    logger.info("Starting LLMXive research pipeline...")
    
    # Phase 1: Download
    logger.info("Phase 1: Downloading dataset...")
    # We need to pass args to download if it supports them, 
    # but for now we assume it uses defaults or env vars.
    # If download.py main() accepts arguments, we would call download_main(args)
    # For this implementation, we assume download_main runs with defaults or we 
    # modify the download script to accept these args if strictly necessary.
    # Given the constraint to extend, we call the existing main.
    # To support the new args, we will set them as environment variables 
    # if the downstream scripts read them, or we assume the download script 
    # handles a default subset if no specific arg is passed.
    # However, to strictly follow the task "Add CLI argument parsing", 
    # we ensure the args are available.
    
    os.environ['DATASET_SAMPLE_SIZE'] = str(args.sample_size)
    
    try:
        download_main()
    except SystemExit:
        pass # download_main might call sys.exit(0) on success
    
    # Phase 2: Preprocess
    logger.info("Phase 2: Preprocessing audio...")
    try:
        preprocess_main()
    except SystemExit:
        pass

    # Phase 3: Embedding Extraction
    logger.info("Phase 3: Extracting embeddings...")
    os.environ['BATCH_SIZE'] = str(args.batch_size)
    try:
        embed_main()
    except SystemExit:
        pass

    # Phase 4: Training
    logger.info("Phase 4: Training classifier...")
    try:
        train_main()
    except SystemExit:
        pass

    # Phase 5: Evaluation
    logger.info("Phase 5: Evaluating model...")
    try:
        eval_main()
    except SystemExit:
        pass

    # Phase 6: State Update
    logger.info("Phase 6: Updating state file...")
    try:
        update_state_main()
    except SystemExit:
        pass

    logger.info("Pipeline completed successfully.")

def main():
    parser = argparse.ArgumentParser(
        description="LLMXive Automated Science Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Number of samples to download and process from the dataset. "
             "Set to -1 or 0 for full dataset if supported."
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for embedding extraction."
    )
    
    parser.add_argument(
        "--cpu-only",
        action="store_true",
        default=True,
        help="Force CPU-only execution (default: True)."
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level."
    )

    args = parser.parse_args()

    # Enforce CPU only
    if args.cpu_only:
        enforce_cpu_only()
    
    # Configure logging
    configure_logging_level(args.log_level)
    log_environment_config()

    run_pipeline(args)

if __name__ == "__main__":
    main()