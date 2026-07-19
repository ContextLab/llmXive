"""
Study Counter Module (T014a)

Reads the extracted studies CSV produced by T013, counts unique (Author, Year) pairs,
and writes the result to data/processed/study_count.json.

This task MUST run regardless of the value of N.
"""
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Import local utilities from the project structure
from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

INPUT_FILE = "data/processed/extracted_studies.csv"
OUTPUT_FILE = "data/processed/study_count.json"

def load_extracted_studies(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the extracted studies CSV file.
    
    Args:
        input_path: Path to the CSV file.
        
    Returns:
        List of study dictionaries.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    studies = []
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                studies.append(row)
    except Exception as e:
        logger.error(f"Failed to read CSV {input_path}: {e}")
        raise
    
    if not studies:
        logger.warning(f"Input file {input_path} is empty.")
    
    return studies

def count_unique_studies(studies: List[Dict[str, Any]]) -> int:
    """
    Count unique (Author, Year) pairs from the list of studies.
    
    Args:
        studies: List of study dictionaries.
        
    Returns:
        The count of unique studies.
    """
    unique_pairs: Set[Tuple[str, str]] = set()
    
    for study in studies:
        # Handle potential missing keys gracefully
        author = study.get('Author', '').strip()
        year = study.get('Year', '').strip()
        
        if not author:
            logger.warning(f"Skipping study with missing Author: {study}")
            continue
        
        if not year:
            logger.warning(f"Skipping study with missing Year: {study}")
            continue
        
        unique_pairs.add((author, year))
    
    return len(unique_pairs)

def save_study_count(n: int, output_path: Path) -> None:
    """
    Save the study count to a JSON file.
    
    Args:
        n: The count of unique studies.
        output_path: Path to the output JSON file.
    """
    result = {"N": n}
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved study count: N={n} to {output_path}")

def run_study_counter() -> int:
    """
    Main execution logic for the study counter.
    
    Returns:
        The calculated study count N.
    """
    root = get_project_root()
    input_path = root / INPUT_FILE
    output_path = root / OUTPUT_FILE
    
    logger.info(f"Starting study counter. Input: {input_path}")
    
    # Load data
    studies = load_extracted_studies(input_path)
    
    # Count unique studies
    n = count_unique_studies(studies)
    
    # Save result
    save_study_count(n, output_path)
    
    return n

def main() -> None:
    """Entry point for the study counter script."""
    try:
        n = run_study_counter()
        print(f"Study count completed. N = {n}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Study counter failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
