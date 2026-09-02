"""
Parser module for extracting and merging study data.

This module parses CSV/JSON inputs for r, n, tract and merges with qualitative
data from T012. It generates data/processed/extracted_studies.csv with columns
including narrative_pool and qualitative_desc. It also logs exclusions to
data/logs/exclusion_log.csv.
"""
import csv
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from utils.config as per API surface
from utils.config import get_project_root, ensure_directory

# Configure logger
logger = logging.getLogger(__name__)

def load_tract_lexicon(lexicon_path: Optional[str] = None) -> List[str]:
    """
    Load the tract lexicon from YAML or default path.
    
    Args:
        lexicon_path: Path to lexicon file. If None, uses default path.
        
    Returns:
        List of tract names.
    """
    if lexicon_path is None:
        project_root = get_project_root()
        lexicon_path = project_root / "code" / "config" / "tract_lexicon.yaml"
    
    try:
        import yaml
        with open(lexicon_path, 'r') as f:
            data = yaml.safe_load(f)
            # The lexicon structure depends on how generate_lexicon.py writes it.
            # Based on T007c, it likely contains a list of tracts.
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'tracts' in data:
                return data['tracts']
            else:
                # Fallback: try to extract keys if it's a dict of tracts
                return list(data.keys())
    except FileNotFoundError:
        logger.warning(f"Lexicon file not found at {lexicon_path}. Using empty list.")
        return []
    except Exception as e:
        logger.error(f"Error loading lexicon: {e}")
        return []

