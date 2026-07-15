"""Output writer module for simulation results.

Handles writing raw p-values to CSV and loading them back for analysis.
"""
import os
import csv
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from code.simulation.logging_config import get_logger, log_operation

logger = get_logger(__name__)

# Output paths
OUTPUT_DIR = "data/simulation"
P_VALUES_RAW_FILE = os.path.join(OUTPUT_DIR, "p_values_raw.csv")

def ensure_output_directory() -> None:
    """Ensure the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def write_p_values_raw(
    results: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """Write raw p-values to a CSV file.

    Args:
        results: List of dictionaries containing simulation results.
                Each dict should have keys: sample_size, effect_size,
                test_type, p_value, hypothesis_state
        output_path: Optional custom output path. Defaults to P_VALUES_RAW_FILE.

    Returns:
        The path to the written file.
    """
    if output_path is None:
        output_path = P_VALUES_RAW_FILE

    ensure_output_directory()

    if not results:
        logger.log("write_p_values_raw", operation="empty_results", path=output_path)
        # Write empty file with headers
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['sample_size', 'effect_size', 'test_type', 'p_value', 'hypothesis_state'])
        return output_path

    # Write to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['sample_size', 'effect_size', 'test_type', 'p_value', 'hypothesis_state'])

        # Write data rows
        for row in results:
            writer.writerow([
                row.get('sample_size', ''),
                row.get('effect_size', ''),
                row.get('test_type', ''),
                row.get('p_value', ''),
                row.get('hypothesis_state', '')
            ])

    logger.log("write_p_values_raw", operation="success", path=output_path, rows=len(results))
    return output_path

def load_p_values_raw(
    input_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Load raw p-values from a CSV file.

    Args:
        input_path: Optional custom input path. Defaults to P_VALUES_RAW_FILE.

    Returns:
        List of dictionaries containing the loaded results.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if input_path is None:
        input_path = P_VALUES_RAW_FILE

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Raw p-values file not found: {input_path}")

    results = []
    with open(input_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['sample_size'] = int(row['sample_size'])
                row['effect_size'] = float(row['effect_size'])
                row['p_value'] = float(row['p_value'])
            except (ValueError, KeyError) as e:
                # Skip malformed rows but log warning
                logger.log("load_p_values_raw", operation="malformed_row", error=str(e))
                continue
            results.append(row)

    if not results:
        raise ValueError(f"Raw p-values file is empty or contains no valid data: {input_path}")

    logger.log("load_p_values_raw", operation="success", path=input_path, rows=len(results))
    return results

def load_p_values_raw_safe(
    input_path: Optional[str] = None
) -> Optional[List[Dict[str, Any]]]:
    """Load raw p-values safely, returning None on failure instead of raising.

    Args:
        input_path: Optional custom input path. Defaults to P_VALUES_RAW_FILE.

    Returns:
        List of dictionaries if successful, None if file not found or empty.
    """
    try:
        return load_p_values_raw(input_path)
    except (FileNotFoundError, ValueError):
        return None

def main() -> None:
    """Main function for testing the output writer module.

    This creates sample data and writes it to the CSV file.
    """
    # Sample data for testing
    sample_results = [
        {
            'sample_size': 5,
            'effect_size': 0.0,
            'test_type': 't-test',
            'p_value': 0.45,
            'hypothesis_state': 'null_true'
        },
        {
            'sample_size': 5,
            'effect_size': 0.5,
            'test_type': 't-test',
            'p_value': 0.02,
            'hypothesis_state': 'alt_true'
        },
        {
            'sample_size': 100,
            'effect_size': 0.0,
            'test_type': 'anova',
            'p_value': 0.33,
            'hypothesis_state': 'null_true'
        },
        {
            'sample_size': 100,
            'effect_size': 0.5,
            'test_type': 'chi-squared',
            'p_value': 0.001,
            'hypothesis_state': 'alt_true'
        }
    ]

    output_path = write_p_values_raw(sample_results)
    print(f"Wrote {len(sample_results)} results to {output_path}")

    # Verify by loading back
    loaded = load_p_values_raw(output_path)
    print(f"Loaded {len(loaded)} results from {output_path}")

    for row in loaded:
        print(f"  n={row['sample_size']}, effect={row['effect_size']}, "
              f"test={row['test_type']}, p={row['p_value']}, state={row['hypothesis_state']}")

if __name__ == "__main__":
    main()