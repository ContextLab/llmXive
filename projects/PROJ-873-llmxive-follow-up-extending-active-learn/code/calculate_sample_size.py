import os
import sys
import json
import logging
import argparse
from pathlib import Path

from config import get_config

logger = logging.getLogger(__name__)

def calculate_dynamic_sample_size(flagged_count: int, minimum_threshold: int = 10, percentage: float = 0.05) -> int:
    """Calculate dynamic sample size based on flagged count."""
    sample_size = max(minimum_threshold, int(flagged_count * percentage))
    return sample_size

def main():
    parser = argparse.ArgumentParser(description="Calculate dynamic sample size")
    parser.add_argument("--flagged-count", type=int, required=True, help="Number of flagged pairs")
    parser.add_argument("--minimum-threshold", type=int, default=10, help="Minimum threshold")
    parser.add_argument("--percentage", type=float, default=0.05, help="Percentage of flagged count")
    parser.add_argument("--output", type=str, default="data/results/sample_config.json", help="Output file path")

    args = parser.parse_args()

    config = get_config()
    sample_size = calculate_dynamic_sample_size(args.flagged_count, args.minimum_threshold, args.percentage)

    sample_config = {
        "sample_size": sample_size,
        "minimum_threshold": args.minimum_threshold,
        "percentage": args.percentage,
        "skip_validation": sample_size == 0
    }

    output_path = os.path.join(config.data_dir, args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(sample_config, f)

    logger.info(f"Sample size calculated: {sample_size}")

if __name__ == "__main__":
    main()