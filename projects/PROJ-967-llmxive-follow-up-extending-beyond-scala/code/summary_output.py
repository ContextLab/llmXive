"""
Task T016: Summary Output
After ingestion, print sample counts, missing-data flags, and per-dimension coverage statistics.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd

from alignment import load_raw_data, setup_logging, setup_directories


def parse_args():
    parser = argparse.ArgumentParser(description="Generate summary output after ingestion.")
    parser.add_argument(
        "--input-path",
        type=str,
        default="data/processed/raw_data.parquet",
        help="Path to the ingested raw data parquet file.",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/processed/summary_output.json",
        help="Path to write the summary output JSON file.",
    )
    return parser.parse_args()


def calculate_dimension_coverage(df: pd.DataFrame) -> dict:
    """Calculate coverage statistics for each of the 4 rubric dimensions."""
    coverage = {}
    for i in range(4):
        dim_col = f"human_annotations_{i}"
        if dim_col in df.columns:
            total = len(df)
            non_null = df[dim_col].notna().sum()
            coverage[str(i)] = {
                "total_samples": int(total),
                "non_null_count": int(non_null),
                "null_count": int(total - non_null),
                "coverage_percentage": float(non_null / total * 100) if total > 0 else 0.0,
            }
        else:
            coverage[str(i)] = {
                "total_samples": 0,
                "non_null_count": 0,
                "null_count": 0,
                "coverage_percentage": 0.0,
                "error": f"Column {dim_col} not found in dataset",
            }
    return coverage


def generate_summary(input_path: str, output_path: str, logger: logging.Logger) -> None:
    """Load data, compute summary stats, and write to JSON."""
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_parquet(input_path)

    total_samples = len(df)
    logger.info(f"Total samples loaded: {total_samples}")

    # Check for missing data flags
    missing_flags = {}
    required_cols = ["student_scalar", "human_annotations_0", "human_annotations_1", "human_annotations_2", "human_annotations_3"]
    for col in required_cols:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            missing_flags[col] = int(missing_count)
        else:
            missing_flags[col] = -1  # Column missing entirely

    # Check for excluded samples from alignment
    if "excluded_reason" in df.columns:
        excluded_count = df["excluded_reason"].notna().sum()
        missing_flags["excluded_reason"] = int(excluded_count)
    else:
        missing_flags["excluded_reason"] = 0

    # Per-dimension coverage
    dimension_coverage = calculate_dimension_coverage(df)

    summary = {
        "total_samples": int(total_samples),
        "missing_data_flags": missing_flags,
        "dimension_coverage": dimension_coverage,
        "generated_from": input_path,
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Writing summary to {output_path}")
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary to stdout as requested
    print(f"=== Summary Output ===")
    print(f"Total Samples: {summary['total_samples']}")
    print(f"Missing Data Flags: {json.dumps(summary['missing_data_flags'], indent=2)}")
    print(f"Dimension Coverage:")
    for dim, stats in summary['dimension_coverage'].items():
        print(f"  Dimension {dim}: {stats['coverage_percentage']:.2f}% coverage ({stats['non_null_count']}/{stats['total_samples']})")


def main():
    args = parse_args()
    setup_directories()
    logger = setup_logging("summary_output")

    try:
        generate_summary(args.input_path, args.output_path, logger)
        logger.info("Summary output generated successfully.")
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()