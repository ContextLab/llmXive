import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Ensure code/ is in path for imports if run from root
if "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sampling import run_sampling_pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for T013c execution.
    Executes the sampling pipeline to generate consensus_sample.json.
    """
    parser = argparse.ArgumentParser(description="Execute T013c: Sampling for Consensus Validation")
    parser.add_argument("--log", default="data/processed/comparison_log.json", help="Path to comparison log")
    parser.add_argument("--config", default="data/results/sample_config.json", help="Path to sample config")
    parser.add_argument("--output", default="data/results/consensus_sample.json", help="Output path for sample indices")
    parser.add_argument("--threshold", type=float, default=0.95, help="Similarity threshold for filtering")
    
    args = parser.parse_args()
    
    logger.info("Starting T013c: Sampling for Consensus Validation")
    
    try:
        result = run_sampling_pipeline(
            log_path=args.log,
            config_path=args.config,
            output_path=args.output,
            threshold=args.threshold
        )
        logger.info(f"T013c completed successfully. Result: {result}")
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during sampling: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
