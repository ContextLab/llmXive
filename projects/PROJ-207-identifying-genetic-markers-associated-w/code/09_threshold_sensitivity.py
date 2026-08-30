"""
Threshold Sensitivity Analysis Script.

This script performs a sensitivity analysis on the FDR-corrected GWAS results
by sweeping across a range of q-value thresholds to determine the robustness
of the identified genetic markers.

It reads the FDR-corrected results and counts how many SNPs pass each threshold.
"""
import os
import sys
import argparse
import json
from pathlib import Path

import pandas as pd

def load_fdr_results(input_path: str) -> pd.DataFrame:
    """
    Load the FDR-corrected GWAS results.

    Args:
        input_path: Path to the TSV file containing FDR-corrected results.

    Returns:
        DataFrame with the results.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the required columns are missing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path, sep='\t')

    required_columns = ['rank', 'raw_p', 'q_value', 'significant']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Input file missing required columns: {missing_cols}")

    return df

def generate_thresholds(min_val: float = 0.01, max_val: float = 0.10, step: float = 0.01) -> list:
    """
    Generate a list of q-value thresholds to sweep.

    Args:
        min_val: Minimum threshold value.
        max_val: Maximum threshold value.
        step: Step size between thresholds.

    Returns:
        List of float thresholds.
    """
    thresholds = []
    current = min_val
    while current <= max_val:
        thresholds.append(round(current, 2))
        current += step
    return thresholds

def run_sensitivity_analysis(df: pd.DataFrame, thresholds: list) -> dict:
    """
    Run the sensitivity analysis across the provided thresholds.

    Args:
        df: DataFrame containing FDR-corrected results.
        thresholds: List of q-value thresholds to test.

    Returns:
        Dictionary containing the analysis results.
    """
    results = {
        "thresholds_tested": thresholds,
        "total_snps": len(df),
        "sensitivity_data": []
    }

    for threshold in thresholds:
        # Count SNPs passing the threshold (q_value <= threshold)
        passing = df[df['q_value'] <= threshold]
        count = len(passing)
        q_values = passing['q_value'].tolist()

        results["sensitivity_data"].append({
            "threshold": threshold,
            "significant_snps_count": count,
            "significant_q_values": q_values
        })

    return results

def write_output(results: dict, output_path: str) -> None:
    """
    Write the sensitivity analysis results to a JSON file.

    Args:
        results: Dictionary containing the analysis results.
        output_path: Path to the output JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Sensitivity analysis results written to: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Perform threshold sensitivity analysis on FDR-corrected GWAS results."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the FDR-corrected GWAS results TSV file (e.g., data/interim/gwas_fdr.tsv)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/threshold_sensitivity.json",
        help="Path to the output JSON file for sensitivity results."
    )
    parser.add_argument(
        "--min-threshold",
        type=float,
        default=0.01,
        help="Minimum q-value threshold to test (default: 0.01)."
    )
    parser.add_argument(
        "--max-threshold",
        type=float,
        default=0.10,
        help="Maximum q-value threshold to test (default: 0.10)."
    )
    parser.add_argument(
        "--step",
        type=float,
        default=0.01,
        help="Step size for threshold sweep (default: 0.01)."
    )

    args = parser.parse_args()

    try:
        print(f"Loading FDR results from: {args.input}")
        df = load_fdr_results(args.input)

        print(f"Generating thresholds from {args.min_threshold} to {args.max_threshold} (step {args.step})")
        thresholds = generate_thresholds(args.min_threshold, args.max_threshold, args.step)

        print("Running sensitivity analysis...")
        results = run_sensitivity_analysis(df, thresholds)

        print(f"Writing results to: {args.output}")
        write_output(results, args.output)

        print("Threshold sensitivity analysis completed successfully.")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()