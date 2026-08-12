import os
import sys
import argparse
from pathlib import Path

from config import load_paths
from utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

def main() -> None:
    """
    Main entry point for the pipeline.
    """
    parser = argparse.ArgumentParser(description="Materials Science Pipeline")
    parser.add_argument("--stage", type=str, choices=['ingest', 'descriptors', 'train', 'evaluate', 'importance', 'plots'],
                        help="Pipeline stage to run")
    args = parser.parse_args()

    setup_logging()
    logger.info(f"Running stage: {args.stage}")

    paths = load_paths()
    logger.info(f"Data directory: {paths['raw_data']}")

    if args.stage == 'ingest':
        from ingest import main as ingest_main
        ingest_main()
    elif args.stage == 'descriptors':
        from descriptors import main as descriptors_main
        descriptors_main()
    elif args.stage == 'train':
        from train import main as train_main
        train_main()
    elif args.stage == 'evaluate':
        from evaluate import main as evaluate_main
        evaluate_main()
    elif args.stage == 'importance':
        from importance import main as importance_main
        importance_main()
    elif args.stage == 'plots':
        from plots import main as plots_main
        plots_main()
    else:
        logger.error("Unknown stage.")
        sys.exit(1)

if __name__ == "__main__":
    main()