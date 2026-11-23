"""
Script to generate lineage_report.json and exclusions_log.json for T014.
This script depends on the raw data being available (from T037/T038).
It implements the logic for T014: Primary Dimension Identification.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Import the utility functions defined in primary_dimension_util
from primary_dimension_util import (
    process_dataframe_primary_dimensions,
    get_derivation_rule_hash
)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def parse_args():
    parser = argparse.ArgumentParser(description="Generate lineage report and exclusions log.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/z_reward.parquet",
        help="Path to the input parquet file (raw data)."
    )
    parser.add_argument(
        "--output-lineage",
        type=str,
        default="data/processed/lineage_report.json",
        help="Path to write the lineage report JSON."
    )
    parser.add_argument(
        "--output-exclusions",
        type=str,
        default="data/processed/exclusions_log.json",
        help="Path to write the exclusions log JSON."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    setup_logging()
    logger = logging.getLogger(__name__)

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Load data
    try:
        import pandas as pd
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} samples from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        sys.exit(1)

    # Process dimensions
    logger.info("Deriving primary dimensions...")
    filtered_df, lineage_report, exclusions_log = process_dataframe_primary_dimensions(df)

    # Save lineage report
    lineage_path = Path(args.output_lineage)
    lineage_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lineage_path, 'w') as f:
        json.dump(lineage_report, f, indent=2)
    logger.info(f"Wrote lineage report to {lineage_path} ({len(lineage_report)} entries)")

    # Save exclusions log
    exclusions_path = Path(args.output_exclusions)
    exclusions_path.parent.mkdir(parents=True, exist_ok=True)
    with open(exclusions_path, 'w') as f:
        json.dump(exclusions_log, f, indent=2)
    logger.info(f"Wrote exclusions log to {exclusions_path} ({len(exclusions_log)} entries)")

    logger.info(f"Original count: {len(df)}, Filtered count: {len(filtered_df)}")
    logger.info("T014 Primary Dimension Identification complete.")

if __name__ == "__main__":
    main()
