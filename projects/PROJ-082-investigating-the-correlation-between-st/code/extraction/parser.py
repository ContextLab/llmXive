import csv
import json
import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from utils.logger import get_logger, log_error_context
from utils.config import get_project_root, ensure_directory

logger = get_logger(__name__)

def load_tract_lexicon(lexicon_path: Optional[Path] = None) -> Dict[str, List[str]]:
    """Load the tract lexicon from YAML or return a default structure if not found."""
    if lexicon_path is None:
        lexicon_path = get_project_root() / "data" / "config" / "tract_lexicon.yaml"
    
    if not lexicon_path.exists():
        logger.warning(f"Tract lexicon not found at {lexicon_path}. Using empty defaults.")
        return {"tracts": [], "verbs": []}
    
    try:
        import yaml
        with open(lexicon_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {"tracts": [], "verbs": []}
    except Exception as e:
        logger.error(f"Failed to load tract lexicon: {e}")
        return {"tracts": [], "verbs": []}

def log_exclusion(study_id: str, reason: str, original_value: str, exclusion_log_path: Optional[Path] = None) -> None:
    """
    Log exclusion reasons to data/logs/exclusion_log.csv.
    Columns: study_id, reason, original_value.
    Creates the file and header if it does not exist.
    """
    if exclusion_log_path is None:
        exclusion_log_path = get_project_root() / "data" / "logs" / "exclusion_log.csv"
    
    ensure_directory(exclusion_log_path.parent)
    
    file_exists = exclusion_log_path.exists()
    
    with open(exclusion_log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['study_id', 'reason', 'original_value'])
        writer.writerow([study_id, reason, original_value])
    
    logger.info(f"Excluded study {study_id}: {reason}. Logged to {exclusion_log_path}")

def parse_row(row: Dict[str, Any], tract_lexicon: Dict[str, List[str]], exclusion_log_path: Optional[Path] = None) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Parse a single study row.
    Returns: (quantitative_record, narrative_record)
    
    Quantitative record is populated if 'r' and 'n' are valid numbers.
    If 'r' or 'n' is missing/invalid:
      - quantitative_record is None
      - Log exclusion to exclusion_log.csv
      - narrative_record is populated with available qualitative data (tract, qualitative_desc)
    """
    study_id = row.get('study_id', row.get('author', 'Unknown'))
    author = row.get('author', '')
    year = row.get('year', '')
    tract = row.get('tract', '')
    qualitative_desc = row.get('qualitative_desc', '')
    
    r_val = row.get('r')
    n_val = row.get('n')
    
    quantitative_record = None
    narrative_record = None
    
    # Check for quantitative validity
    r_valid = False
    n_valid = False
    r_val_float = None
    n_val_int = None
    
    if r_val is not None and r_val != '':
        try:
            r_val_float = float(r_val)
            if -1.0 <= r_val_float <= 1.0:
                r_valid = True
            else:
                logger.warning(f"Study {study_id}: r value {r_val_float} out of range [-1, 1].")
        except (ValueError, TypeError):
            logger.warning(f"Study {study_id}: Invalid r value '{r_val}'.")
    
    if n_val is not None and n_val != '':
        try:
            n_val_int = int(float(n_val)) # Handle "10.0" strings
            if n_val_int > 0:
                n_valid = True
            else:
                logger.warning(f"Study {study_id}: n value {n_val_int} must be positive.")
        except (ValueError, TypeError):
            logger.warning(f"Study {study_id}: Invalid n value '{n_val}'.")
    
    if r_valid and n_valid:
        # Valid quantitative data
        quantitative_record = {
            'author': author,
            'year': year,
            'tract': tract,
            'r': r_val_float,
            'n': n_val_int,
            'qualitative_desc': qualitative_desc,
            'narrative_pool': False, # Explicitly not in narrative pool if quantitative is valid
            'study_id': study_id
        }
    else:
        # Missing or invalid quantitative data
        reason_parts = []
        original_values = []
        
        if not r_valid:
            reason_parts.append("missing_or_invalid_r")
            original_values.append(str(r_val))
        if not n_valid:
            reason_parts.append("missing_or_invalid_n")
            original_values.append(str(n_val))
        
        reason = "; ".join(reason_parts)
        original_value = "; ".join(original_values)
        
        # Log the exclusion
        log_exclusion(study_id, reason, original_value, exclusion_log_path)
        
        # Prepare narrative record
        # If we have some qualitative info, include it. If completely empty, still include but flag.
        narrative_record = {
            'author': author,
            'year': year,
            'tract': tract,
            'r': None,
            'n': None,
            'qualitative_desc': qualitative_desc,
            'narrative_pool': True,
            'study_id': study_id,
            'exclusion_reason': reason
        }
        
        # If tract is missing too, we might still keep it for "No studies found" logic, 
        # but usually we need at least some identifier. The task says include in narrative pool.
        
    return quantitative_record, narrative_record

def parse_csv_file(input_path: Path, tract_lexicon: Optional[Dict[str, List[str]]] = None, exclusion_log_path: Optional[Path] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parse a CSV file. Returns (quantitative_list, narrative_list).
    """
    if tract_lexicon is None:
        tract_lexicon = load_tract_lexicon()
    
    quantitative_records = []
    narrative_records = []
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # Ensure study_id exists for logging
            if 'study_id' not in row:
                row['study_id'] = f"row_{i}"
            
            q_rec, n_rec = parse_row(row, tract_lexicon, exclusion_log_path)
            if q_rec:
                quantitative_records.append(q_rec)
            if n_rec:
                narrative_records.append(n_rec)
    
    return quantitative_records, narrative_records

def parse_json_file(input_path: Path, tract_lexicon: Optional[Dict[str, List[str]]] = None, exclusion_log_path: Optional[Path] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parse a JSON file (list of dicts). Returns (quantitative_list, narrative_list).
    """
    if tract_lexicon is None:
        tract_lexicon = load_tract_lexicon()
    
    quantitative_records = []
    narrative_records = []
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("JSON input must be a list of study records.")
    
    for i, row in enumerate(data):
        if 'study_id' not in row:
            row['study_id'] = f"row_{i}"
        
        q_rec, n_rec = parse_row(row, tract_lexicon, exclusion_log_path)
        if q_rec:
            quantitative_records.append(q_rec)
        if n_rec:
            narrative_records.append(n_rec)
    
    return quantitative_records, narrative_records

def parse_input(input_path: Path, tract_lexicon: Optional[Dict[str, List[str]]] = None, exclusion_log_path: Optional[Path] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Dispatch to CSV or JSON parser based on file extension.
    """
    if tract_lexicon is None:
        tract_lexicon = load_tract_lexicon()
    
    suffix = input_path.suffix.lower()
    if suffix == '.csv':
        return parse_csv_file(input_path, tract_lexicon, exclusion_log_path)
    elif suffix == '.json':
        return parse_json_file(input_path, tract_lexicon, exclusion_log_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

def save_extracted_studies(quantitative_records: List[Dict[str, Any]], narrative_records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Combine quantitative and narrative records into a single CSV.
    Narrative records will have r/n as None (or empty string if preferred, but None is safer for JSON).
    The 'narrative_pool' column indicates if the study was excluded from quantitative analysis.
    """
    ensure_directory(output_path.parent)
    
    all_records = []
    # Add quantitative records
    for rec in quantitative_records:
        all_records.append(rec)
    
    # Add narrative records (ensure they are distinct from quantitative)
    # The task says: "If 'r' or 'n' missing, exclude from quantitative pool; include in narrative pool."
    # So narrative_records are those that failed the r/n check.
    for rec in narrative_records:
        all_records.append(rec)
    
    if not all_records:
        logger.warning("No records to save. Creating empty CSV with headers.")
    
    fieldnames = ['study_id', 'author', 'year', 'tract', 'r', 'n', 'qualitative_desc', 'narrative_pool']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in all_records:
            # Ensure r and n are written as empty strings if None for CSV compatibility
            row = rec.copy()
            if row.get('r') is None:
                row['r'] = ''
            if row.get('n') is None:
                row['n'] = ''
            writer.writerow(row)
    
    logger.info(f"Saved {len(all_records)} extracted studies to {output_path}")

def main() -> None:
    """
    Entry point for parser script.
    Expected to be called by the pipeline orchestrator or run standalone with args.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse study data and handle missing effect sizes.")
    parser.add_argument('--input', type=str, required=True, help="Path to input CSV or JSON file.")
    parser.add_argument('--output', type=str, required=True, help="Path to output extracted studies CSV.")
    parser.add_argument('--lexicon', type=str, default=None, help="Path to tract lexicon YAML (optional).")
    parser.add_argument('--log-path', type=str, default=None, help="Path to exclusion log CSV (optional).")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    lexicon_path = Path(args.lexicon) if args.lexicon else None
    exclusion_log_path = Path(args.log_path) if args.log_path else None
    
    try:
        tract_lexicon = load_tract_lexicon(lexicon_path)
        q_records, n_records = parse_input(input_path, tract_lexicon, exclusion_log_path)
        save_extracted_studies(q_records, n_records, output_path)
        logger.info("Parsing completed successfully.")
    except Exception as e:
        logger.error(f"Error during parsing: {e}")
        raise

if __name__ == "__main__":
    main()