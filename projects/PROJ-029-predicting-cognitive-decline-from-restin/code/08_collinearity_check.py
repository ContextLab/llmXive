"""
T044: Collinearity Check Script
Reconciles run-book invocation with implementation.
Performs collinearity analysis on graph metrics and outputs a report.
"""
import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

from utils.logger import get_logger
from utils.stats import calculate_correlation_matrix, check_collinearity
from utils.io import load_csv, save_csv, ensure_dir
from config import get_config

logger = get_logger("collinearity_check")

def main():
    """Main entry point for T044."""
    logger.info("Starting T044: Collinearity Check")
    
    # Load configuration
    config = get_config()
    data_dir = Path(config["data"]["processed"])
    input_path = data_dir / "graph_metrics.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("This script requires 'data/processed/graph_metrics.csv' to be generated first by code/03_compute_graph_metrics.py.")
        # Exit with code 1 to indicate missing dependency
        sys.exit(1)
    
    # Load data
    try:
        df = load_csv(input_path)
        logger.info(f"Loaded {len(df)} records from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        sys.exit(1)
    
    # Ensure required columns exist
    # We expect at least subject_id and some numeric features
    if 'subject_id' not in df.columns:
        logger.error(f"Missing required column 'subject_id' in {input_path}")
        sys.exit(1)
    
    # Identify numeric feature columns (exclude subject_id)
    feature_cols = [col for col in df.columns if col != 'subject_id' and pd.api.types.is_numeric_dtype(df[col])]
    
    if len(feature_cols) < 2:
        logger.warning("Not enough features to check collinearity (need >= 2). Found: " + str(feature_cols))
        result = {
            "status": "skipped",
            "reason": "insufficient features",
            "input_file": str(input_path),
            "found_columns": list(df.columns)
        }
        output_path = data_dir / "collinearity_report.json"
        ensure_dir(output_path.parent)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(json.dumps(result))
        return 0
    
    # Calculate correlation matrix
    try:
        corr_matrix = calculate_correlation_matrix(df[feature_cols])
    except Exception as e:
        logger.error(f"Failed to calculate correlation matrix: {e}")
        sys.exit(1)
    
    # Find highly correlated pairs
    high_corr_pairs = []
    threshold = 0.95
    
    for i in range(len(feature_cols)):
        for j in range(i + 1, len(feature_cols)):
            corr_val = corr_matrix.iloc[i, j]
            if abs(corr_val) > threshold:
                high_corr_pairs.append({
                    "feature1": feature_cols[i],
                    "feature2": feature_cols[j],
                    "correlation": float(corr_val)
                })
    
    result = {
        "status": "success",
        "input_file": str(input_path),
        "total_features": len(feature_cols),
        "threshold": threshold,
        "highly_correlated_pairs": high_corr_pairs,
        "correlation_matrix_shape": list(corr_matrix.shape)
    }
    
    # Write output
    output_path = data_dir / "collinearity_report.json"
    ensure_dir(output_path.parent)
    try:
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Wrote collinearity report to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        sys.exit(1)
    
    print(json.dumps(result))
    return 0

if __name__ == "__main__":
    sys.exit(main())
