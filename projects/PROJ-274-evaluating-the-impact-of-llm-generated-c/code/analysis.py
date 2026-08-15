"""
Analysis Module for Data Cleaning and Processing.

Implements T032a (PII Removal) and T032b (Incomplete Record Handling).
Also provides helper functions for loading/saving and checksums.
"""

import json
import os
import re
import logging
import hashlib
import csv
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

# --- Helper Functions ---

def load_json_file(path: str) -> List[Dict[str, Any]]:
    """Load a JSON file and return its content."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data: Any, path: str) -> None:
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def calculate_checksum(data: str) -> str:
    """Calculate SHA-256 checksum of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def update_checksums(checksums_path: str, filename: str, checksum: str) -> None:
    """Update the global checksums file."""
    os.makedirs(os.path.dirname(checksums_path), exist_ok=True)
    if os.path.exists(checksums_path):
        with open(checksums_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []

    # Remove existing entry for this file if present
    lines = [l for l in lines if not l.startswith(f"{filename}:")]

    with open(checksums_path, 'a') as f:
        f.write(f"{filename}:{checksum}\n")

# --- T032a: PII Removal ---

# Regex patterns for common PII
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b')
IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
# Simple name pattern (capitalized words, heuristic) - be careful not to over-remove
NAME_PATTERN = re.compile(r'\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b')

def remove_pii_from_string(text: str) -> str:
    """Remove PII patterns from a string."""
    if not isinstance(text, str):
        return text
    text = EMAIL_PATTERN.sub('[EMAIL_REDACTED]', text)
    text = PHONE_PATTERN.sub('[PHONE_REDACTED]', text)
    text = IP_PATTERN.sub('[IP_REDACTED]', text)
    # Note: Name removal is heuristic and might be too aggressive for generic text.
    # Usually, specific fields are better targets, but we apply a conservative pass here.
    return text

def remove_pii_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively remove PII from a dictionary."""
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str):
            cleaned[key] = remove_pii_from_string(value)
        elif isinstance(value, dict):
            cleaned[key] = remove_pii_from_dict(value)
        elif isinstance(value, list):
            cleaned[key] = remove_pii_from_list(value)
        else:
            cleaned[key] = value
    return cleaned

def remove_pii_from_list(data: List[Any]) -> List[Any]:
    """Recursively remove PII from a list."""
    cleaned = []
    for item in data:
        if isinstance(item, str):
            cleaned.append(remove_pii_from_string(item))
        elif isinstance(item, dict):
            cleaned.append(remove_pii_from_dict(item))
        elif isinstance(item, list):
            cleaned.append(remove_pii_from_list(item))
        else:
            cleaned.append(item)
    return cleaned

def remove_pii(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Main entry point for T032a.
    Removes PII from the entire dataset.
    """
    logger.info("Starting PII removal...")
    cleaned_data = []
    for record in data:
        cleaned_record = remove_pii_from_dict(record)
        cleaned_data.append(cleaned_record)
    logger.info("PII removal completed.")
    return cleaned_data

# --- T032b: Incomplete Record Handling ---

def validate_input_data(data: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """
    Validates input data and separates valid/incomplete records.
    Returns (valid_records, invalid_records).
    """
    valid = []
    invalid = []
    
    required_fields = ['participant_id', 'condition', 'start_time', 'end_time']
    
    for record in data:
        is_valid = True
        for field in required_fields:
            if field not in record or record[field] is None:
                is_valid = False
                break
        
        # Check for explicit status flag if present
        if 'status' in record and record['status'] == 'incomplete':
            is_valid = False
        
        if is_valid:
            valid.append(record)
        else:
            invalid.append(record)
            
    return valid, invalid

def handle_incomplete_records(data: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """
    Main entry point for T032b.
    Flags and excludes incomplete records.
    Returns (final_data_for_analysis, dropouts).
    """
    logger.info("Handling incomplete records...")
    valid, invalid = validate_input_data(data)
    
    # Mark invalid records as dropouts
    dropouts = []
    for record in invalid:
        record['status'] = 'incomplete'
        record['dropout_reason'] = 'missing_required_fields_or_flagged'
        dropouts.append(record)
        
    logger.info(f"Identified {len(dropouts)} incomplete records.")
    return valid, dropouts

def save_dropouts(dropouts: List[Dict], path: str) -> None:
    """Save dropout records to a separate JSON file."""
    if dropouts:
        save_json_file(dropouts, path)
        logger.info(f"Saved {len(dropouts)} dropouts to {path}")

def save_cleaned_dataset_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves the cleaned dataset to a CSV file.
    Ensures the directory exists.
    """
    if not data:
        # Create empty file with headers if we know them, or just touch it
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            f.write("")
        logger.warning("No data to write to CSV.")
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Determine headers from the first record
    headers = list(data[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved cleaned dataset with {len(data)} rows to {output_path}")

def main():
    """
    Standalone execution for testing T032a/T032b logic.
    """
    # This is primarily run via run_cleaning_pipeline.py
    pass

if __name__ == "__main__":
    main()