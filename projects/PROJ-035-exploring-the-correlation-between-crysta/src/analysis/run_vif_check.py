import sys
import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import from the project's validation utility
from src.utils.validation import setup_logger, calculate_vif

def run_vif_check(
    input_path: str,
    output_csv_path: str,
    report_path: str,
    vif_threshold: float = 5.0,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Execute VIF check on the dataset, filter out high-VIF predictors,
    save the filtered dataset, and generate a VIF report.

    Args:
        input_path: Path to the input CSV with descriptors.
        output_csv_path: Path to save the filtered dataset.
        report_path: Path to save the VIF report JSON.
        vif_threshold: Threshold above which predictors are excluded.
        seed: Random seed for reproducibility (if needed).

    Returns:
        A dictionary containing the VIF results and summary.
    """
    logger = setup_logger("run_vif_check", logging.INFO)
    logger.info(f"Loading data from {input_path}")

    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    # Define predictors based on T021/T022 output schema
    # These are the structural descriptors calculated previously
    predictor_columns = [
        'tilting_angle',
        'bond_length_variance',
        'tolerance_factor',
        'unit_cell_volume'
    ]

    # Ensure predictors exist in the dataframe
    missing_cols = [col for col in predictor_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing predictor columns in input data: {missing_cols}")

    X = df[predictor_columns]

    # Calculate VIF for all predictors
    # Using the function from src.utils.validation
    vif_data = calculate_vif(X, predictor_columns)
    # vif_data is expected to be a list of dicts: [{'feature': name, 'vif': value}, ...]

    logger.info(f"Calculated VIF for {len(vif_data)} predictors")

    # Identify predictors to exclude (VIF > threshold)
    excluded_predictors = [item['feature'] for item in vif_data if item['vif'] > vif_threshold]
    included_predictors = [item['feature'] for item in vif_data if item['vif'] <= vif_threshold]

    logger.info(f"Excluding predictors with VIF > {vif_threshold}: {excluded_predictors}")
    logger.info(f"Keeping predictors: {included_predictors}")

    # Prepare the filtered dataset
    # We keep the target variable (thermal_conductivity) and the included predictors
    # Assuming the input file contains 'thermal_conductivity' as the target
    target_col = 'thermal_conductivity'
    if target_col not in df.columns:
        # If target is missing, we still filter the predictors but warn
        logger.warning(f"Target column '{target_col}' not found in input. Keeping all non-predictor columns.")
        cols_to_keep = [c for c in df.columns if c in included_predictors or c == target_col]
        # Fallback if target missing: keep all non-predictor columns + included predictors
        cols_to_keep = [c for c in df.columns if c not in predictor_columns or c in included_predictors]
    else:
        cols_to_keep = [target_col] + included_predictors

    df_filtered = df[cols_to_keep]

    # Save filtered dataset
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_filtered.to_csv(output_csv_path, index=False)
    logger.info(f"Saved filtered dataset to {output_csv_path}")

    # Generate VIF report
    report = {
        "vif_results": vif_data,
        "excluded_predictors": excluded_predictors,
        "included_predictors": included_predictors,
        "threshold": vif_threshold,
        "input_rows": len(df),
        "output_rows": len(df_filtered),
        "input_columns": list(df.columns),
        "output_columns": list(df_filtered.columns)
    }

    # Save report
    report_path_obj = Path(report_path)
    report_path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved VIF report to {report_path}")

    return report

def main():
    parser = argparse.ArgumentParser(description="Run VIF check and filter dataset")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input CSV file (e.g., data/descriptors.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save filtered CSV file (e.g., data/cleaned/descriptors_vif_filtered.csv)"
    )
    parser.add_argument(
        "--report",
        type=str,
        required=True,
        help="Path to save VIF report JSON (e.g., data/results/vif_report.json)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="VIF threshold for exclusion (default: 5.0)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    try:
        run_vif_check(
            input_path=args.input,
            output_csv_path=args.output,
            report_path=args.report,
            vif_threshold=args.threshold,
            seed=args.seed
        )
        print("VIF check completed successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"Error during VIF check: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
