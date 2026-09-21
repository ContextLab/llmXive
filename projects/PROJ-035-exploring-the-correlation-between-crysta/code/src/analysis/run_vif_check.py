import sys
import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# Import the validated VIF utility from the project's validation module
from src.utils.validation import calculate_vif, get_high_vif_predictors, setup_logger

def run_vif_check(
    input_path: str,
    output_csv_path: str,
    report_json_path: str,
    vif_threshold: float = 5.0,
    seed: int = 42
) -> None:
    """
    Execute VIF check on the dataset, exclude high-VIF predictors, and save results.

    Logic:
    1. Load the input dataset (expected to contain computed descriptors).
    2. Identify numeric predictor columns.
    3. Calculate VIF for all predictors.
    4. Exclude predictors with VIF > threshold.
    5. Save the filtered dataset to `output_csv_path`.
    6. Generate a VIF report JSON listing VIF for all predictors to `report_json_path`.

    Args:
        input_path: Path to the input CSV (e.g., data/descriptors.csv).
        output_csv_path: Path to save the filtered dataset.
        report_json_path: Path to save the VIF report JSON.
        vif_threshold: Threshold above which predictors are excluded (default 5.0).
        seed: Random seed for reproducibility (used if any stochastic steps exist).
    """
    logger = setup_logger("vif_check", logging.INFO)
    logger.info(f"Starting VIF check with threshold {vif_threshold}")

    # Load data
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")

    # Identify numeric predictor columns
    # We assume the target variable is 'thermal_conductivity' or similar,
    # and we want to calculate VIF on the structural descriptors.
    # Common descriptors from T021: tilting_angle, bond_length_variance, tolerance_factor, unit_cell_volume
    # We select only numeric columns that are likely predictors.
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Heuristic: Exclude 'thermal_conductivity' if present, and any ID columns
    # Based on T021 output and T005 schema, 'thermal_conductivity' is the target.
    # We want to check collinearity among the structural descriptors.
    predictors = [col for col in numeric_cols if col not in ['thermal_conductivity', 'structure_id']]
    
    if len(predictors) == 0:
        raise ValueError("No numeric predictor columns found in the dataset.")
    
    logger.info(f"Identified predictors for VIF: {predictors}")

    # Calculate VIF
    vif_data = calculate_vif(df, predictors)
    
    # Create report
    report = {
        "vif_values": vif_data,
        "threshold": vif_threshold,
        "high_vif_predictors": [p for p, v in vif_data.items() if v > vif_threshold],
        "total_predictors": len(predictors),
        "excluded_count": len([p for p, v in vif_data.items() if v > vif_threshold])
    }

    # Save VIF report
    Path(report_json_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_json_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"VIF report saved to {report_json_path}")

    # Filter dataset
    # Exclude predictors with VIF > threshold
    high_vif_cols = get_high_vif_predictors(vif_data, vif_threshold)
    if high_vif_cols:
        logger.warning(f"Excluding predictors with VIF > {vif_threshold}: {high_vif_cols}")
        cols_to_keep = [col for col in df.columns if col not in high_vif_cols]
        df_filtered = df[cols_to_keep]
    else:
        logger.info("No predictors exceeded the VIF threshold. Keeping all columns.")
        df_filtered = df

    # Save filtered dataset
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    df_filtered.to_csv(output_csv_path, index=False)
    logger.info(f"Filtered dataset saved to {output_csv_path} with {len(df_filtered.columns)} columns")

def main():
    parser = argparse.ArgumentParser(description="Run VIF check on perovskite descriptors")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV (e.g., data/descriptors.csv)")
    parser.add_argument("--output-csv", type=str, required=True, help="Path to save filtered CSV")
    parser.add_argument("--output-json", type=str, required=True, help="Path to save VIF report JSON")
    parser.add_argument("--threshold", type=float, default=5.0, help="VIF threshold for exclusion")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()

    run_vif_check(
        input_path=args.input,
        output_csv_path=args.output_csv,
        report_json_path=args.output_json,
        vif_threshold=args.threshold,
        seed=args.seed
    )

if __name__ == "__main__":
    main()