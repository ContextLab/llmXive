"""
Calculate dynamic sample size for LLM consensus validation.

This script reads the flagged pairs count from T013a's output and calculates
the sample size using the formula:
sample_size = max(minimum_threshold, int(0.05 * total_flagged_count))

It writes the result to data/results/sample_config.json.
"""
import os
import sys
import json
import logging
import argparse

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics import calculate_dynamic_sample_size
from config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description='Calculate dynamic sample size for LLM consensus validation.'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/results/flagged_pairs_count.json',
        help='Path to the flagged pairs count JSON file (default: data/results/flagged_pairs_count.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/results/sample_config.json',
        help='Path to write the sample config JSON file (default: data/results/sample_config.json)'
    )
    parser.add_argument(
        '--minimum-threshold',
        type=int,
        default=None,
        help='Minimum sample size threshold (overrides config if provided)'
    )
    parser.add_argument(
        '--percentage',
        type=float,
        default=0.05,
        help='Percentage of flagged count to use (default: 0.05 = 5%%)'
    )
    args = parser.parse_args()

    # Load flagged pairs count
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    with open(args.input, 'r') as f:
        flagged_data = json.load(f)

    total_flagged_count = flagged_data.get('total_flagged_count', 0)
    logger.info(f"Total flagged count: {total_flagged_count}")

    # Get minimum threshold from config or argument
    config = get_config()
    minimum_threshold = args.minimum_threshold
    if minimum_threshold is None:
        # Try to get from config, default to 10
        minimum_threshold = getattr(config, 'MINIMUM_SAMPLE_THRESHOLD', 10)

    logger.info(f"Using minimum threshold: {minimum_threshold}")
    logger.info(f"Using percentage: {args.percentage}")

    # Calculate sample size
    sample_size = calculate_dynamic_sample_size(
        total_flagged_count,
        minimum_threshold,
        percentage=args.percentage
    )

    logger.info(f"Calculated sample size: {sample_size}")

    # Prepare output
    sample_config = {
        "total_flagged_count": total_flagged_count,
        "minimum_threshold": minimum_threshold,
        "percentage": args.percentage,
        "sample_size": sample_size,
        "calculation_method": "dynamic_percentage_capped"
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    # Write output
    with open(args.output, 'w') as f:
        json.dump(sample_config, f, indent=2)

    logger.info(f"Sample config written to: {args.output}")
    print(f"Sample size: {sample_size}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
