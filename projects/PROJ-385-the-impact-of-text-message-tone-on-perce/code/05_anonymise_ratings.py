"""
Anonymise real ratings data.

Reads data/raw/real_ratings.csv, hashes Prolific IDs and strips PII,
and writes the result to data/processed/anonymised_ratings.csv.

Verification: The output file contains no raw Prolific IDs.
"""
import csv
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import project configuration
sys.path.insert(0, str(Path(__file__).parent))
from config import get_raw_data_dir, get_processed_data_dir
from logging_config import setup_logging, get_logger

def hash_prolific_id(prolific_id: str, salt: str = "llmXive_project_salt") -> str:
    """
    Hash a Prolific ID to anonymise it.
    
    Args:
        prolific_id: The raw Prolific ID string.
        salt: A salt string to ensure uniqueness across projects.
        
    Returns:
        A SHA-256 hex digest of the salted ID.
    """
    if not prolific_id:
        return ""
    # Combine salt and ID, encode to bytes, hash
    salted_id = f"{salt}_{prolific_id}"
    return hashlib.sha256(salted_id.encode('utf-8')).hexdigest()

def anonymise_row(row: Dict[str, str], salt: str = "llmXive_project_salt") -> Dict[str, str]:
    """
    Anonymise a single row of ratings data.
    
    Args:
        row: A dictionary representing a CSV row.
        salt: Salt for hashing Prolific IDs.
        
    Returns:
        A new dictionary with anonymised fields.
    """
    new_row = {}
    for key, value in row.items():
        # Identify PII fields to strip or hash
        if key.lower() in ['prolific_id', 'prolificid', 'participant_id', 'pid']:
            # Hash the ID
            new_key = 'participant_id' # Standardize to participant_id
            new_row[new_key] = hash_prolific_id(value, salt)
        elif key.lower() in ['email', 'name', 'phone', 'address', 'ip_address']:
            # Strip PII entirely (do not include in output)
            continue
        else:
            # Keep other fields as-is
            new_row[key] = value
    return new_row

def anonymise_ratings(input_path: Path, output_path: Path, salt: str = "llmXive_project_salt") -> None:
    """
    Read real ratings, anonymise PII, and write to processed data.
    
    Args:
        input_path: Path to data/raw/real_ratings.csv
        output_path: Path to data/processed/anonymised_ratings.csv
        salt: Salt for hashing Prolific IDs.
    """
    logger = get_logger(__name__)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Reading real ratings from {input_path}")
    
    rows = []
    headers = None
    
    with open(input_path, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        headers = reader.fieldnames
        if not headers:
            raise ValueError("Input CSV file has no headers")
        
        for row in reader:
            anonymised_row = anonymise_row(row, salt)
            rows.append(anonymised_row)
    
    if not rows:
        logger.warning("No data rows found in input file.")
    
    # Determine output headers from the first anonymised row
    if rows:
        output_headers = list(rows[0].keys())
    else:
        # Fallback if no rows, try to infer from input minus PII
        output_headers = [h for h in headers if h.lower() not in ['email', 'name', 'phone', 'address', 'ip_address']]
        if 'prolific_id' in [h.lower() for h in headers]:
            output_headers.append('participant_id')
    
    logger.info(f"Writing anonymised ratings to {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_headers)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Successfully wrote {len(rows)} anonymised rows to {output_path}")

def main() -> None:
    """Main entry point for the anonymisation script."""
    setup_logging()
    logger = get_logger(__name__)
    
    raw_dir = get_raw_data_dir()
    processed_dir = get_processed_data_dir()
    
    input_file = raw_dir / "real_ratings.csv"
    output_file = processed_dir / "anonymised_ratings.csv"
    
    try:
        anonymise_ratings(input_file, output_file)
        logger.info("Anonymisation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during anonymisation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
