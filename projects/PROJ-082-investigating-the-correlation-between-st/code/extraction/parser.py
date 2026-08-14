import csv
import json
import re
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from utils.logger import get_logger, log_error_context
from utils.config import get_project_root
from extraction.nlp_logic import extract_tract_descriptors
from extraction.p_value_converter import convert_p_value_to_effect_size

# Initialize logger
logger = get_logger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def load_tract_lexicon(lexicon_path: Optional[str] = None) -> Dict[str, Any]:
    """Load the tract lexicon from YAML or JSON file."""
    if lexicon_path is None:
        project_root = get_project_root()
        lexicon_path = project_root / "data" / "config" / "tract_lexicon.yaml"
    
    lexicon_path = Path(lexicon_path)
    if not lexicon_path.exists():
        logger.error(f"Tract lexicon not found at {lexicon_path}")
        raise FileNotFoundError(f"Tract lexicon not found at {lexicon_path}")
    
    try:
        # Try to load as YAML first
        import yaml
        with open(lexicon_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as yaml_error:
        try:
            # Fallback to JSON
            with open(lexicon_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as json_error:
            logger.error(f"Failed to load lexicon as YAML or JSON: {yaml_error}, {json_error}")
            raise

def log_exclusion(
    exclusion_log_path: Path,
    study_id: str,
    reason: str,
    original_value: str
) -> None:
    """Log an exclusion reason to the exclusion log CSV."""
    # Ensure directory exists
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = exclusion_log_path.exists()
    
    with open(exclusion_log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['study_id', 'reason', 'original_value'])
        writer.writerow([study_id, reason, original_value])
    
    logger.info(f"Logged exclusion: study_id={study_id}, reason={reason}")

def parse_row(
    row: Dict[str, Any],
    study_id: str,
    lexicon: Dict[str, Any],
    scheme: Dict[str, Any],
    exclusion_log_path: Path
) -> Tuple[Dict[str, Any], bool]:
    """
    Parse a single row from the input data.
    
    Returns:
        Tuple of (parsed_study_dict, is_valid_for_quantitative)
    """
    parsed = {
        'study_id': study_id,
        'author': row.get('author', ''),
        'year': row.get('year', None),
        'tract': row.get('tract', ''),
        'r': None,
        'n': None,
        'qualitative_desc': '',
        'narrative_pool': False,
        'exclusion_reason': None
    }
    
    is_valid_for_quantitative = False
    
    # Try to extract r and n directly
    r_val = row.get('r')
    n_val = row.get('n')
    
    # Handle r value
    if r_val is not None and r_val != '':
        try:
            parsed['r'] = float(r_val)
            if not (-1.0 <= parsed['r'] <= 1.0):
                log_exclusion(exclusion_log_path, study_id, "r_out_of_range", str(r_val))
                parsed['r'] = None
                parsed['exclusion_reason'] = "r_out_of_range"
        except (ValueError, TypeError):
            log_exclusion(exclusion_log_path, study_id, "r_invalid_format", str(r_val))
            parsed['r'] = None
            parsed['exclusion_reason'] = "r_invalid_format"
    else:
        # Check for p-value conversion
        p_val = row.get('p_value')
        if p_val is not None and p_val != '':
            try:
                p_float = float(p_val)
                if 0 < p_float < 1:
                    converted = convert_p_value_to_effect_size(p_float, n_val)
                    if converted and 'r' in converted:
                        parsed['r'] = converted['r']
                        parsed['n'] = n_val
                        is_valid_for_quantitative = True
                        parsed['exclusion_reason'] = "converted_from_p_value"
                    else:
                        log_exclusion(exclusion_log_path, study_id, "p_conversion_failed", str(p_val))
                        parsed['exclusion_reason'] = "p_conversion_failed"
                else:
                    log_exclusion(exclusion_log_path, study_id, "p_value_out_of_range", str(p_val))
                    parsed['exclusion_reason'] = "p_value_out_of_range"
            except (ValueError, TypeError):
                log_exclusion(exclusion_log_path, study_id, "p_value_invalid_format", str(p_val))
                parsed['exclusion_reason'] = "p_value_invalid_format"
        else:
            log_exclusion(exclusion_log_path, study_id, "r_missing", "null")
            parsed['exclusion_reason'] = "r_missing"
    
    # Handle n value
    if n_val is not None and n_val != '':
        try:
            parsed['n'] = int(n_val)
            if parsed['n'] <= 0:
                log_exclusion(exclusion_log_path, study_id, "n_non_positive", str(n_val))
                parsed['n'] = None
                if parsed['exclusion_reason'] is None:
                    parsed['exclusion_reason'] = "n_non_positive"
        except (ValueError, TypeError):
            log_exclusion(exclusion_log_path, study_id, "n_invalid_format", str(n_val))
            parsed['n'] = None
            if parsed['exclusion_reason'] is None:
                parsed['exclusion_reason'] = "n_invalid_format"
    else:
        log_exclusion(exclusion_log_path, study_id, "n_missing", "null")
        parsed['exclusion_reason'] = "n_missing"
    
    # Determine if valid for quantitative analysis
    if parsed['r'] is not None and parsed['n'] is not None and parsed['exclusion_reason'] != "r_missing" and parsed['exclusion_reason'] != "n_missing":
        is_valid_for_quantitative = True
    else:
        # If missing r or n, mark for narrative pool
        parsed['narrative_pool'] = True
        
        # Try to extract qualitative description
        desc = row.get('qualitative_desc')
        if desc and desc != '':
            parsed['qualitative_desc'] = desc
        else:
            # Try NLP extraction if tract is available
            tract = row.get('tract', '')
            if tract:
                try:
                    extracted_desc = extract_tract_descriptors(tract, lexicon, scheme)
                    if extracted_desc:
                        parsed['qualitative_desc'] = extracted_desc
                    else:
                        parsed['qualitative_desc'] = "no_descriptor_found"
                except Exception as e:
                    logger.warning(f"NLP extraction failed for study {study_id}: {e}")
                    parsed['qualitative_desc'] = "no_descriptor_found"
            else:
                parsed['qualitative_desc'] = "no_descriptor_found"
    
    return parsed, is_valid_for_quantitative

def parse_csv_file(
    input_path: Path,
    lexicon: Dict[str, Any],
    scheme: Dict[str, Any],
    exclusion_log_path: Path
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Parse a CSV input file.
    
    Returns:
        Tuple of (list of parsed studies, count of valid quantitative, count of narrative pool)
    """
    studies = []
    quantitative_count = 0
    narrative_count = 0
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            study_id = row.get('study_id', f"study_{idx}")
            parsed, is_valid = parse_row(row, study_id, lexicon, scheme, exclusion_log_path)
            studies.append(parsed)
            
            if is_valid:
                quantitative_count += 1
            else:
                narrative_count += 1
    
    return studies, quantitative_count, narrative_count

def parse_json_file(
    input_path: Path,
    lexicon: Dict[str, Any],
    scheme: Dict[str, Any],
    exclusion_log_path: Path
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Parse a JSON input file.
    
    Returns:
        Tuple of (list of parsed studies, count of valid quantitative, count of narrative pool)
    """
    studies = []
    quantitative_count = 0
    narrative_count = 0
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict) and 'studies' in data:
            rows = data['studies']
        else:
            rows = [data]
    
    for idx, row in enumerate(rows):
        study_id = row.get('study_id', f"study_{idx}")
        parsed, is_valid = parse_row(row, study_id, lexicon, scheme, exclusion_log_path)
        studies.append(parsed)
        
        if is_valid:
            quantitative_count += 1
        else:
            narrative_count += 1
    
    return studies, quantitative_count, narrative_count

def parse_input(
    input_path: Path,
    lexicon: Dict[str, Any],
    scheme: Dict[str, Any],
    exclusion_log_path: Path
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Parse input file (CSV or JSON).
    
    Returns:
        Tuple of (list of parsed studies, count of valid quantitative, count of narrative pool)
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    suffix = input_path.suffix.lower()
    
    if suffix == '.csv':
        return parse_csv_file(input_path, lexicon, scheme, exclusion_log_path)
    elif suffix == '.json':
        return parse_json_file(input_path, lexicon, scheme, exclusion_log_path)
    else:
        logger.error(f"Unsupported file format: {suffix}")
        raise ValueError(f"Unsupported file format: {suffix}")

def save_extracted_studies(
    studies: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """Save extracted studies to CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'study_id', 'author', 'year', 'tract', 'r', 'n',
        'qualitative_desc', 'narrative_pool', 'exclusion_reason'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(studies)
    
    logger.info(f"Saved {len(studies)} extracted studies to {output_path}")

def main():
    """Main entry point for the parser."""
    project_root = get_project_root()
    
    # Define paths
    input_path = project_root / "data" / "raw" / "studies.csv"
    lexicon_path = project_root / "data" / "config" / "tract_lexicon.yaml"
    methodology_path = project_root / "data" / "config" / "narrative_methodology.yaml"
    exclusion_log_path = project_root / "data" / "logs" / "exclusion_log.csv"
    output_path = project_root / "data" / "processed" / "extracted_studies.csv"
    
    # Ensure logs directory exists
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load lexicon
    logger.info(f"Loading tract lexicon from {lexicon_path}")
    lexicon = load_tract_lexicon(lexicon_path)
    
    # Load methodology scheme
    logger.info(f"Loading methodology from {methodology_path}")
    try:
        import yaml
        with open(methodology_path, 'r', encoding='utf-8') as f:
            scheme = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load methodology: {e}")
        scheme = {'keywords': [], 'sentiment_rules': {}, 'exclusion_criteria': []}
    
    # Parse input
    logger.info(f"Parsing input from {input_path}")
    try:
        studies, quant_count, narr_count = parse_input(
            input_path, lexicon, scheme, exclusion_log_path
        )
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        # Create empty output
        save_extracted_studies([], output_path)
        return
    
    # Save results
    save_extracted_studies(studies, output_path)
    
    logger.info(f"Extraction complete: {quant_count} quantitative, {narr_count} narrative pool")

if __name__ == "__main__":
    main()
