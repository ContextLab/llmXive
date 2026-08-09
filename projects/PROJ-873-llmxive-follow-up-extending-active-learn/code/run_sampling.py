import os
import sys
import json
import logging
import argparse
from pathlib import Path

from sampling import run_sampling_pipeline

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Execute T013c: Sampling for Consensus Validation")
    parser.add_argument(
        "--log-path",
        type=str,
        default=None,
        help="Path to comparison log (default: data/processed/comparison_log.json from config)"
    )
    parser.add_argument(
        "--config-path",
        type=str,
        default="data/results/sample_config.json",
        help="Path to sample config (default: data/results/sample_config.json)"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/results/consensus_sample.json",
        help="Path to output sample (default: data/results/consensus_sample.json)"
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        result = run_sampling_pipeline(
            log_path=args.log_path,
            config_path=args.config_path,
            output_path=args.output_path
        )
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Sampling pipeline failed: {e}")
        print(json.dumps({"status": "failed", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
