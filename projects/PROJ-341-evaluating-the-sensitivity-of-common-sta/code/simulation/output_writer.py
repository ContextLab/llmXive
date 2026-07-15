import os
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime

def write_p_values_raw(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write raw p-values to a CSV file.
    
    Args:
        results: List of dictionaries containing simulation results
        output_path: Path to the output CSV file
    """
    if not results:
        raise ValueError("No results to write")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define fieldnames based on expected columns
    fieldnames = [
        'run_id',
        'sample_size',
        'effect_size',
        'test_type',
        'hypothesis_state',
        'alpha',
        'p_value',
        'iteration'
    ]
    
    # Write to CSV
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def load_p_values_raw(input_path: str) -> List[Dict[str, Any]]:
    """
    Load raw p-values from a CSV file.
    
    Args:
        input_path: Path to the input CSV file
        
    Returns:
        List of dictionaries containing the loaded data
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")
    
    results = []
    with open(input_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert numeric fields
            row['sample_size'] = int(row['sample_size'])
            row['effect_size'] = float(row['effect_size'])
            row['alpha'] = float(row['alpha'])
            row['p_value'] = float(row['p_value'])
            row['iteration'] = int(row['iteration'])
            results.append(row)
    
    return results
