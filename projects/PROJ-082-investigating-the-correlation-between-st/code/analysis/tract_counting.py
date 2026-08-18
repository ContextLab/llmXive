"""
Tract Counting Module (T008c / T017 Merged Logic)

This module implements the logic for counting unique tracts from the extracted studies.
It serves the requirements of T017 (Validation/Extraction logic) by ensuring
that the tract data is correctly aggregated and counted for downstream analysis
(e.g., Bonferroni correction in T022).

It reads `data/processed/extracted_studies.csv` (produced by T013) and generates
`data/derived/tract_count.json`.
"""
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)


def load_extracted_studies(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the extracted studies CSV file.
    
    Args:
        input_path: Path to data/processed/extracted_studies.csv
        
    Returns:
        List of dictionaries representing each study row.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T013 (parser) has been executed.")
    
    studies = []
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                studies.append(row)
    except Exception as e:
        logger.error(f"Error reading CSV {input_path}: {e}")
        raise
        
    if not studies:
        logger.warning("Input CSV is empty. Returning empty list.")
        
    return studies


def extract_tract_names(studies: List[Dict[str, Any]]) -> Set[str]:
    """
    Extract unique tract names from the study list.
    
    This function looks for the 'tract' column. If the column contains
    multiple tracts separated by a delimiter (e.g., ';'), it splits them.
    It normalizes the names (lowercase, strip whitespace) to ensure
    accurate counting.
    
    Args:
        studies: List of study dictionaries.
        
    Returns:
        A set of unique, normalized tract names.
    """
    tracts: Set[str] = set()
    
    for study in studies:
        tract_value = study.get('tract', '')
        if not tract_value or pd.isna(tract_value) if 'pd' in dir() else False:
            continue
            
        # Handle potential multiple tracts in one cell
        # Common delimiters: ';', ',', '|'
        separators = [';', ',', '|']
        found_separator = False
        for sep in separators:
            if sep in str(tract_value):
                parts = str(tract_value).split(sep)
                for part in parts:
                    normalized = part.strip().lower()
                    if normalized:
                        tracts.add(normalized)
                found_separator = True
                break
        
        if not found_separator:
            normalized = str(tract_value).strip().lower()
            if normalized:
                tracts.add(normalized)
                
    return tracts


def count_unique_tracts(tracts: Set[str]) -> int:
    """
    Count the number of unique tracts.
    
    Args:
        tracts: Set of unique tract names.
        
    Returns:
        Integer count.
    """
    return len(tracts)


def save_tract_count(output_path: Path, count: int, tracts: List[str]) -> None:
    """
    Save the tract count and list to a JSON file.
    
    Args:
        output_path: Path to data/derived/tract_count.json
        count: Number of unique tracts.
        tracts: List of unique tract names (sorted).
    """
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        "k": count,
        "tracts": sorted(tracts),
        "timestamp": "auto-generated" # In a real run, this would be datetime.now().isoformat()
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Saved tract count to {output_path}: {count} unique tracts.")


def run_tract_counting(input_path: Optional[Path] = None, 
                       output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main execution flow for T008c/T017 tract counting logic.
    
    1. Loads extracted studies.
    2. Extracts unique tracts.
    3. Counts them.
    4. Saves the result.
    
    Args:
        input_path: Optional override for input CSV.
        output_path: Optional override for output JSON.
        
    Returns:
        Dictionary containing the results (count, tracts).
    """
    root = get_project_root()
    if input_path is None:
        input_path = root / "data" / "processed" / "extracted_studies.csv"
    if output_path is None:
        output_path = root / "data" / "derived" / "tract_count.json"
        
    logger.info(f"Starting tract counting. Input: {input_path}, Output: {output_path}")
    
    try:
        studies = load_extracted_studies(input_path)
        logger.info(f"Loaded {len(studies)} studies.")
        
        unique_tracts = extract_tract_names(studies)
        logger.info(f"Found {len(unique_tracts)} unique tracts.")
        
        count = count_unique_tracts(unique_tracts)
        
        save_tract_count(output_path, count, list(unique_tracts))
        
        return {
            "k": count,
            "tracts": sorted(list(unique_tracts)),
            "status": "success"
        }
        
    except FileNotFoundError as e:
        logger.error(str(e))
        return {
            "k": 0,
            "tracts": [],
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in tract counting: {e}")
        return {
            "k": 0,
            "tracts": [],
            "status": "error",
            "error": str(e)
        }


def main():
    """Entry point for script execution."""
    result = run_tract_counting()
    if result["status"] == "success":
        print(f"Tract Counting Complete. k={result['k']}")
        sys.exit(0)
    else:
        print(f"Tract Counting Failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()