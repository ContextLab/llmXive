import csv
import json
import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

from utils.logger import get_logger
from extraction.nlp_logic import extract_tract_descriptors
from extraction.p_value_converter import convert_p_value_to_effect_size

logger = get_logger(__name__)

def load_tract_lexicon(lexicon_path: str) -> Dict[str, List[str]]:
    """Load the tract lexicon from a YAML file."""
    path = Path(lexicon_path)
    if not path.exists():
        raise FileNotFoundError(f"Lexicon file not found: {lexicon_path}")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def log_exclusion(study_id: str, reason: str, original_value: str, log_path: str) -> None:
    """Log an exclusion reason to the exclusion log CSV."""
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = log_file.exists() and log_file.stat().st_size > 0
    
    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['study_id', 'reason', 'original_value'])
        writer.writerow([study_id, reason, original_value])

def parse_row(row: Dict[str, Any], lexicon: Dict[str, List[str]], p_converter: Any) -> Dict[str, Any]:
    """
    Parse a single row from the input data.
    
    Logic:
    1. Try to extract 'r' and 'n' directly.
    2. If 'r' is missing but 'p' is present, try to convert 'p' to 'r'.
    3. If 'r' is still missing, attempt NLP extraction on text fields.
    4. Determine if the study belongs in the 'narrative_pool'.
    """
    study_id = row.get('id', row.get('author', 'Unknown'))
    result = {
        'author': row.get('author', ''),
        'year': row.get('year', ''),
        'tract': row.get('tract', ''),
        'r': None,
        'n': None,
        'qualitative_desc': '',
        'narrative_pool': False,
        'source': 'raw'
    }

    # 1. Direct Extraction
    r_val = row.get('r')
    n_val = row.get('n')
    p_val = row.get('p')
    text_field = row.get('notes', row.get('description', row.get('text', '')))

    # Parse numeric values
    if r_val is not None and r_val != '':
        try:
            result['r'] = float(r_val)
        except (ValueError, TypeError):
            result['r'] = None

    if n_val is not None and n_val != '':
        try:
            result['n'] = int(n_val)
        except (ValueError, TypeError):
            result['n'] = None

    # 2. P-value conversion if r is missing
    if result['r'] is None and p_val is not None and p_val != '':
        try:
            p_float = float(p_val)
            if 0 < p_float < 1:
                # Assuming a standard conversion logic exists in p_value_converter
                # We need to know 'n' for conversion, but if 'n' is also missing, we might skip or log.
                # For this task, we assume if we have p, we try to convert. If n is missing, we might not be able to get r.
                # The p_value_converter module likely handles this or we pass n if available.
                if result['n'] is not None:
                    converted = convert_p_value_to_effect_size(p_float, result['n'])
                    if converted:
                        result['r'] = converted['r']
                        result['source'] = 'p-conversion'
                        logger.info(f"Converted p-value to r for study {study_id}")
                else:
                    # Cannot convert p to r without n (degrees of freedom)
                    logger.warning(f"Cannot convert p-value to r for study {study_id}: missing 'n'")
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse p-value for study {study_id}: {e}")

    # 3. NLP Extraction if r is still missing or to populate qualitative_desc
    if not result['tract'] or not text_field:
        # If we don't have a specific tract from the row, we might skip NLP or try to find one.
        # The spec says: "search for tract names... in proximity to directional verbs".
        # If the row has a tract, use it. If not, we might iterate over known tracts?
        # For now, assume the row has a tract or we use the lexicon to find one in text.
        target_tract = result['tract']
        if not target_tract and text_field:
            # Try to find any tract from the lexicon in the text
            for tract in lexicon.get('tracts', []):
                if tract.lower() in text_field.lower():
                    target_tract = tract
                    break
        
        if target_tract and text_field:
            descriptors = extract_tract_descriptors(text_field, target_tract, lexicon)
            if descriptors:
                result['qualitative_desc'] = "; ".join(descriptors)
                result['source'] = 'nlp-extraction'
            else:
                result['qualitative_desc'] = text_field # Fallback to raw text if no descriptors found
        elif text_field:
            result['qualitative_desc'] = text_field

    # 4. Determine Narrative Pool Eligibility
    # "If no specific descriptors are found, EXCLUDE the study from the narrative_pool"
    # However, the task also says: "If 'r' or 'n' missing, exclude from quantitative pool; include in narrative pool."
    # Let's refine: 
    # - If we have a valid r and n, it's quantitative.
    # - If we have qualitative info (desc) but no r/n, it's narrative.
    # - If we have neither, it's excluded from both? Or just logged?
    # Task says: "If no specific descriptors are found, EXCLUDE the study from the narrative_pool"
    # AND "log the exclusion reason".
    
    has_effect_size = result['r'] is not None and result['n'] is not None
    has_qualitative = bool(result['qualitative_desc'])

    if has_effect_size:
        result['narrative_pool'] = False # It's quantitative
    elif has_qualitative:
        result['narrative_pool'] = True # It's narrative
    else:
        # No r/n and no qualitative descriptors found via NLP
        result['narrative_pool'] = False
        log_exclusion(
            study_id=str(study_id),
            reason="No effect size (r, n) and no qualitative descriptors found",
            original_value=str(row),
            log_path="data/logs/exclusion_log.csv"
        )

    return result

