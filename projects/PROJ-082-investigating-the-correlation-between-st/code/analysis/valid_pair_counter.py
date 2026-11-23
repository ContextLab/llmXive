"""
Valid Pair Counter (Task T014b).

Counts rows with both 'r' and 'n' present in extracted_studies.csv.
Output: data/processed/valid_pair_count.json

This script must be run after T013 (parser) which produces extracted_studies.csv.
It reads the CSV, validates that 'r' and 'n' are present and numeric,
and writes the count to a JSON file.
"""
import csv
import json
import logging
import math
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("valid_pair_counter")

def get_project_root() -> Path:
    """Get the project root directory (parent of code/)."""
    return Path(__file__).resolve().parent.parent.parent

def get_input_path() -> Path:
    """Path to extracted_studies.csv."""
    return get_project_root() / "data" / "processed" / "extracted_studies.csv"

def get_output_path() -> Path:
    """Path to valid_pair_count.json."""
    return get_project_root() / "data" / "processed" / "valid_pair_count.json"

def load_extracted_studies(path: Path) -> List[Dict[str, Any]]:
    """
    Load the extracted studies CSV file.
    
    Args:
        path: Path to the CSV file.
        
    Returns:
        List of dictionaries representing rows.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    studies = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append(row)
    
    logger.info(f"Loaded {len(studies)} rows from {path}")
    return studies

def is_valid_pair(row: Dict[str, Any]) -> bool:
    """
    Check if a row has valid 'r' and 'n' values.
    
    A valid pair requires:
    - 'r' is present, not None, and can be converted to a float (not nan/inf)
    - 'n' is present, not None, and can be converted to a positive integer
    
    Args:
        row: A dictionary representing a study row.
        
    Returns:
        True if the row has a valid (r, n) pair.
    """
    r_val = row.get('r')
    n_val = row.get('n')
    
    # Check for missing values
    if r_val is None or n_val is None:
        return False
    
    # Check for empty strings
    if r_val == '' or n_val == '':
        return False
    
    try:
        r = float(r_val)
        n_float = float(n_val)
        n = int(n_float)
        
        # Validate r is a real number (not nan/inf)
        if math.isnan(r) or math.isinf(r):
            return False
        
        # Validate n is positive
        if n <= 0:
            return False
            
        return True
        
    except (ValueError, TypeError):
        return False

def count_valid_pairs(studies: List[Dict[str, Any]]) -> int:
    """
    Count the number of studies with valid (r, n) pairs.
    
    Args:
        studies: List of study dictionaries.
        
    Returns:
        The count of valid pairs.
    """
    count = 0
    for study in studies:
        if is_valid_pair(study):
            count += 1
    return count

def save_valid_pair_count(count: int, path: Path) -> None:
    """
    Save the valid pair count to a JSON file.
    
    Args:
        count: The number of valid pairs.
        path: The output file path.
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {"N_valid": count}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved valid pair count: {count} to {path}")

def run_valid_pair_counter() -> int:
    """
    Main execution function for the valid pair counter.
    
    Returns:
        Exit code (0 for success).
    """
    input_path = get_input_path()
    output_path = get_output_path()
    
    try:
        # Load data
        studies = load_extracted_studies(input_path)
        
        # Count valid pairs
        count = count_valid_pairs(studies)
        
        # Save result
        save_valid_pair_count(count, output_path)
        
        logger.info(f"Analysis complete. Valid pairs: {count}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        # Write a count of 0 if input is missing, but log error
        save_valid_pair_count(0, output_path)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        return 1

def main() -> int:
    """Entry point."""
    return run_valid_pair_counter()

if __name__ == "__main__":
    sys.exit(main())