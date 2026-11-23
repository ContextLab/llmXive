"""
Parser and Converter for Study Data.

This module parses CSV/JSON inputs for r, n, tract, and merges with qualitative data.
It performs initial p-value to r conversion if r is missing but p or t is present.
It generates data/processed/extracted_studies.csv and logs exclusions to data/logs/exclusion_log.csv.
"""

import csv
import json
import logging
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from project utils
from utils.config import get_project_root
from utils.logger import get_logger

# Import from extraction module
from extraction.nlp_logic import extract_tract_descriptors

# Setup logging
logger = get_logger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    # Assuming the script is run from code/extraction/ or code/
    current_file = Path(__file__).resolve()
    # Go up two levels from code/extraction/parser.py to reach project root
    return current_file.parent.parent.parent

def load_tract_lexicon() -> List[str]:
    """Load the tract lexicon from the config file."""
    project_root = get_project_root()
    lexicon_path = project_root / "code" / "config" / "tract_lexicon.yaml"
    
    if not lexicon_path.exists():
        logger.warning(f"Tract lexicon not found at {lexicon_path}. Using default list.")
        return [
            "arcuate fasciculus",
            "cingulum bundle",
            "uncinate fasciculus",
            "inferior longitudinal fasciculus",
            "auditory cortex",
            "ventral striatum"
        ]
    
    try:
        import yaml
        with open(lexicon_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('tracts', [])
    except Exception as e:
        logger.error(f"Error loading tract lexicon: {e}")
        return []

def load_qualitative_data() -> Dict[str, Dict[str, Any]]:
    """Load qualitative data from the extracted JSON file."""
    project_root = get_project_root()
    qualitative_path = project_root / "data" / "processed" / "qualitative_data.json"
    
    if not qualitative_path.exists():
        logger.warning(f"Qualitative data not found at {qualitative_path}.")
        return {}
    
    try:
        with open(qualitative_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Convert list to dict for easy lookup by (author, year)
            result = {}
            for item in data:
                key = f"{item.get('author', '')}_{item.get('year', '')}"
                result[key] = item
            return result
    except Exception as e:
        logger.error(f"Error loading qualitative data: {e}")
        return {}

def p_to_t(p_value: float, df: int) -> float:
    """Convert p-value to t-statistic (two-tailed)."""
    if p_value <= 0 or p_value >= 1:
        raise ValueError("p-value must be between 0 and 1 (exclusive)")
    if df <= 0:
        raise ValueError("Degrees of freedom must be positive")
    
    # Use scipy if available, otherwise approximate
    try:
        from scipy.stats import t
        return t.ppf(1 - p_value / 2, df)
    except ImportError:
        logger.warning("scipy not available. Using approximation for p-to-t conversion.")
        # Simple approximation for large df
        return math.sqrt(df) * (1 - p_value)  # Very rough approximation

def t_to_r(t: float, df: int) -> float:
    """Convert t-statistic to correlation coefficient r."""
    if df <= 0:
        raise ValueError("Degrees of freedom must be positive")
    
    # r = t / sqrt(t^2 + df)
    r = t / math.sqrt(t**2 + df)
    return r

def convert_p_to_r(p_value: float, n: int) -> float:
    """Convert p-value to r using t-statistic conversion."""
    if p_value <= 0 or p_value >= 1:
        raise ValueError("p-value must be between 0 and 1 (exclusive)")
    if n <= 2:
        raise ValueError("Sample size must be > 2 for correlation")
    
    df = n - 2
    t = p_to_t(p_value, df)
    r = t_to_r(t, df)
    return r

def parse_row(row: Dict[str, str], qualitative_data: Dict[str, Dict[str, Any]], tract_lexicon: List[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse a single row from the input data.
    
    Returns:
        Tuple of (parsed_row_dict, exclusion_reason)
        If parsed_row is None, the row should be excluded.
    """
    parsed = {}
    exclusion_reason = None
    
    # Extract basic fields
    author = row.get('author', '').strip()
    year_str = row.get('year', '').strip()
    tract = row.get('tract', '').strip()
    r_str = row.get('r', '').strip()
    n_str = row.get('n', '').strip()
    p_str = row.get('p', '').strip()
    t_str = row.get('t', '').strip()
    qualitative_desc = row.get('qualitative_desc', '').strip()
    
    # Validate basic fields
    if not author or not year_str:
        return None, "Missing author or year"
    
    try:
        year = int(year_str)
    except ValueError:
        return None, f"Invalid year: {year_str}"
    
    if not tract:
        return None, "Missing tract name"
    
    # Check if tract is in lexicon (optional validation)
    tract_lower = tract.lower()
    if tract_lexicon and not any(lex.lower() in tract_lower for lex in tract_lexicon):
        logger.warning(f"Tract '{tract}' not found in lexicon. Continuing anyway.")
    
    parsed['author'] = author
    parsed['year'] = year
    parsed['tract'] = tract
    parsed['narrative_pool'] = False
    parsed['conversion_method'] = None
    
    # Handle r and n
    r_val = None
    n_val = None
    
    if r_str:
        try:
            r_val = float(r_str)
            if not (-1 <= r_val <= 1):
                return None, f"r value out of range: {r_val}"
        except ValueError:
            return None, f"Invalid r value: {r_str}"
    
    if n_str:
        try:
            n_val = int(n_str)
            if n_val <= 0:
                return None, f"n must be positive: {n_val}"
        except ValueError:
            return None, f"Invalid n value: {n_str}"
    
    # Handle p and t conversion if r is missing
    if r_val is None:
        if p_str:
            try:
                p_val = float(p_str)
                if n_val is None:
                    return None, "p-value present but n missing for conversion"
                r_val = convert_p_to_r(p_val, n_val)
                parsed['conversion_method'] = 'p_to_r'
                logger.info(f"Converted p={p_val} to r={r_val:.4f} for {author} ({year})")
            except ValueError:
                return None, f"Invalid p value: {p_str}"
            except Exception as e:
                return None, f"Error converting p to r: {e}"
        elif t_str:
            if n_val is None:
                return None, "t-statistic present but n missing for conversion"
            try:
                t_val = float(t_str)
                df = n_val - 2
                r_val = t_to_r(t_val, df)
                parsed['conversion_method'] = 't_to_r'
                logger.info(f"Converted t={t_val} to r={r_val:.4f} for {author} ({year})")
            except ValueError:
                return None, f"Invalid t value: {t_str}"
            except Exception as e:
                return None, f"Error converting t to r: {e}"
        else:
            # No r, p, or t - check qualitative data
            key = f"{author}_{year}"
            if key in qualitative_data:
                qual_entry = qualitative_data[key]
                parsed['qualitative_desc'] = qual_entry.get('qualitative_desc', '')
                parsed['narrative_pool'] = True
                logger.info(f"Using qualitative data for {author} ({year})")
            else:
                return None, "No r, p, t, or qualitative data available"
    
    parsed['r'] = r_val
    parsed['n'] = n_val
    
    # If we still don't have n, and we have qualitative data, that's okay
    if n_val is None and parsed['narrative_pool']:
        logger.info(f"Row for {author} ({year}) is narrative-only, no n value")
    
    return parsed, None

def parse_csv_file(input_path: Path, qualitative_data: Dict[str, Dict[str, Any]], tract_lexicon: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parse a CSV input file."""
    parsed_rows = []
    exclusions = []
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                parsed, reason = parse_row(row, qualitative_data, tract_lexicon)
                if parsed:
                    parsed_rows.append(parsed)
                else:
                    exclusions.append({
                        'row': row_num,
                        'reason': reason,
                        'data': row
                    })
                    logger.warning(f"Row {row_num} excluded: {reason}")
    except Exception as e:
        logger.error(f"Error parsing CSV file {input_path}: {e}")
        raise
    
    return parsed_rows, exclusions

def parse_json_file(input_path: Path, qualitative_data: Dict[str, Dict[str, Any]], tract_lexicon: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parse a JSON input file."""
    parsed_rows = []
    exclusions = []
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                for idx, row in enumerate(data, start=1):
                    parsed, reason = parse_row(row, qualitative_data, tract_lexicon)
                    if parsed:
                        parsed_rows.append(parsed)
                    else:
                        exclusions.append({
                            'row': idx,
                            'reason': reason,
                            'data': row
                        })
                        logger.warning(f"Row {idx} excluded: {reason}")
            else:
                # Single object
                parsed, reason = parse_row(data, qualitative_data, tract_lexicon)
                if parsed:
                    parsed_rows.append(parsed)
                else:
                    exclusions.append({
                        'row': 1,
                        'reason': reason,
                        'data': data
                    })
                    logger.warning(f"Row 1 excluded: {reason}")
    except Exception as e:
        logger.error(f"Error parsing JSON file {input_path}: {e}")
        raise
    
    return parsed_rows, exclusions

def save_extracted_studies(parsed_rows: List[Dict[str, Any]], output_path: Path):
    """Save parsed studies to CSV."""
    if not parsed_rows:
        logger.warning("No parsed rows to save. Creating empty CSV with headers.")
        # Create empty file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['author', 'year', 'tract', 'r', 'n', 'narrative_pool', 'qualitative_desc', 'conversion_method']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['author', 'year', 'tract', 'r', 'n', 'narrative_pool', 'qualitative_desc', 'conversion_method']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in parsed_rows:
            # Ensure all fields are present
            output_row = {
                'author': row.get('author', ''),
                'year': row.get('year', ''),
                'tract': row.get('tract', ''),
                'r': row.get('r', ''),
                'n': row.get('n', ''),
                'narrative_pool': row.get('narrative_pool', False),
                'qualitative_desc': row.get('qualitative_desc', ''),
                'conversion_method': row.get('conversion_method', '')
            }
            writer.writerow(output_row)
    
    logger.info(f"Saved {len(parsed_rows)} studies to {output_path}")

def log_exclusion(exclusions: List[Dict[str, Any]], log_path: Path):
    """Log excluded rows to CSV."""
    if not exclusions:
        logger.info("No exclusions to log.")
        return
    
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['row', 'reason', 'data']
    
    with open(log_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for exclusion in exclusions:
            writer.writerow(exclusion)
    
    logger.info(f"Logged {len(exclusions)} exclusions to {log_path}")

def parse_input(input_path: Path, qualitative_data_path: Optional[Path] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Main entry point for parsing input data.
    
    Args:
        input_path: Path to input CSV or JSON file
        qualitative_data_path: Optional path to qualitative data JSON (if not using default location)
    
    Returns:
        Tuple of (parsed_rows, exclusions)
    """
    project_root = get_project_root()
    
    # Load tract lexicon
    tract_lexicon = load_tract_lexicon()
    logger.info(f"Loaded {len(tract_lexicon)} tracts from lexicon")
    
    # Load qualitative data
    if qualitative_data_path:
        qualitative_data_path = Path(qualitative_data_path)
    else:
        qualitative_data_path = project_root / "data" / "processed" / "qualitative_data.json"
    
    qualitative_data = load_qualitative_data()
    logger.info(f"Loaded {len(qualitative_data)} qualitative entries")
    
    # Parse input file
    parsed_rows = []
    exclusions = []
    
    if not input_path.exists():
        logger.warning(f"Input file not found: {input_path}. Creating empty output.")
        # Return empty results
        return parsed_rows, exclusions
    
    if input_path.suffix.lower() == '.csv':
        parsed_rows, exclusions = parse_csv_file(input_path, qualitative_data, tract_lexicon)
    elif input_path.suffix.lower() == '.json':
        parsed_rows, exclusions = parse_json_file(input_path, qualitative_data, tract_lexicon)
    else:
        raise ValueError(f"Unsupported input file format: {input_path.suffix}")
    
    return parsed_rows, exclusions

def main():
    """Main function to run the parser."""
    project_root = get_project_root()
    
    # Setup paths
    input_path = project_root / "data" / "raw" / "studies.csv"
    output_path = project_root / "data" / "processed" / "extracted_studies.csv"
    exclusion_log_path = project_root / "data" / "logs" / "exclusion_log.csv"
    
    # Ensure directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting parser and converter...")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Exclusion log: {exclusion_log_path}")
    
    try:
        # Parse input
        parsed_rows, exclusions = parse_input(input_path)
        
        # Save results
        save_extracted_studies(parsed_rows, output_path)
        log_exclusion(exclusions, exclusion_log_path)
        
        logger.info("Parser and converter completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Parser and converter failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())