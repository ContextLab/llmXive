import csv
import hashlib
import logging
import os
import sys
from pathlib import Path
from config import get_raw_data_dir, get_processed_data_dir
from logging_config import setup_logging, get_logger

def hash_prolific_id(prolific_id: str, salt: str = "llmXive_salt_2024") -> str:
    """
    Hash a Prolific ID using SHA-256 with a project-specific salt.
    
    Args:
        prolific_id: The raw Prolific ID string.
        salt: The salt string used for hashing.
    
    Returns:
        A hex digest of the hashed ID.
    """
    if not prolific_id:
        raise ValueError("Prolific ID cannot be empty")
    combined = f"{salt}{prolific_id}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def anonymise_row(row: dict, salt: str = "llmXive_salt_2024") -> dict:
    """
    Create an anonymised copy of a rating row.
    
    - Replaces 'prolific_id' with 'participant_id' (hashed).
    - Removes any potential PII columns (e.g., 'email', 'name', 'ip_address') if present.
    - Retains all other data columns intact.
    
    Args:
        row: A dictionary representing a single row from the raw ratings CSV.
        salt: The salt for hashing the ID.
    
    Returns:
        A new dictionary with anonymised fields.
    """
    anonymised = {}
    
    # Copy all fields except PII and the original ID
    pii_fields = {'email', 'name', 'ip_address', 'phone', 'address'}
    for key, value in row.items():
        if key.lower() in pii_fields:
            continue
        if key == 'prolific_id':
            continue
        anonymised[key] = value
    
    # Add the hashed participant ID
    original_id = row.get('prolific_id')
    if original_id:
        anonymised['participant_id'] = hash_prolific_id(original_id, salt)
    else:
        raise ValueError("Row missing 'prolific_id' column")
    
    return anonymised

def anonymise_ratings(input_path: Path, output_path: Path, salt: str = "llmXive_salt_2024") -> int:
    """
    Read raw ratings, anonymise Prolific IDs, strip PII, and write to a new CSV.
    
    Args:
        input_path: Path to the input raw ratings CSV.
        output_path: Path to the output anonymised ratings CSV.
        salt: The salt for hashing.
    
    Returns:
        The number of rows processed.
    """
    logger = get_logger()
    logger.info(f"Starting anonymisation of {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    row_count = 0
    fieldnames = None
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(input_path, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames)
        
        # Filter fieldnames for the output to exclude raw PII
        pii_fields = {'email', 'name', 'ip_address', 'phone', 'address'}
        output_fieldnames = [f for f in fieldnames if f.lower() not in pii_fields and f != 'prolific_id']
        output_fieldnames.append('participant_id')
        
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
            writer.writeheader()
            
            for row in reader:
                anonymised_row = anonymise_row(row, salt)
                writer.writerow(anonymised_row)
                row_count += 1
                if row_count % 1000 == 0:
                    logger.debug(f"Processed {row_count} rows...")
    
    logger.info(f"Anonymisation complete. Wrote {row_count} rows to {output_path}")
    return row_count

def main():
    """Main entry point for the anonymisation script."""
    logger = setup_logging()
    
    input_dir = get_raw_data_dir()
    output_dir = get_processed_data_dir()
    
    input_file = input_dir / "real_ratings.csv"
    output_file = output_dir / "anonymised_ratings.csv"
    
    try:
        count = anonymise_ratings(input_file, output_file)
        logger.info(f"Successfully anonymised {count} ratings.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"An error occurred during anonymisation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
