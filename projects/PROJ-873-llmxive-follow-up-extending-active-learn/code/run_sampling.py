import os
import sys
import json
import logging
import argparse
from sampling import run_sampling_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the sampling pipeline."""
    parser = argparse.ArgumentParser(description="Run sampling pipeline for consensus validation")
    parser.add_argument("--logs", type=str, default="data/processed/comparison_logs.json",
                      help="Path to comparison logs")
    parser.add_argument("--config", type=str, default="data/results/sample_config.json",
                      help="Path to sample configuration")
    parser.add_argument("--output", type=str, default="data/results/consensus_sample.json",
                      help="Path to output sample indices")
    args = parser.parse_args()

    if not os.path.exists(args.logs):
        logger.error(f"Comparison logs not found: {args.logs}")
        sys.exit(1)
    
    if not os.path.exists(args.config):
        logger.error(f"Sample config not found: {args.config}")
        sys.exit(1)

    try:
        run_sampling_pipeline(args.logs, args.config, args.output)
        logger.info(f"Sampling complete. Output written to {args.output}")
    except Exception as e:
        logger.error(f"Sampling failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
