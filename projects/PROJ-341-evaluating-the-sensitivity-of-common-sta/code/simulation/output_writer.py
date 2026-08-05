"""
Output writer module for simulation results.
Handles writing p-values raw data and loading it back for analysis.
"""
import os
import csv
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from code.simulation.logging_config import get_logger, log_operation

logger = get_logger(__name__)

OUTPUT_DIR = "data/simulation"
P_VALUES_RAW_FILE = os.path.join(OUTPUT_DIR, "p_values_raw.csv")


def ensure_output_directory():
    """Ensure the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


@log_operation
def write_p_values_raw(results: List[Dict[str, Any]], output_path: Optional[str] = None):
    """
    Write simulation results to a CSV file.

    Args:
        results: List of dictionaries containing simulation results with keys:
            - sample_size (int)
            - effect_size (float)
            - test_type (str)
            - p_value (float)
            - hypothesis_state (str: 'null' or 'alternative')
            - alpha (float)
            - iteration (int)
        output_path: Optional custom output path. Defaults to P_VALUES_RAW_FILE.
    """
    ensure_output_directory()
    path = output_path or P_VALUES_RAW_FILE

    if not results:
        logger.log("write_p_values_raw", operation="empty_results", path=path, status="skipped")
        return

    # Define standard columns
    fieldnames = [
        "sample_size", "effect_size", "test_type", "p_value",
        "hypothesis_state", "alpha", "iteration", "timestamp"
    ]

    # Add any extra columns found in the first result
    if results:
        extra_cols = [k for k in results[0].keys() if k not in fieldnames]
        fieldnames.extend(extra_cols)

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            # Ensure all fieldnames are present, fill missing with empty string
            safe_row = {k: row.get(k, "") for k in fieldnames}
            writer.writerow(safe_row)

    logger.log("write_p_values_raw", operation="success", path=path, count=len(results))


def load_p_values_raw(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load p-values raw data from CSV.

    Args:
        input_path: Optional custom input path. Defaults to P_VALUES_RAW_FILE.

    Returns:
        pandas DataFrame with the loaded data.
    """
    path = input_path or P_VALUES_RAW_FILE
    if not os.path.exists(path):
        raise FileNotFoundError(f"P-values raw file not found: {path}")

    df = pd.read_csv(path)
    logger.log("load_p_values_raw", operation="success", path=path, rows=len(df))
    return df


def load_p_values_raw_safe(input_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Safely load p-values raw data, returning None if file not found or error occurs.

    Args:
        input_path: Optional custom input path.

    Returns:
        pandas DataFrame or None if loading fails.
    """
    try:
        return load_p_values_raw(input_path)
    except Exception as e:
        logger.log("load_p_values_raw_safe", operation="failed", error=str(e))
        return None


def main():
    """
    Main function to demonstrate writing and loading p-values raw data.
    This is typically called by the simulation runner after generating results.
    """
    # Example usage:
    sample_results = [
        {
            "sample_size": 10,
            "effect_size": 0.5,
            "test_type": "t-test",
            "p_value": 0.042,
            "hypothesis_state": "alternative",
            "alpha": 0.05,
            "iteration": 1
        },
        {
            "sample_size": 10,
            "effect_size": 0.5,
            "test_type": "t-test",
            "p_value": 0.123,
            "hypothesis_state": "alternative",
            "alpha": 0.05,
            "iteration": 2
        }
    ]

    write_p_values_raw(sample_results)
    df = load_p_values_raw()
    print(f"Loaded {len(df)} rows from {P_VALUES_RAW_FILE}")
    print(df.head())


if __name__ == "__main__":
    main()