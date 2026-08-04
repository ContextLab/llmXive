"""
Script to generate the synthetic test set for llmXive.
Executes the data generation pipeline with configurable parameters.
"""
import argparse
import logging
import sys

from code.data_generation import main as generation_main
from code.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic test set")
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--trial-count", type=int, default=50, help="Number of trials to generate"
    )
    parser.add_argument(
        "--config", type=str, default="code/config.yaml", help="Path to config file"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        config = load_config(args.config)
        config.experiment.seed = args.seed
        config.experiment.trial_count = args.trial_count

        logger.info(f"Starting test set generation with seed {args.seed}")
        logger.info(f"Target trial count: {args.trial_count}")

        generation_main(config_path=args.config)

        logger.info("Test set generation completed successfully")

    except Exception as e:
        logger.exception(f"Test set generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()