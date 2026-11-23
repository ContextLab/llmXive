"""
Compute Variance Inflation Factor (VIF) for descriptor columns.

This script calculates the VIF for each descriptor in the derived dataset
to identify multicollinearity before feature filtering or model training.
It outputs a JSON report containing VIF scores for each feature.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/vif_report.log')
    ]
)
logger = logging.getLogger(__name__)

def load_descriptors(input_path: str) -> pd.DataFrame:
    """
    Load the descriptor vector CSV.

    Args:
        input_path: Path to the descriptor vector CSV file.

    Returns:
        DataFrame containing the descriptors.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Descriptor file not found: {input_path}")

    df = pd.read_csv(input_path)
    logger.info(f"Loaded descriptors from {input_path}. Shape: {df.shape}")

    # Identify descriptor columns (exclude metadata columns like 'sample_id', 'phase_label')
    exclude_cols = ['sample_id', 'phase_label', 'composition']
    descriptor_cols = [col for col in df.columns if col not in exclude_cols]

    if not descriptor_cols:
        raise ValueError("No descriptor columns found in the input file.")

    logger.info(f"Using descriptor columns: {descriptor_cols}")
    return df[descriptor_cols]

def calculate_vif(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each column in the DataFrame.

    Args:
        df: DataFrame containing numeric descriptor columns.

    Returns:
        Dictionary mapping column names to their VIF scores.
    """
    if df.isnull().any().any():
        logger.warning("NaN values detected in descriptors. Dropping rows with NaN.")
        df = df.dropna()

    if len(df) == 0:
        raise ValueError("No valid data rows remaining after dropping NaNs.")

    vif_data = {}
    for i, col in enumerate(df.columns):
        # VIF requires an intercept, so we include all other columns as predictors
        # For VIF of col_i, we regress col_i against all other columns
        X = df.values
        try:
            vif = variance_inflation_factor(X, i)
            vif_data[col] = float(vif)
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = float('inf')

    return vif_data

def write_report(vif_data: Dict[str, float], output_path: str) -> None:
    """
    Write the VIF report to a JSON file.

    Args:
        vif_data: Dictionary of VIF scores.
        output_path: Path to the output JSON file.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created directory: {output_dir}")

    report = {
        "status": "success",
        "total_features": len(vif_data),
        "vif_scores": vif_data,
        "high_vif_features": [k for k, v in vif_data.items() if v > 10],
        "critical_vif_features": [k for k, v in vif_data.items() if v > 33]
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"VIF report written to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Compute VIF for descriptors.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/derived/descriptor_vector.csv",
        help="Path to the input descriptor CSV file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/derived/vif_report.json",
        help="Path to the output VIF report JSON file."
    )

    args = parser.parse_args()

    try:
        logger.info(f"Starting VIF calculation for {args.input}")
        df = load_descriptors(args.input)
        vif_scores = calculate_vif(df)
        write_report(vif_scores, args.output)
        logger.info("VIF calculation completed successfully.")
    except Exception as e:
        logger.error(f"VIF calculation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()