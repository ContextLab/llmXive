"""
T016: Summary Output

Prints sample counts, missing-data flags, and per-dimension coverage statistics
after ingestion. Reads from data/processed/raw_data.parquet (produced by T012).
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Import shared utilities if needed, or define local ones
# Using standard logging setup
def setup_logging(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("llmxive.summary")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(handler)
    return logger

def setup_directories(base_path: Path) -> dict:
    """Ensure required directories exist."""
    dirs = {
        "data_raw": base_path / "data" / "raw",
        "data_processed": base_path / "data" / "processed",
        "results": base_path / "results",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def load_raw_data(path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load the processed raw data from parquet."""
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")
    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded {len(df)} samples from {path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise

def calculate_summary_stats(df: pd.DataFrame, logger: logging.Logger) -> dict:
    """Calculate and return summary statistics."""
    total_samples = len(df)
    
    # Check for missing student_scalar
    missing_student_scalar = df["student_scalar"].isna().sum()
    missing_student_scalar_flag = "missing_student_scalar" in df.columns and \
                                  (df["excluded_reason"] == "missing_student_scalar").sum() if "excluded_reason" in df.columns else 0
    
    # Check for missing human annotations
    # Assuming human_annotations is a dict or list column, or separate columns
    # Based on T037 spec, human_annotations are generated. 
    # We check if the column exists and has nulls or empty dicts/lists.
    missing_human_annotations = 0
    if "human_annotations" in df.columns:
        # Count rows where human_annotations is NaN or empty
        missing_human_annotations = df["human_annotations"].isna().sum()
        if df["human_annotations"].apply(lambda x: isinstance(x, dict) and len(x) == 0).sum() > 0:
             missing_human_annotations += df["human_annotations"].apply(lambda x: isinstance(x, dict) and len(x) == 0).sum()
    
    # Per-dimension coverage
    # Teacher scores are expected to be in a column 'teacher_scores' as a list/dict of 4 dimensions
    # Or separate columns. The spec mentions 4 rubric dimensions.
    # Let's assume 'teacher_scores' is a list of 4 floats or a dict with keys 0-3.
    # We need to check coverage for each of the 4 dimensions.
    
    dimension_coverage = {}
    rubric_cols = [f"rubric_{i}" for i in range(4)] # Hypothesized column names if flattened
    # If teacher_scores is a single column containing lists/dicts:
    if "teacher_scores" in df.columns:
        dim_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        total_valid = 0
        for idx, row in df.iterrows():
            scores = row["teacher_scores"]
            valid_count = 0
            if isinstance(scores, list):
                for i, val in enumerate(scores):
                    if pd.notna(val):
                        dim_counts[i] += 1
                        valid_count += 1
            elif isinstance(scores, dict):
                for i in range(4):
                    val = scores.get(i)
                    if val is not None and pd.notna(val):
                        dim_counts[i] += 1
                        valid_count += 1
            if valid_count == 4:
                total_valid += 1
        
        dimension_coverage = {
            f"dimension_{i}": {
                "count": count,
                "coverage_rate": count / total_samples if total_samples > 0 else 0.0
            }
            for i, count in dim_counts.items()
        }
        dimension_coverage["full_coverage_count"] = total_valid
    else:
        # Fallback if columns are flattened
        for i in range(4):
            col = f"rubric_{i}"
            if col in df.columns:
                count = df[col].notna().sum()
                dimension_coverage[f"dimension_{i}"] = {
                    "count": count,
                    "coverage_rate": count / total_samples if total_samples > 0 else 0.0
                }
            else:
                dimension_coverage[f"dimension_{i}"] = {"count": 0, "coverage_rate": 0.0}

    summary = {
        "total_samples": total_samples,
        "missing_student_scalar_count": int(missing_student_scalar),
        "missing_human_annotations_count": int(missing_human_annotations),
        "dimension_coverage": dimension_coverage
    }
    return summary

def print_summary(summary: dict, logger: logging.Logger) -> None:
    """Print the summary to stdout."""
    logger.info("--- SUMMARY OUTPUT ---")
    logger.info(f"Total Samples: {summary['total_samples']}")
    logger.info(f"Missing Student Scalar Count: {summary['missing_student_scalar_count']}")
    logger.info(f"Missing Human Annotations Count: {summary['missing_human_annotations_count']}")
    logger.info("Per-Dimension Coverage:")
    for dim, stats in summary['dimension_coverage'].items():
        if isinstance(stats, dict):
            logger.info(f"  {dim}: Count={stats.get('count', 0)}, Rate={stats.get('coverage_rate', 0.0):.4f}")
        else:
            logger.info(f"  {dim}: {stats}")
    logger.info("----------------------")

def parse_args():
    parser = argparse.ArgumentParser(description="T016: Summary Output")
    parser.add_argument(
        "--input-path",
        type=str,
        default="data/processed/raw_data.parquet",
        help="Path to the raw data parquet file."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging(args.verbose)
    
    # Determine base path (assume current working directory is project root)
    base_path = Path.cwd()
    input_path = base_path / args.input_path
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    df = load_raw_data(input_path, logger)
    summary = calculate_summary_stats(df, logger)
    print_summary(summary, logger)

if __name__ == "__main__":
    main()