"""
Module to handle writing simulation results to CSV files.
Specifically implements T016: Writing raw p-values to data/simulation/p_values_raw.csv
"""
import os
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime

def write_p_values_raw(
    results: List[Dict[str, Any]],
    output_path: str = "data/simulation/p_values_raw.csv"
) -> str:
    """
    Writes simulation results containing p-values to a CSV file.
    
    Args:
        results: List of dictionaries containing simulation results.
                Expected keys: sample_size, effect_size, test_type, p_value, hypothesis_state, seed
        output_path: Path to the output CSV file.
    
    Returns:
        The absolute path to the written file.
    
    Raises:
        FileNotFoundError: If the output directory does not exist.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if not results:
        # Write empty file with headers if no results
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['sample_size', 'effect_size', 'test_type', 'p_value', 'hypothesis_state', 'seed', 'timestamp'])
        return os.path.abspath(output_path)

    # Define standard columns based on task requirements
    fieldnames = [
        'sample_size', 
        'effect_size', 
        'test_type', 
        'p_value', 
        'hypothesis_state',
        'seed',
        'timestamp'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in results:
            # Ensure all required fields are present, fill missing with defaults if necessary
            out_row = {
                'sample_size': row.get('sample_size', ''),
                'effect_size': row.get('effect_size', ''),
                'test_type': row.get('test_type', ''),
                'p_value': row.get('p_value', ''),
                'hypothesis_state': row.get('hypothesis_state', ''),
                'seed': row.get('seed', ''),
                'timestamp': row.get('timestamp', datetime.now().isoformat())
            }
            writer.writerow(out_row)
    
    return os.path.abspath(output_path)

def load_p_values_raw(
    input_path: str = "data/simulation/p_values_raw.csv"
) -> List[Dict[str, Any]]:
    """
    Loads raw p-values from the CSV file.
    
    Args:
        input_path: Path to the input CSV file.
    
    Returns:
        List of dictionaries containing the data.
    """
    results = []
    if not os.path.exists(input_path):
        return results
    
    with open(input_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings back to floats/integers
            try:
                row['sample_size'] = int(row['sample_size']) if row['sample_size'] else None
                row['effect_size'] = float(row['effect_size']) if row['effect_size'] else None
                row['p_value'] = float(row['p_value']) if row['p_value'] else None
            except ValueError:
                pass # Keep as string if conversion fails
            results.append(row)
    
    return results
