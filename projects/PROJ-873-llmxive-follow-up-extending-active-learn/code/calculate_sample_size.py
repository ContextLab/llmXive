"""
T013c: Calculate the dynamic sample size for LLM consensus validation.

Reads the count of flagged pairs from data/results/flagged_pairs_count.json,
applies the dynamic sampling logic (min threshold, percentage cap), and writes
the result to data/results/sample_config.json.
"""
import os
import sys
import json
import logging
import argparse

# Add project root to path to allow imports from sibling modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from metrics import calculate_dynamic_sample_size
from config import get_config

logger = logging.getLogger(__name__)

def main():
    """
    Entry point for T013c.
    Reads flagged_pairs_count.json, calculates sample size, writes sample_config.json.
    """
    parser = argparse.ArgumentParser(description="Calculate dynamic sample size for consensus validation.")
    parser.add_argument("--input", type=str, default="data/results/flagged_pairs_count.json",
                        help="Path to the input file containing flagged pair counts.")
    parser.add_argument("--output", type=str, default="data/results/sample_config.json",
                        help="Path to write the sample configuration.")
    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load input
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    with open(args.input, 'r') as f:
        input_data = json.load(f)

    total_flagged = input_data.get("total_flagged_count")
    if total_flagged is None:
        logger.error("Input file missing 'total_flagged_count'.")
        sys.exit(1)

    # Calculate sample size
    sample_size = calculate_dynamic_sample_size(total_flagged)

    # Get config for max_limit (if needed, though calculate_dynamic_sample_size handles logic)
    config = get_config()
    max_limit = getattr(config, 'max_sample_size', 1000) # Fallback if config doesn't have it

    result = {
        "total_flagged_count": total_flagged,
        "max_limit": max_limit,
        "sample_size": sample_size,
        "calculation_method": "dynamic_percentage_capped"
    }

    # Write output
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Sample size calculated: {sample_size} (from {total_flagged} flagged pairs).")
    logger.info(f"Result written to: {args.output}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