def load_qualitative_data(qualitative_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Load qualitative data from JSON.
    
    Args:
        qualitative_path: Path to qualitative data JSON. If None, uses default path.
        
    Returns:
        Dictionary mapping study identifiers to qualitative data.
    """
    if qualitative_path is None:
        project_root = get_project_root()
        qualitative_path = project_root / "data" / "processed" / "qualitative_data.json"
    
    try:
        with open(qualitative_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Qualitative data file not found at {qualitative_path}. Returning empty dict.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding qualitative data JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading qualitative data: {e}")
        return {}

def parse_row(row: Dict[str, str], lexicon: List[str], qualitative_data: Dict[str, Dict[str, Any]], study_id: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Parse a single row from the input CSV.
    
    Args:
        row: Dictionary representing a CSV row.
        lexicon: List of tract names.
        qualitative_data: Dictionary of qualitative data.
        study_id: Unique identifier for the study (e.g., author_year).
        
    Returns:
        Tuple of (parsed_record, exclusion_reason).
    """
    parsed = {}
    exclusion_reason = None

    # Extract basic fields
    parsed['author'] = row.get('author', '').strip()
    parsed['year'] = row.get('year', '').strip()
    parsed['tract'] = row.get('tract', '').strip()
    
    # Parse r and n, handling missing values
    r_str = row.get('r', '').strip()
    n_str = row.get('n', '').strip()
    
    parsed['r'] = None
    parsed['n'] = None
    
    if r_str:
        try:
            parsed['r'] = float(r_str)
        except ValueError:
            logger.warning(f"Invalid r value '{r_str}' for study {study_id}. Setting to None.")
            parsed['r'] = None
            
    if n_str:
        try:
            parsed['n'] = int(n_str)
        except ValueError:
            logger.warning(f"Invalid n value '{n_str}' for study {study_id}. Setting to None.")
            parsed['n'] = None

    # Determine if qualitative extraction is needed
    # "This logic MUST ONLY be applied to studies that lack both r and n values."
    if parsed['r'] is None and parsed['n'] is None:
        parsed['narrative_pool'] = True
        # Look up qualitative description
        qual_entry = qualitative_data.get(study_id, {})
        parsed['qualitative_desc'] = qual_entry.get('description', '')
        parsed['extraction_method'] = qual_entry.get('method', 'unknown')
        
        # If no qualitative data found, mark for exclusion
        if not parsed['qualitative_desc']:
            exclusion_reason = "Missing both r and n, and no qualitative description found"
    else:
        parsed['narrative_pool'] = False
        parsed['qualitative_desc'] = ''
        parsed['extraction_method'] = 'quantitative'

    # Validate tract name against lexicon (optional, for logging)
    if parsed['tract'] and lexicon:
        tract_lower = parsed['tract'].lower()
        found = any(tract.lower() in tract_lower or tract_lower in tract.lower() for tract in lexicon)
        if not found:
            logger.warning(f"Tract '{parsed['tract']}' not found in lexicon for study {study_id}.")

    return parsed, exclusion_reason

def parse_csv_file(input_path: Path, lexicon: List[str], qualitative_data: Dict[str, Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parse a CSV file and extract study records.
    
    Args:
        input_path: Path to input CSV file.
        lexicon: List of tract names.
        qualitative_data: Dictionary of qualitative data.
        
    Returns:
        Tuple of (parsed_records, excluded_records).
    """
    parsed_records = []
    excluded_records = []

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            # Create a unique study ID
            study_id = f"{row.get('author', 'unknown')}_{row.get('year', 'unknown')}"
            
            parsed, exclusion_reason = parse_row(row, lexicon, qualitative_data, study_id)
            
            if exclusion_reason:
                excluded_records.append({
                    'study_id': study_id,
                    'row_index': idx + 1,  # 1-based index
                    'reason': exclusion_reason,
                    'raw_data': row
                })
            else:
                parsed_records.append(parsed)

    return parsed_records, excluded_records

def parse_json_file(input_path: Path, lexicon: List[str], qualitative_data: Dict[str, Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parse a JSON file and extract study records.
    
    Args:
        input_path: Path to input JSON file.
        lexicon: List of tract names.
        qualitative_data: Dictionary of qualitative data.
        
    Returns:
        Tuple of (parsed_records, excluded_records).
    """
    parsed_records = []
    excluded_records = []

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {input_path}: {e}")
        return [], []

    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and 'studies' in data:
        records = data['studies']
    else:
        logger.warning(f"Unexpected JSON structure in {input_path}. Assuming root is list of studies.")
        records = [data] if isinstance(data, dict) else []

    for idx, row in enumerate(records):
        study_id = f"{row.get('author', 'unknown')}_{row.get('year', 'unknown')}"
        parsed, exclusion_reason = parse_row(row, lexicon, qualitative_data, study_id)
        
        if exclusion_reason:
            excluded_records.append({
                'study_id': study_id,
                'row_index': idx + 1,
                'reason': exclusion_reason,
                'raw_data': row
            })
        else:
            parsed_records.append(parsed)

    return parsed_records, excluded_records

def save_extracted_studies(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save extracted studies to a CSV file.
    
    Args:
        records: List of parsed study records.
        output_path: Path to output CSV file.
    """
    ensure_directory(output_path)
    
    fieldnames = [
        'author', 'year', 'tract', 'r', 'n', 
        'narrative_pool', 'qualitative_desc', 'extraction_method'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record)
    
    logger.info(f"Saved {len(records)} records to {output_path}")

def log_exclusion(excluded_records: List[Dict[str, Any]], log_path: Path) -> None:
    """
    Log excluded records to a CSV file.
    
    Args:
        excluded_records: List of excluded study records.
        log_path: Path to log CSV file.
    """
    ensure_directory(log_path)
    
    if not excluded_records:
        # Write an empty file with headers if no exclusions
        with open(log_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['study_id', 'row_index', 'reason', 'raw_data'])
            writer.writeheader()
        logger.info(f"No exclusions. Created empty log at {log_path}")
        return

    fieldnames = ['study_id', 'row_index', 'reason', 'raw_data']
    
    with open(log_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in excluded_records:
            # Convert raw_data dict to JSON string for CSV
            record['raw_data'] = json.dumps(record['raw_data'])
            writer.writerow(record)
    
    logger.info(f"Logged {len(excluded_records)} exclusions to {log_path}")

def parse_input(input_path: str, output_csv_path: str, exclusion_log_path: str) -> Dict[str, int]:
    """
    Main entry point for parsing input data.
    
    Args:
        input_path: Path to input CSV or JSON file.
        output_csv_path: Path to output extracted studies CSV.
        exclusion_log_path: Path to exclusion log CSV.
        
    Returns:
        Dictionary with counts of processed and excluded records.
    """
    project_root = get_project_root()
    input_path_obj = Path(input_path)
    output_path_obj = Path(output_csv_path)
    log_path_obj = Path(exclusion_log_path)

    # Load dependencies
    lexicon = load_tract_lexicon()
    qualitative_data = load_qualitative_data()

    logger.info(f"Starting parsing from {input_path_obj}")
    logger.info(f"Loaded {len(lexicon)} tracts from lexicon")
    logger.info(f"Loaded {len(qualitative_data)} qualitative entries")

    # Determine file type and parse
    if input_path_obj.suffix.lower() == '.csv':
        records, excluded = parse_csv_file(input_path_obj, lexicon, qualitative_data)
    elif input_path_obj.suffix.lower() == '.json':
        records, excluded = parse_json_file(input_path_obj, lexicon, qualitative_data)
    else:
        raise ValueError(f"Unsupported file format: {input_path_obj.suffix}")

    # Save outputs
    save_extracted_studies(records, output_path_obj)
    log_exclusion(excluded, log_path_obj)

    return {
        'processed': len(records),
        'excluded': len(excluded)
    }

def main() -> int:
    """
    Command-line entry point for the parser script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    import argparse

    parser = argparse.ArgumentParser(description='Parse and merge study data.')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV or JSON file.')
    parser.add_argument('--output', type=str, default='data/processed/extracted_studies.csv', help='Path to output CSV file.')
    parser.add_argument('--log', type=str, default='data/logs/exclusion_log.csv', help='Path to exclusion log CSV file.')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging.')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        results = parse_input(args.input, args.output, args.log)
        logger.info(f"Parsing complete. Processed: {results['processed']}, Excluded: {results['excluded']}")
        return 0
    except Exception as e:
        logger.error(f"Error during parsing: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())