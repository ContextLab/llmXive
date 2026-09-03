"""
Qualitative Extraction (Narrative Path)
Task T012: Read data/raw/studies.csv and extract qualitative descriptors for rows
lacking both 'r' and 'n' using code/extraction/nlp_logic.py.
Writes data/processed/qualitative_data.json.
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from existing API surface
from extraction.nlp_logic import extract_tract_descriptors
from utils.config import get_project_root, ensure_directory
from utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)

def load_lexicon() -> Dict[str, Any]:
    """
    Load the tract lexicon from code/config/tract_lexicon.yaml.
    Returns a dictionary with 'tracts' and 'verbs' keys.
    """
    project_root = get_project_root()
    lexicon_path = project_root / "code" / "config" / "tract_lexicon.yaml"
    
    if not lexicon_path.exists():
        logger.error(f"Lexicon file not found: {lexicon_path}")
        raise FileNotFoundError(f"Lexicon file not found: {lexicon_path}")
    
    import yaml
    with open(lexicon_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_methodology() -> Dict[str, Any]:
    """
    Load the narrative methodology from data/config/narrative_methodology.yaml.
    Returns the configuration dictionary.
    """
    project_root = get_project_root()
    method_path = project_root / "data" / "config" / "narrative_methodology.yaml"
    
    if not method_path.exists():
        logger.error(f"Methodology file not found: {method_path}")
        raise FileNotFoundError(f"Methodology file not found: {method_path}")
    
    import yaml
    with open(method_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def extract_qualitative_descriptors(
    studies: List[Dict[str, Any]],
    lexicon: Dict[str, Any],
    scheme: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Extract qualitative descriptors for studies lacking both 'r' and 'n'.
    
    Args:
        studies: List of study dictionaries from the input CSV.
        lexicon: Tract lexicon dictionary.
        scheme: Narrative methodology scheme dictionary.
        
    Returns:
        List of dictionaries containing author, year, tract, and qualitative_desc.
    """
    results = []
    
    for study in studies:
        # Check if the study lacks both 'r' and 'n'
        r_val = study.get('r')
        n_val = study.get('n')
        
        # Treat None, empty string, or missing keys as missing
        has_r = r_val is not None and r_val != '' and str(r_val).strip() != ''
        has_n = n_val is not None and n_val != '' and str(n_val).strip() != ''
        
        if has_r or has_n:
            # Skip studies that have quantitative data
            continue
        
        # Extract qualitative description using NLP logic
        # We assume the study has some text field or we construct a text from available fields
        # For mock data, we might need to construct a placeholder text or use existing fields
        # Let's check if there's a 'text' or 'description' field, otherwise construct one
        text_to_analyze = study.get('text', study.get('description', ''))
        
        if not text_to_analyze:
            # If no text field, we might need to construct one from available fields
            # For now, let's skip if no text is available
            logger.debug(f"Skipping study {study.get('author', 'Unknown')}: no text to analyze")
            continue
        
        # Use the NLP logic to extract descriptors
        descriptor = extract_tract_descriptors(text_to_analyze, lexicon, scheme)
        
        if descriptor:
            result_entry = {
                'author': study.get('author', ''),
                'year': study.get('year', ''),
                'tract': study.get('tract', ''),
                'qualitative_desc': descriptor
            }
            results.append(result_entry)
            logger.info(f"Extracted qualitative descriptor for {study.get('author', 'Unknown')}: {descriptor}")
        else:
            logger.debug(f"No descriptor extracted for {study.get('author', 'Unknown')}")
    
    return results

def save_qualitative_data(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the extracted qualitative data to a JSON file.
    
    Args:
        data: List of extracted qualitative data dictionaries.
        output_path: Path to the output JSON file.
    """
    ensure_directory(output_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved qualitative data to {output_path}")

def run_extraction(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Main extraction workflow.
    
    Args:
        input_path: Path to input studies CSV. Defaults to data/raw/studies.csv.
        output_path: Path to output JSON. Defaults to data/processed/qualitative_data.json.
        
    Returns:
        List of extracted qualitative data dictionaries.
    """
    project_root = get_project_root()
    
    # Set default paths
    if input_path is None:
        input_path = project_root / "data" / "raw" / "studies.csv"
    if output_path is None:
        output_path = project_root / "data" / "processed" / "qualitative_data.json"
    
    # Validate input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load dependencies
    logger.info("Loading lexicon and methodology...")
    lexicon = load_lexicon()
    scheme = load_methodology()
    
    # Read input CSV
    logger.info(f"Reading input file: {input_path}")
    studies = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append(row)
    
    logger.info(f"Loaded {len(studies)} studies from {input_path}")
    
    # Extract qualitative descriptors
    logger.info("Extracting qualitative descriptors...")
    extracted_data = extract_qualitative_descriptors(studies, lexicon, scheme)
    
    logger.info(f"Extracted {len(extracted_data)} qualitative descriptors")
    
    # Save results
    save_qualitative_data(extracted_data, output_path)
    
    return extracted_data

def main() -> int:
    """
    Main entry point for the extraction script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        logger.info("Starting qualitative extraction (T012)...")
        run_extraction()
        logger.info("Qualitative extraction completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Qualitative extraction failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())