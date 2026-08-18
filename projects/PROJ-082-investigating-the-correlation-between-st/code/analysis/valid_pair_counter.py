"""
T014b: Valid Pair Counter

Task: Read `data/processed/extracted_studies.csv` and count studies with valid (r, n) pairs.
Output: Write `data/processed/valid_pair_count.json` containing `{"N_valid": <count>}`.

Constraint: This task distinguishes between 'Data Insufficient' (N_valid = 0) and 
'Narrative Fallback' (N_valid < 10).
"""
import csv
import json
import logging
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import shared utilities from existing project API
from utils.config import get_project_root
from utils.logger import get_logger

logger = get_logger(__name__)

def get_input_path() -> Path:
    """Return the path to the extracted studies CSV."""
    root = get_project_root()
    return root / "data" / "processed" / "extracted_studies.csv"

def get_output_path() -> Path:
    """Return the path to the valid pair count JSON."""
    root = get_project_root()
    return root / "data" / "processed" / "valid_pair_count.json"

def load_extracted_studies(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load the extracted studies from CSV.
    
    Args:
        csv_path: Path to the CSV file.
        
    Returns:
        List of dictionaries representing each row.
        
    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Input file not found: {csv_path}")
    
    studies = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append(row)
    
    if not studies:
        logger.warning(f"Input file {csv_path} exists but contains no data rows.")
    
    return studies

def is_valid_pair(row: Dict[str, Any]) -> bool:
    """
    Check if a study row has valid (r, n) pairs.
    
    A pair is valid if:
    1. 'r' exists and is not empty/null
    2. 'n' exists and is not empty/null
    3. Both can be converted to float/int respectively
    4. Values are not NaN or Inf
    5. n > 0
    
    Args:
        row: A dictionary representing a study row.
        
    Returns:
        True if valid, False otherwise.
    """
    r_val = row.get('r')
    n_val = row.get('n')
    
    # Check for None or empty strings
    if r_val is None or r_val == '' or str(r_val).lower() == 'nan':
        return False
    if n_val is None or n_val == '' or str(n_val).lower() == 'nan':
        return False
    
    try:
        r_float = float(r_val)
        # Handle cases where n might be "5.0"
        n_float = float(n_val)
        n_int = int(n_float)
        
        # Check for NaN or Inf
        if math.isnan(r_float) or math.isinf(r_float):
            return False
        if math.isnan(n_float) or math.isinf(n_float):
            return False
            
        if n_int <= 0:
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
        Count of valid pairs.
    """
    count = 0
    for study in studies:
        if is_valid_pair(study):
            count += 1
    return count

def save_valid_pair_count(count: int, output_path: Path) -> None:
    """
    Save the valid pair count to a JSON file.
    
    Args:
        count: The number of valid pairs.
        output_path: Path to the output JSON file.
    """
    result = {"N_valid": count}
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved valid pair count: {count} to {output_path}")

def run_valid_pair_counter() -> Dict[str, Any]:
    """
    Main execution function for T014b.
    
    Returns:
        Dictionary containing the result and status.
    """
    input_path = get_input_path()
    output_path = get_output_path()
    
    logger.info(f"Starting valid pair counter. Input: {input_path}")
    
    try:
        # Load studies
        studies = load_extracted_studies(input_path)
        logger.info(f"Loaded {len(studies)} studies from {input_path}")
        
        # Count valid pairs
        n_valid = count_valid_pairs(studies)
        logger.info(f"Found {n_valid} studies with valid (r, n) pairs")
        
        # Save result
        save_valid_pair_count(n_valid, output_path)
        
        # Determine status for gate logic
        if n_valid == 0:
            status = "data_insufficient"
            message = "No studies with valid (r, n) pairs found. Triggering 'Data Insufficient' mode."
        elif n_valid < 10:
            status = "narrative_fallback"
            message = f"Only {n_valid} studies with valid pairs (N < 10). Triggering narrative fallback."
        else:
            status = "quantitative_ready"
            message = f"Found {n_valid} valid pairs (N >= 10). Proceeding with quantitative analysis."
        
        logger.info(f"Status: {status} - {message}")
        
        return {
            "status": status,
            "N_valid": n_valid,
            "message": message,
            "output_file": str(output_path)
        }
        
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "N_valid": 0
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "N_valid": 0
        }

def main() -> int:
    """
    Entry point for the script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    result = run_valid_pair_counter()
    
    if result.get("status") == "error":
        print(f"ERROR: {result.get('error')}")
        return 1
    
    print(f"Completed successfully. N_valid: {result.get('N_valid')}")
    print(f"Status: {result.get('status')}")
    print(f"Output: {result.get('output_file')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
