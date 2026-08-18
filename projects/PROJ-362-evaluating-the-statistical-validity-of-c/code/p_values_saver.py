"""
Module to save raw p-values to CSV.

This module handles the persistence of raw p-values calculated from
permutation tests to the results directory.
"""
import os
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import RESULTS_DIR, ensure_dirs

logger = logging.getLogger(__name__)

def ensure_p_values_dir() -> Path:
    """
    Ensure the p_values directory exists within RESULTS_DIR.
    
    Returns:
        Path: The path to the p_values directory.
    """
    p_values_dir = Path(RESULTS_DIR) / "p_values"
    ensure_dirs(p_values_dir)
    return p_values_dir

def save_raw_p_values(p_values: List[Dict[str, Any]], output_file: Optional[str] = None) -> Path:
    """
    Save a list of raw p-value dictionaries to a CSV file.
    
    Args:
        p_values: List of dictionaries containing 'query_id', 'metric', and 'p_value'.
        output_file: Optional filename. Defaults to 'raw_p_values.csv'.
        
    Returns:
        Path: The path to the saved file.
        
    Raises:
        ValueError: If the p_values list is empty or contains invalid data.
    """
    if not p_values:
        logger.warning("No p-values provided to save. Creating empty file.")
    
    p_values_dir = ensure_p_values_dir()
    if output_file is None:
        output_file = "raw_p_values.csv"
        
    output_path = p_values_dir / output_file
    
    if not p_values:
        # Create empty file with headers if no data
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['query_id', 'metric', 'p_value'])
        logger.info(f"Created empty p-values file at {output_path}")
        return output_path

    # Validate and write data
    required_keys = {'query_id', 'metric', 'p_value'}
    for i, item in enumerate(p_values):
        if not isinstance(item, dict):
            raise ValueError(f"Item at index {i} is not a dictionary: {type(item)}")
        missing = required_keys - set(item.keys())
        if missing:
            raise ValueError(f"Item at index {i} missing keys: {missing}")
        if not isinstance(item['p_value'], (int, float)):
            raise ValueError(f"Item at index {i} has invalid p_value type: {type(item['p_value'])}")

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'p_value'])
        writer.writeheader()
        writer.writerows(p_values)
        
    logger.info(f"Saved {len(p_values)} raw p-values to {output_path}")
    return output_path

def run_p_values_saving(p_values: List[Dict[str, Any]], output_file: Optional[str] = None) -> Path:
    """
    Wrapper function to save raw p-values, suitable for integration with main.py.
    
    Args:
        p_values: List of dictionaries with p-value data.
        output_file: Optional filename.
        
    Returns:
        Path: Path to the saved file.
    """
    return save_raw_p_values(p_values, output_file)
