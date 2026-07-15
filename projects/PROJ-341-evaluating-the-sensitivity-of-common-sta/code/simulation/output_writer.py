"""
Utility module for writing simulation results to disk.
Handles CSV output for p-values and other simulation artifacts.
"""
import os
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime

def write_p_values_raw(results: List[Dict[str, Any]], output_file: str, logger=None) -> None:
    """
    Write raw p-values to CSV file.
    
    Args:
        results: List of dictionaries containing simulation results
        output_file: Path to output CSV file
        logger: Optional logger for progress updates
    """
    if not results:
        if logger:
            logger.warning("No results to write")
        return

    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Define CSV columns
    fieldnames = [
        "sample_size",
        "effect_size",
        "test_type",
        "hypothesis",
        "alpha",
        "p_value",
        "iteration",
        "timestamp"
    ]

    timestamp = datetime.now().isoformat()

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, result in enumerate(results):
            row = {
                "sample_size": result.get("n"),
                "effect_size": result.get("effect_size"),
                "test_type": result.get("test_type"),
                "hypothesis": result.get("hypothesis"),
                "alpha": result.get("alpha"),
                "p_value": result.get("p_value"),
                "iteration": i + 1,
                "timestamp": timestamp
            }
            writer.writerow(row)

    if logger:
        logger.info(f"Successfully wrote {len(results)} results to {output_file}")

def load_p_values_raw(input_file: str) -> List[Dict[str, Any]]:
    """
    Load raw p-values from CSV file.
    
    Args:
        input_file: Path to input CSV file
        
    Returns:
        List of dictionaries containing simulation results
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    results = []
    with open(input_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert numeric fields
            result = {
                "n": int(row["sample_size"]),
                "effect_size": float(row["effect_size"]),
                "test_type": row["test_type"],
                "hypothesis": row["hypothesis"],
                "alpha": float(row["alpha"]),
                "p_value": float(row["p_value"]),
                "iteration": int(row["iteration"])
            }
            results.append(result)

    return results

def load_p_values_raw_safe(input_file: str) -> List[Dict[str, Any]]:
    """
    Safely load raw p-values, returning empty list if file doesn't exist.
    
    Args:
        input_file: Path to input CSV file
        
    Returns:
        List of dictionaries containing simulation results
    """
    try:
        return load_p_values_raw(input_file)
    except FileNotFoundError:
        return []
    except Exception as e:
        # Log error but return empty list to allow graceful degradation
        print(f"Warning: Failed to load {input_file}: {e}")
        return []