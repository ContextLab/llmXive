import os
import sys
import json
import logging
import argparse

from sampling import run_sampling_pipeline
from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for run_sampling script."""
    parser = argparse.ArgumentParser(description="Run sampling pipeline")
    parser.add_argument("--size", type=int, default=100, help="Sample size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    # If no output specified, use default from config
    output_file = args.output
    if not output_file:
        config = get_config()
        output_file = os.path.join(config.data_dir, 'results', 'consensus_sample.json')
    
    run_sampling_pipeline(args.size, output_file, args.seed)
    logger.info(f"Sampling complete. Output: {output_file}")

if __name__ == "__main__":
    main()
