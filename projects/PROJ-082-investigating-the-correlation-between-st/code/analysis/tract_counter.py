"""
Tract Counter (Task T008c).

Reads extracted_studies.csv and counts distinct tracts.
Output: data/derived/tract_count.json

Constraint: If input missing or empty, write {"k": 0}.
"""
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Set, Optional, Dict, Any

def get_input_path() -> Path:
    """Return the path to the extracted studies CSV."""
    return Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "extracted_studies.csv"

def get_output_path() -> Path:
    """Return the path to the output tract count JSON."""
    return Path(__file__).resolve().parent.parent.parent / "data" / "derived" / "tract_count.json"

def load_extracted_studies(path: Path) -> list:
    """
    Load the extracted studies from a CSV file.
    
    Args:
        path: Path to the CSV file.
        
    Returns:
        List of dictionaries representing the studies.
        Returns an empty list if the file does not exist.
    """
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def extract_tract_names(studies: list) -> Set[str]:
    """
    Extract unique tract names from the list of studies.
    
    Args:
        studies: List of study dictionaries.
        
    Returns:
        A set of unique, lowercased tract names.
    """
    tracts = set()
    for study in studies:
        # Check for 'tract_name' or 'tract' depending on schema variations
        tract = study.get('tract_name', '').strip() or study.get('tract', '').strip()
        if tract:
            tracts.add(tract.lower())
    return tracts

def count_unique_tracts(tracts: Set[str]) -> int:
    """
    Count the number of unique tracts.
    
    Args:
        tracts: Set of tract names.
        
    Returns:
        Integer count of unique tracts.
    """
    return len(tracts)

def save_tract_count(count: int, path: Path) -> None:
    """
    Save the tract count to a JSON file.
    
    Args:
        count: The integer count of unique tracts.
        path: Output file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    result = {"k": count}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

def run_tract_counter() -> int:
    """
    Main execution logic for the tract counter.
    
    Reads the extracted studies, counts unique tracts, and writes the result.
    If the input file is missing or empty, writes {"k": 0} and logs a warning.
    
    Returns:
        Exit code (0 for success).
    """
    # Configure logging for this script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("tract_counter")
    
    input_path = get_input_path()
    output_path = get_output_path()
    
    # Check if input exists
    if not input_path.exists():
        logger.warning(f"Input file not found: {input_path}. Writing k=0.")
        save_tract_count(0, output_path)
        return 0
    
    # Load data
    studies = load_extracted_studies(input_path)
    if not studies:
        logger.warning(f"Input file {input_path} exists but contains no data rows. Writing k=0.")
        save_tract_count(0, output_path)
        return 0
    
    # Process
    tracts = extract_tract_names(studies)
    k = count_unique_tracts(tracts)
    
    # Save output
    save_tract_count(k, output_path)
    logger.info(f"Distinct tracts counted: {k}")
    logger.info(f"Output written to: {output_path}")
    
    return 0

def main() -> int:
    """Entry point for the script."""
    return run_tract_counter()

if __name__ == "__main__":
    sys.exit(main())