"""
Parser module for extracting and merging study data.
Parses CSV/JSON inputs for r, n, tract and merges with qualitative data.
"""
import csv
import json
import re
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils.config import get_project_root
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def load_tract_lexicon() -> List[str]:
    """Load the tract lexicon from the config file."""
    lexicon_path = get_project_root() / "code" / "config" / "tract_lexicon.yaml"
    if not lexicon_path.exists():
        logger.warning(f"Tract lexicon not found at {lexicon_path}")
        return []
    
    import yaml
    with open(lexicon_path, 'r') as f:
        data = yaml.safe_load(f)
        return data.get('tracts', [])

def log_exclusion(row: Dict[str, Any], reason: str, exclusion_log_path: Path) -> None:
    """Log an excluded row to the exclusion log."""
    file_exists = exclusion_log_path.exists()
    
    with open(exclusion_log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['author', 'year', 'tract', 'reason'])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'author': row.get('author', ''),
            'year': row.get('year', ''),
            'tract': row.get('tract', ''),
            'reason': reason
        })

def parse_row(row: Dict[str, Any], tract_lexicon: List[str], qualitative_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse a single row from the input data.
    Returns a tuple of (parsed_row, exclusion_reason).
    If exclusion_reason is not None, the row should be excluded.
    """
    parsed = {}
    
    # Extract basic fields
    author = row.get('author', '').strip()
    year_str = row.get('year', '').strip()
    tract_raw = row.get('tract', '').strip()
    r_raw = row.get('r', '').strip()
    n_raw = row.get('n', '').strip()
    qualitative_desc = row.get('qualitative_desc', '').strip()
    narrative_pool = row.get('narrative_pool', False)
    
    # Validate author and year
    if not author:
        return None, "Missing author"
    
    try:
        year = int(year_str) if year_str else None
        if year is None:
            return None, "Missing or invalid year"
    except ValueError:
        return None, "Invalid year format"
    
    # Validate tract
    if not tract_raw:
        return None, "Missing tract"
    
    # Normalize tract name
    tract_normalized = tract_raw.lower()
    if tract_normalized not in [t.lower() for t in tract_lexicon]:
        # Check if it's close to any tract in the lexicon
        match = False
        for lex_tract in tract_lexicon:
            if lex_tract.lower() in tract_normalized or tract_normalized in lex_tract.lower():
                match = True
                break
        if not match:
            return None, f"Tract '{tract_raw}' not found in lexicon"
    
    parsed['author'] = author
    parsed['year'] = year
    parsed['tract'] = tract_raw
    
    # Process r and n
    r_val = None
    n_val = None
    
    if r_raw:
        try:
            r_val = float(r_raw)
            if not (-1.0 <= r_val <= 1.0):
                return None, f"r value {r_val} out of range [-1, 1]"
        except ValueError:
            return None, f"Invalid r value: {r_raw}"
    
    if n_raw:
        try:
            n_val = int(n_raw)
            if n_val <= 0:
                return None, f"n value {n_val} must be positive"
        except ValueError:
            return None, f"Invalid n value: {n_raw}"
    
    parsed['r'] = r_val
    parsed['n'] = n_val
    
    # Check for qualitative data
    if r_val is None and n_val is None:
        # Look for qualitative data in the qualitative_data dict
        key = f"{author}_{year}"
        if key in qualitative_data:
            parsed['qualitative_desc'] = qualitative_data[key].get('description', '')
            parsed['narrative_pool'] = True
        else:
            # Try to find a matching tract-based entry
            for q_key, q_val in qualitative_data.items():
                if q_val.get('tract', '').lower() == tract_normalized:
                    parsed['qualitative_desc'] = q_val.get('description', '')
                    parsed['narrative_pool'] = True
                    break
            else:
                # No qualitative data found, exclude
                return None, "Missing both r/n and qualitative description"
    else:
        parsed['qualitative_desc'] = qualitative_desc if qualitative_desc else ""
        parsed['narrative_pool'] = bool(narrative_pool) if isinstance(narrative_pool, bool) else False
    
    return parsed, None

def parse_csv_file(input_path: Path, tract_lexicon: List[str], qualitative_data: Dict[str, Any], exclusion_log_path: Path) -> List[Dict[str, Any]]:
    """Parse a CSV input file."""
    parsed_rows = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed, reason = parse_row(row, tract_lexicon, qualitative_data)
            if parsed is not None:
                parsed_rows.append(parsed)
            else:
                log_exclusion(row, reason, exclusion_log_path)
                logger.info(f"Excluded row: {row.get('author', 'Unknown')} - {reason}")
    
    return parsed_rows

def parse_json_file(input_path: Path, tract_lexicon: List[str], qualitative_data: Dict[str, Any], exclusion_log_path: Path) -> List[Dict[str, Any]]:
    """Parse a JSON input file."""
    parsed_rows = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Handle both list of dicts and dict with 'studies' key
    studies = data if isinstance(data, list) else data.get('studies', [])
    
    for row in studies:
        parsed, reason = parse_row(row, tract_lexicon, qualitative_data)
        if parsed is not None:
            parsed_rows.append(parsed)
        else:
            log_exclusion(row, reason, exclusion_log_path)
            logger.info(f"Excluded row: {row.get('author', 'Unknown')} - {reason}")
    
    return parsed_rows

def load_qualitative_data(qualitative_data_path: Path) -> Dict[str, Any]:
    """Load qualitative data from a JSON file."""
    if not qualitative_data_path.exists():
        logger.warning(f"Qualitative data file not found at {qualitative_data_path}")
        return {}
    
    with open(qualitative_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert list to dict for easier lookup
    result = {}
    if isinstance(data, list):
        for item in data:
            key = f"{item.get('author', '')}_{item.get('year', '')}"
            result[key] = item
    elif isinstance(data, dict):
        result = data
    
    return result

def save_extracted_studies(parsed_rows: List[Dict[str, Any]], output_path: Path) -> None:
    """Save parsed rows to a CSV file."""
    if not parsed_rows:
        logger.warning("No rows to save")
        # Create an empty file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['author', 'year', 'tract', 'r', 'n', 'qualitative_desc', 'narrative_pool']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['author', 'year', 'tract', 'r', 'n', 'qualitative_desc', 'narrative_pool']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in parsed_rows:
            writer.writerow(row)
    
    logger.info(f"Saved {len(parsed_rows)} rows to {output_path}")

def parse_input(input_path: Path, output_path: Path, exclusion_log_path: Path) -> None:
    """Main function to parse input and write extracted studies."""
    # Load tract lexicon
    tract_lexicon = load_tract_lexicon()
    if not tract_lexicon:
        logger.error("Tract lexicon is empty, cannot proceed")
        return
    
    # Load qualitative data
    qualitative_data_path = get_project_root() / "data" / "processed" / "qualitative_data.json"
    qualitative_data = load_qualitative_data(qualitative_data_path)
    
    # Determine input format and parse
    parsed_rows = []
    if input_path.suffix.lower() == '.csv':
        parsed_rows = parse_csv_file(input_path, tract_lexicon, qualitative_data, exclusion_log_path)
    elif input_path.suffix.lower() == '.json':
        parsed_rows = parse_json_file(input_path, tract_lexicon, qualitative_data, exclusion_log_path)
    else:
        logger.error(f"Unsupported input file format: {input_path.suffix}")
        return
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save extracted studies
    save_extracted_studies(parsed_rows, output_path)

def main() -> None:
    """Entry point for the parser script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Parse study data and extract relevant fields.')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV or JSON file')
    parser.add_argument('--output', type=str, required=True, help='Path to output CSV file')
    parser.add_argument('--exclusion-log', type=str, default=None, help='Path to exclusion log CSV file')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if args.exclusion_log:
        exclusion_log_path = Path(args.exclusion_log)
    else:
        # Default exclusion log path
        exclusion_log_path = get_project_root() / "data" / "logs" / "exclusion_log.csv"
    
    # Ensure log directory exists
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run parsing
    parse_input(input_path, output_path, exclusion_log_path)
    
    logger.info("Parsing complete")

if __name__ == '__main__':
    main()