import os
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from code.simulation.logging_config import get_logger

def ensure_output_directory(filepath: str) -> None:
    """Ensure the directory for the output file exists."""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def write_p_values_raw(results: List[Dict[str, Any]], filepath: str) -> None:
    """
    Write raw p-values to a CSV file.
    
    Args:
        results: List of dictionaries containing simulation results
        filepath: Path to the output CSV file
    """
    if not results:
        logger = get_logger()
        logger.warning("No results to write to CSV")
        return
        
    ensure_output_directory(filepath)
    
    # Define standard columns
    columns = ['sample_size', 'effect_size', 'test_type', 'p_value', 'hypothesis_state']
    
    # Check if all results have the same keys
    first_keys = set(results[0].keys())
    for result in results[1:]:
        if set(result.keys()) != first_keys:
            logger = get_logger()
            logger.warning("Inconsistent keys in results. Using union of all keys.")
            first_keys = first_keys.union(set(result.keys()))
            break
    
    # Write to CSV
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        
        for result in results:
            # Ensure all required columns are present
            row = {col: result.get(col, '') for col in columns}
            writer.writerow(row)
    
    logger = get_logger()
    logger.info(f"Wrote {len(results)} results to {filepath}")

def load_p_values_raw(filepath: str) -> pd.DataFrame:
    """
    Load raw p-values from a CSV file.
    
    Args:
        filepath: Path to the input CSV file
        
    Returns:
        pd.DataFrame: DataFrame containing the loaded data
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    return pd.read_csv(filepath)

def load_p_values_raw_safe(filepath: str) -> Optional[pd.DataFrame]:
    """
    Safely load raw p-values from a CSV file.
    
    Args:
        filepath: Path to the input CSV file
        
    Returns:
        Optional[pd.DataFrame]: DataFrame containing the loaded data, or None if failed
    """
    try:
        return load_p_values_raw(filepath)
    except Exception as e:
        logger = get_logger()
        logger.error(f"Failed to load p-values from {filepath}: {e}")
        return None