def parse_csv_file(input_path: str, lexicon: Dict[str, List[str]], p_converter: Any) -> List[Dict[str, Any]]:
    """Parse a CSV input file."""
    studies = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append(parse_row(row, lexicon, p_converter))
    return studies

def parse_json_file(input_path: str, lexicon: Dict[str, List[str]], p_converter: Any) -> List[Dict[str, Any]]:
    """Parse a JSON input file."""
    studies = []
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            for row in data:
                studies.append(parse_row(row, lexicon, p_converter))
        elif isinstance(data, dict):
            # Assume it's a single study or a dict of studies
            studies.append(parse_row(data, lexicon, p_converter))
    return studies

def parse_input(input_path: str, lexicon_path: str) -> List[Dict[str, Any]]:
    """Main entry point to parse input based on file extension."""
    lexicon = load_tract_lexicon(lexicon_path)
    # We don't need a specific p_converter instance for the logic here, 
    # as the function is imported and used directly.
    p_converter = None 

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    suffix = path.suffix.lower()
    if suffix == '.csv':
        return parse_csv_file(input_path, lexicon, p_converter)
    elif suffix == '.json':
        return parse_json_file(input_path, lexicon, p_converter)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

def save_extracted_studies(studies: List[Dict[str, Any]], output_path: str) -> None:
    """Save the extracted studies to a CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not studies:
        logger.warning("No studies to save. Creating empty file.")
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['author', 'year', 'tract', 'r', 'n', 'qualitative_desc', 'narrative_pool', 'source'])
        return

    fieldnames = ['author', 'year', 'tract', 'r', 'n', 'qualitative_desc', 'narrative_pool', 'source']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for study in studies:
            writer.writerow(study)

def main() -> None:
    """Main entry point for the parser."""
    import argparse
    parser = argparse.ArgumentParser(description="Parse study data for meta-analysis.")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV or JSON file.")
    parser.add_argument("--lexicon", type=str, default="data/config/tract_lexicon.yaml", help="Path to tract lexicon YAML.")
    parser.add_argument("--output", type=str, default="data/processed/extracted_studies.csv", help="Path to output CSV file.")
    
    args = parser.parse_args()
    
    logger.info(f"Starting extraction from {args.input}")
    try:
        studies = parse_input(args.input, args.lexicon)
        save_extracted_studies(studies, args.output)
        logger.info(f"Successfully extracted {len(studies)} studies to {args.output}")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
