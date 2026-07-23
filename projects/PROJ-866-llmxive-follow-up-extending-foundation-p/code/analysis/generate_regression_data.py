"""
Generate raw regression data for the paper (T032).

This script loads the processed execution logs, calls the existing
tradeoff_model.generate_regression_data() function to compute the
regression curve points, and saves the result to data/results/tradeoff_curve.csv.

It does NOT generate synthetic data; it computes the curve from the real
processed logs produced by previous pipeline stages (T024-T031).
"""
import json
import os
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from analysis.tradeoff_model import generate_regression_data, load_processed_logs


def save_regression_data_to_csv(
    regression_data: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save the regression data points to a CSV file.

    Args:
        regression_data: List of dictionaries containing the regression curve points.
        output_path: Path to the output CSV file.
    """
    if not regression_data:
        raise ValueError("No regression data to save.")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine field names from the first data point
    fieldnames = list(regression_data[0].keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(regression_data)

    print(f"Saved {len(regression_data)} regression data points to {output_path}")


def main() -> int:
    """
    Main entry point for generating regression data.

    Returns:
        0 on success, non-zero on failure.
    """
    # Define paths
    processed_logs_dir = project_root / "data" / "processed"
    output_file = project_root / "data" / "results" / "tradeoff_curve.csv"

    if not processed_logs_dir.exists():
        print(f"Error: Processed logs directory not found: {processed_logs_dir}")
        print("Please ensure T025 has been completed and logs exist in data/processed/")
        return 1

    print(f"Loading processed execution logs from {processed_logs_dir}...")
    try:
        logs = load_processed_logs(processed_logs_dir)
    except Exception as e:
        print(f"Error loading processed logs: {e}")
        return 1

    if not logs:
        print("No processed logs found. Cannot generate regression data.")
        return 1

    print(f"Loaded {len(logs)} processed execution logs.")

    print("Generating regression curve data...")
    try:
        regression_data = generate_regression_data(logs)
    except Exception as e:
        print(f"Error generating regression data: {e}")
        return 1

    if not regression_data:
        print("No regression data points generated.")
        return 1

    print(f"Generated {len(regression_data)} data points.")
    print(f"Saving to {output_file}...")

    try:
        save_regression_data_to_csv(regression_data, output_file)
    except Exception as e:
        print(f"Error saving regression data: {e}")
        return 1

    print("Successfully generated tradeoff_curve.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
