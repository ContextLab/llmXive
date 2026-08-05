import csv
import json
import re
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

from utils.logger import get_logger
from extraction.nlp_logic import extract_tract_descriptors
from extraction.p_value_converter import convert_p_value_to_effect_size

logger = get_logger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LEXICON_PATH = PROJECT_ROOT / "data" / "config" / "tract_lexicon.yaml"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def load_tract_lexicon() -> Dict[str, List[str]]:
    """Load the tract lexicon from YAML."""
    if not LEXICON_PATH.exists():
        raise FileNotFoundError(f"Tract lexicon not found at {LEXICON_PATH}. "
                                "Run T007c to generate it.")
    with open(LEXICON_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def log_exclusion(study_id: str, reason: str, original_value: str) -> None:
    """Log an exclusion reason to data/logs/exclusion_log.csv."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / "exclusion_log.csv"
    
    file_exists = log_path.exists()
    
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['study_id', 'reason', 'original_value'])
        writer.writerow([study_id, reason, original_value])
    
    logger.info(f"Exclusion logged: {study_id} - {reason}")

def parse_row(row: Dict[str, Any], lexicon: Dict[str, List[str]], study_id: str) -> Dict[str, Any]:
    """
    Parse a single study row.
    
    Logic:
    1. Try to extract 'r' and 'n' directly.
    2. If 'p' is present but 'r' is missing, convert p to r.
    3. If 'tract' is missing but text is present, use NLP to find tract/descriptor.
    4. If no quantitative data (r, n) is found:
       - Mark as narrative_pool = True.
       - Set qualitative_desc based on NLP or "no_descriptor_found".
       - Log exclusion reason.
    5. If quantitative data found:
       - Mark as narrative_pool = False.
    """
    result = {
        'author': row.get('author', ''),
        'year': row.get('year', ''),
        'tract': row.get('tract', ''),
        'r': None,
        'n': row.get('n'),
        'qualitative_desc': None,
        'narrative_pool': False,
        'original_row': row
    }

    # 1. Direct extraction of r
    r_val = row.get('r')
    if r_val is not None:
        try:
            result['r'] = float(r_val)
        except (ValueError, TypeError):
            result['r'] = None

    # 2. Convert p-value if r is missing but p is present
    if result['r'] is None:
        p_val = row.get('p')
        if p_val is not None:
            try:
                converted = convert_p_value_to_effect_size(p_val)
                if converted is not None:
                    result['r'] = converted
                    logger.info(f"Converted p-value {p_val} to r={result['r']} for {study_id}")
            except Exception as e:
                logger.warning(f"Failed to convert p-value for {study_id}: {e}")

    # 3. NLP for tract/descriptor if missing
    text_input = row.get('qualitative_desc') or row.get('notes') or row.get('abstract', '')
    if not result['tract'] and text_input:
        # Try to find any tract in the lexicon within the text
        # For simplicity, we iterate lexicon keys (tracts)
        found_tract = None
        found_desc = []
        
        # Heuristic: Check if any known tract name appears in the text
        for tract_name in lexicon.get('tracts', []):
            if tract_name.lower() in text_input.lower():
                found_tract = tract_name
                # Extract descriptors for this tract
                descriptors = extract_tract_descriptors(text_input, tract_name, lexicon)
                if descriptors:
                    found_desc = descriptors
                break # Take the first match
        
        if found_tract:
            result['tract'] = found_tract
            result['qualitative_desc'] = "; ".join(found_desc)

    # 4. Determine narrative pool status
    if result['r'] is None or result['n'] is None:
        # Missing quantitative data -> Narrative Pool
        result['narrative_pool'] = True
        
        if not result['qualitative_desc']:
            result['qualitative_desc'] = "no_descriptor_found"
            log_exclusion(study_id, "missing_quantitative_data", f"r={row.get('r')}, n={row.get('n')}")
        else:
            log_exclusion(study_id, "missing_quantitative_data", f"r={row.get('r')}, n={row.get('n')}")
        
        logger.info(f"Study {study_id} added to narrative pool (missing r/n)")
    else:
        # Quantitative data present
        result['narrative_pool'] = False
        # If qualitative desc is still missing but we have r/n, we might still want to try NLP
        # to enrich the record, but it's not strictly required for the quantitative path.
        # However, the task says "If no specific descriptors are found... include in narrative_pool".
        # Since we have r/n, we are in the quantitative pool. We can still try to fill qualitative_desc.
        if not result['qualitative_desc'] and text_input:
            # Attempt to find descriptors without a specific tract first?
            # The NLP function requires a target_tract. If we don't have a tract, we can't call it easily.
            # We'll leave it as None or empty string.
            result['qualitative_desc'] = ""

    return result

def parse_csv_file(input_path: Path, lexicon: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """Parse a CSV file into a list of study records."""
    studies = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            study_id = row.get('id', f"row_{idx}")
            parsed = parse_row(row, lexicon, study_id)
            studies.append(parsed)
    return studies

def parse_json_file(input_path: Path, lexicon: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """Parse a JSON file into a list of study records."""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    studies = []
    if isinstance(data, list):
        for idx, row in enumerate(data):
            study_id = row.get('id', f"row_{idx}")
            parsed = parse_row(row, lexicon, study_id)
            studies.append(parsed)
    elif isinstance(data, dict) and 'studies' in data:
        for idx, row in enumerate(data['studies']):
            study_id = row.get('id', f"row_{idx}")
            parsed = parse_row(row, lexicon, study_id)
            studies.append(parsed)
    else:
        raise ValueError("JSON file must contain a list of studies or a dict with 'studies' key.")
    
    return studies

def parse_input(input_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Main entry point to parse input CSV or JSON."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    # Pre-flight check for dependencies
    if not LEXICON_PATH.exists():
        raise FileNotFoundError(f"Tract lexicon missing at {LEXICON_PATH}. Run T007c first.")
    
    lexicon = load_tract_lexicon()
    logger.info(f"Loaded tract lexicon from {LEXICON_PATH}")

    if path.suffix.lower() == '.csv':
        return parse_csv_file(path, lexicon)
    elif path.suffix.lower() in ['.json', '.yaml', '.yml']:
        # Handle JSON specifically for now as per task description
        if path.suffix.lower() == '.json':
            return parse_json_file(path, lexicon)
        else:
            # Fallback for YAML if needed, though task says CSV/JSON
            raise NotImplementedError("YAML input parsing not yet implemented for this task.")
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def save_extracted_studies(studies: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
    """Save extracted studies to a CSV file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['author', 'year', 'tract', 'r', 'n', 'qualitative_desc', 'narrative_pool']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for study in studies:
            # Ensure boolean is written as string or 0/1 for CSV compatibility
            row = study.copy()
            row['narrative_pool'] = 1 if row['narrative_pool'] else 0
            # Clean up None values for CSV
            for k, v in row.items():
                if v is None:
                    row[k] = ""
            writer.writerow(row)
    
    logger.info(f"Saved {len(studies)} extracted studies to {output_path}")

def main() -> None:
    """
    Main execution function for T013.
    Expects an input file path as argument or reads from config.
    For this task, we assume input is provided or we use a default mock path if testing.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse study data for meta-analysis")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV or JSON")
    parser.add_argument("--output", type=str, default=None, help="Path to output CSV (default: data/processed/extracted_studies.csv)")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else PROCESSED_DIR / "extracted_studies.csv"
    
    # Ensure output directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        studies = parse_input(input_path)
        save_extracted_studies(studies, output_path)
        logger.info("Extraction complete.")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
