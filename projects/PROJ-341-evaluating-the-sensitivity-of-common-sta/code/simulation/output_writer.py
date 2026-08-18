"""
Output writing utilities for the simulation pipeline.
Handles writing raw p-values and loading them for downstream analysis.
"""
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
        os.makedirs(directory, exist_ok=True)
        logger.log("output_directory_created", path=directory)

def write_p_values_raw(
    results: List[Dict[str, Any]],
    output_path: str = "data/simulation/p_values_raw.csv"
) -> None:
    """
    Write simulation results to a CSV file.
    
    Args:
        results: List of dictionaries containing simulation results.
                 Expected keys: sample_size, effect_size, test_type, p_value, hypothesis_state
        output_path: Path to the output CSV file.
    """
    if not results:
        logger.log("no_results_to_write", path=output_path)
        return

    ensure_output_directory(output_path)

    # Use pandas for vectorized writing as requested
    df = pd.DataFrame(results)
    
    # Ensure required columns exist and are in the correct order
    required_cols = ["sample_size", "effect_size", "test_type", "p_value", "hypothesis_state"]
    existing_cols = [c for c in required_cols if c in df.columns]
    # Add any missing columns with NaN if they somehow aren't there (shouldn't happen)
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    # Reorder to match spec
    df = df[required_cols]

    df.to_csv(output_path, index=False)
    logger.log("p_values_raw_written", path=output_path, row_count=len(results))

def load_p_values_raw(input_path: str = "data/simulation/p_values_raw.csv") -> pd.DataFrame:
    """
    Load raw p-values from CSV.
    
    Args:
        input_path: Path to the CSV file.
        
    Returns:
        pandas DataFrame containing the raw p-values.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Raw p-values file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.log("p_values_raw_loaded", path=input_path, row_count=len(df))
    return df

def load_p_values_raw_safe(input_path: str = "data/simulation/p_values_raw.csv") -> Optional[pd.DataFrame]:
    """
    Safely load raw p-values, returning None if file doesn't exist or is invalid.
    """
    try:
        return load_p_values_raw(input_path)
    except FileNotFoundError:
        logger.log("p_values_raw_not_found", path=input_path)
        return None
    except Exception as e:
        logger.log("p_values_raw_load_error", path=input_path, error=str(e))
        return None

def main():
    """
    Standalone execution for testing the writer.
    Generates dummy data to verify the write path works.
    """
    # Dummy data for testing
    dummy_results = [
        {
            "sample_size": 10,
            "effect_size": 0.0,
            "test_type": "t-test",
            "p_value": 0.45,
            "hypothesis_state": "null"
        },
        {
            "sample_size": 50,
            "effect_size": 0.5,
            "test_type": "anova",
            "p_value": 0.02,
            "hypothesis_state": "alt"
        }
    ]
    
    test_output = "data/simulation/test_p_values_raw.csv"
    write_p_values_raw(dummy_results, test_output)
    print(f"Test write complete: {test_output}")

if __name__ == "__main__":
    main()
