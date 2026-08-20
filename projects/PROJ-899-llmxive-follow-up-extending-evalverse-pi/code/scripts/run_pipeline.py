import os
import sys
from pathlib import Path
import argparse
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.download import fetch_evalverse_dataset, main as download_main
from src.models.train import main as train_main
from src.models.evaluate import main as evaluate_main
from src.data.profiles import main as profile_main
from src.utils import setup_logging, get_logger

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run the llmXive pipeline")
    parser.add_argument("--stage", type=str, help="Specific stage to run: fetch, train, evaluate, profile, all")
    args = parser.parse_args()

    setup_logging(level=logging.INFO)

    stages = []
    if args.stage:
        if args.stage == "all":
            stages = ["fetch", "train", "evaluate", "profile"]
        else:
            stages = [args.stage]
    else:
        stages = ["fetch", "train", "evaluate", "profile"]

    try:
        if "fetch" in stages:
            logger.info("Stage: Fetching dataset...")
            download_main()

        if "train" in stages:
            logger.info("Stage: Training models...")
            train_main()

        if "evaluate" in stages:
            logger.info("Stage: Running evaluations...")
            evaluate_main()

        if "profile" in stages:
            logger.info("Stage: Profiling performance...")
            profile_main()

        logger.info("Pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()