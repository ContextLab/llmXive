import csv
import hashlib
import logging
import os
import sys
from pathlib import Path

from config import get_raw_data_dir, get_processed_data_dir
from logging_config import setup_logging, get_logger

# Configure logger
logger = setup_logging()

def hash_prolific_id(prolific_id: str, salt: str = "llmXive_salt_2024") -> str:
    """
    Hashes a Prolific ID using SHA-256 with a project-specific salt.
    Returns the hexadecimal digest.
    """
    if not prolific_id:
        return ""
    combined = f"{salt}{prolific_id}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def anonymise_row(row: dict, salt: str = "llmXive_salt_2024") -> dict:
    """
    Creates a new dictionary with PII removed or hashed.
    - 'prolific_id' becomes 'participant_id' (hashed)
    - 'consent_timestamp' is kept (not PII)
    - 'rating' is kept
    - 'stimulus_id' is kept
    - 'context' is kept
    - Any other PII-like columns (e.g., email, name) would be dropped if present.
    """
    new_row = {}
    
    # Map prolific_id to hashed participant_id
    if 'prolific_id' in row:
        new_row['participant_id'] = hash_prolific_id(row['prolific_id'], salt)
    
    # Preserve non-PII data
    non_pii_columns = ['stimulus_id', 'context', 'rating', 'consent_timestamp', 'timestamp']
    for col in non_pii_columns:
        if col in row:
            new_row[col] = row[col]
    
    # Explicitly drop known PII if present (safety measure)
    pii_columns = ['email', 'name', 'prolific_id', 'ip_address', 'phone']
    for col in pii_columns:
        if col in row and col not in new_row:
            logger.warning(f"Dropping PII column: {col}")
    
    return new_row

def anonymise_ratings(input_path: Path, output_path: Path, salt: str = "llmXive_salt_2024"):
    """
    Reads real_ratings.csv, anonymizes Prolific IDs, and writes to anonymised_ratings.csv.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Reading raw ratings from {input_path}")
    
    rows = []
    with open(input_path, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        if not fieldnames:
            raise ValueError("Input CSV has no header row")
        
        if 'prolific_id' not in fieldnames:
            raise ValueError("Input CSV missing required column 'prolific_id'")
        
        for row in reader:
            anon_row = anonymise_row(row, salt)
            rows.append(anon_row)
    
    # Determine output fieldnames based on what we kept
    output_fieldnames = ['participant_id', 'stimulus_id', 'context', 'rating', 'consent_timestamp']
    # Filter to only columns that exist in the data (some might be missing if optional)
    if rows:
        existing_cols = set(rows[0].keys())
        output_fieldnames = [c for c in output_fieldnames if c in existing_cols]
    
    logger.info(f"Writing anonymised ratings to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Successfully anonymised {len(rows)} ratings.")
    return len(rows)

def main():
    raw_dir = get_raw_data_dir()
    processed_dir = get_processed_data_dir()
    
    input_file = raw_dir / "real_ratings.csv"
    output_file = processed_dir / "anonymised_ratings.csv"
    
    try:
        count = anonymise_ratings(input_file, output_file)
        logger.info(f"Task T051 completed: {count} records anonymised.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Failed to anonymise: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during anonymisation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
