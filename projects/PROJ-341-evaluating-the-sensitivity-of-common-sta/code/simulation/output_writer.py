"""Output writer module for simulation results."""
import os
import csv
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from code.simulation.logging_config import get_logger

logger = get_logger(__name__)


def ensure_output_directory(output_path: str) -> None:
    """Ensure the directory for the output file exists."""
    directory = os.path.dirname(output_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        logger.log("directory_created", path=directory)


def write_p_values_raw(
    results: List[Dict[str, Any]],
    output_path: str = "data/simulation/p_values_raw.csv"
) -> None:
    """
    Write simulation p-values to a CSV file.

    Args:
        results: List of dictionaries containing simulation results.
                 Each dict should have keys: sample_size, effect_size, test_type,
                 p_value, hypothesis_state, iteration_id (optional), seed (optional).
        output_path: Path to the output CSV file.
    """
    ensure_output_directory(output_path)

    if not results:
        logger.log("write_p_values_raw", path=output_path, status="skipped", reason="no_results")
        return

    # Define standard columns
    columns = ["sample_size", "effect_size", "test_type", "p_value", "hypothesis_state"]
    
    # Check for optional columns in the first result
    if results:
        optional_cols = [k for k in results[0].keys() if k not in columns]
        columns.extend(sorted(optional_cols))

    logger.log("write_p_values_raw", path=output_path, num_rows=len(results), columns=columns)

    try:
        df = pd.DataFrame(results, columns=columns)
        df.to_csv(output_path, index=False)
        logger.log("file_written", path=output_path, size_bytes=os.path.getsize(output_path))
    except Exception as e:
        logger.log("file_write_error", path=output_path, error=str(e))
        raise


def load_p_values_raw(
    input_path: str = "data/simulation/p_values_raw.csv"
) -> List[Dict[str, Any]]:
    """
    Load p-values from a CSV file.

    Args:
        input_path: Path to the input CSV file.

    Returns:
        List of dictionaries containing the loaded data.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.log("load_p_values_raw", path=input_path)
    try:
        df = pd.read_csv(input_path)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.log("file_load_error", path=input_path, error=str(e))
        raise


def load_p_values_raw_safe(
    input_path: str = "data/simulation/p_values_raw.csv"
) -> List[Dict[str, Any]]:
    """
    Safely load p-values, returning an empty list if file not found or error occurs.

    Args:
        input_path: Path to the input CSV file.

    Returns:
        List of dictionaries, or empty list if error.
    """
    try:
        return load_p_values_raw(input_path)
    except Exception as e:
        logger.log("load_p_values_raw_safe_error", path=input_path, error=str(e))
        return []


def main() -> None:
    """
    Main entry point for testing the output writer.
    Generates sample data and writes it to the CSV.
    """
    # Sample data for testing
    sample_results = [
        {
            "sample_size": 10,
            "effect_size": 0.5,
            "test_type": "t-test",
            "p_value": 0.032,
            "hypothesis_state": "null_true",
            "iteration_id": 1,
            "seed": 42
        },
        {
            "sample_size": 10,
            "effect_size": 0.5,
            "test_type": "t-test",
            "p_value": 0.045,
            "hypothesis_state": "null_true",
            "iteration_id": 2,
            "seed": 43
        },
        {
            "sample_size": 50,
            "effect_size": 0.8,
            "test_type": "anova",
            "p_value": 0.001,
            "hypothesis_state": "alt_true",
            "iteration_id": 1,
            "seed": 42
        },
        {
            "sample_size": 50,
            "effect_size": 0.8,
            "test_type": "chi-squared",
            "p_value": 0.067,
            "hypothesis_state": "null_true",
            "iteration_id": 1,
            "seed": 42
        }
    ]

    output_path = "data/simulation/p_values_raw.csv"
    write_p_values_raw(sample_results, output_path)
    print(f"Successfully wrote {len(sample_results)} records to {output_path}")


if __name__ == "__main__":
    main()