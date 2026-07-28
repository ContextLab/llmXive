import argparse
import csv
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Import from local utils
from utils.data_validation import (
    validate_liker_scale,
    validate_participant_id,
    validate_condition,
    validate_survey_response_row,
    ValidationResult
)
from utils.logger import setup_logger, log_script_start, log_script_end, log_data_operation, info, error, warning
from utils.random_utils import set_global_seed

@dataclass
class Participant:
    participant_id: str
    condition: str
    manipulation_check: str
    manipulation_check_failed: bool
    attitude_items: List[int]
    usefulness_items: List[int]
    trust_items: List[int]
    timestamp: str

def setup_directories(base_path: Path) -> Dict[str, Path]:
    """Ensure all required directories exist."""
    dirs = {
        'raw': base_path / 'data' / 'raw',
        'processed': base_path / 'data' / 'processed',
        'stimuli': base_path / 'data' / 'stimuli',
        'ethics': base_path / 'data' / 'ethics'
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def load_raw_data(raw_path: Path) -> List[Dict[str, Any]]:
    """
    Load raw survey data from CSV.
    Expects a CSV with columns mapping to our expected schema.
    If file doesn't exist, raises FileNotFoundError to fail loudly.
    """
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}. "
                                "Please ensure data collection has run and populated data/raw/responses.csv.")
    
    rows = []
    with open(raw_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    log_data_operation("load_raw_data", f"Loaded {len(rows)} rows from {raw_path}")
    return rows

def normalize_row(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Normalize raw CSV string values to appropriate types.
    Handles missing values by converting to None.
    """
    normalized = {}
    for key, value in row.items():
        if value == '' or value is None:
            normalized[key] = None
        elif key.endswith('_id') or key in ['participant_id', 'condition']:
            normalized[key] = str(value)
        else:
            # Attempt to parse as int for Likert scales
            try:
                normalized[key] = int(value)
            except (ValueError, TypeError):
                normalized[key] = value
    return normalized

def is_partial_response(normalized_row: Dict[str, Any]) -> bool:
    """
    Check if a response is partial (abandoned halfway).
    We consider it partial if the manipulation check or any attitude item is missing.
    """
    required_fields = ['manipulation_check', 'attitude_item_1']
    for field in required_fields:
        if normalized_row.get(field) is None:
            return True
    return False

def validate_and_process_row(row: Dict[str, Any], row_idx: int) -> Optional[Participant]:
    """
    Validate a single row and convert it to a Participant object.
    Returns None if validation fails or response is partial.
    """
    # Check for partial response first
    if is_partial_response(row):
        log_data_operation("validate_and_process_row", f"Row {row_idx}: Excluded partial response")
        return None

    # Validate Participant ID
    p_id = row.get('participant_id')
    if not p_id or not validate_participant_id(p_id):
        warning(f"Row {row_idx}: Invalid participant_id '{p_id}', skipping.")
        return None

    # Validate Condition
    condition = row.get('condition')
    if not condition or not validate_condition(condition):
        warning(f"Row {row_idx}: Invalid condition '{condition}', skipping.")
        return None

    # Collect Attitude Items (1-7)
    attitude_items = []
    for i in range(1, 8):
        val = row.get(f'attitude_item_{i}')
        if val is None:
            warning(f"Row {row_idx}: Missing attitude_item_{i}, skipping row.")
            return None
        if not validate_liker_scale(val):
            warning(f"Row {row_idx}: Invalid attitude_item_{i} value '{val}', skipping.")
            return None
        attitude_items.append(int(val))

    # Collect Usefulness Items (1-3)
    usefulness_items = []
    for i in range(1, 4):
        val = row.get(f'usefulness_item_{i}')
        if val is None:
            warning(f"Row {row_idx}: Missing usefulness_item_{i}, skipping row.")
            return None
        if not validate_liker_scale(val):
            warning(f"Row {row_idx}: Invalid usefulness_item_{i} value '{val}', skipping.")
            return None
        usefulness_items.append(int(val))

    # Collect Trust Items (1-4)
    trust_items = []
    for i in range(1, 5):
        val = row.get(f'trust_item_{i}')
        if val is None:
            warning(f"Row {row_idx}: Missing trust_item_{i}, skipping row.")
            return None
        if not validate_liker_scale(val):
            warning(f"Row {row_idx}: Invalid trust_item_{i} value '{val}', skipping.")
            return None
        trust_items.append(int(val))

    # Process Manipulation Check
    mc_val = row.get('manipulation_check')
    if mc_val is None:
        warning(f"Row {row_idx}: Missing manipulation_check, skipping.")
        return None
    
    # Determine if manipulation check failed
    # Assuming 'pass' or similar indicates success, anything else fails
    # This logic should align with the specific survey design
    mc_failed = str(mc_val).lower() not in ['pass', 'true', '1', 'yes']
    
    timestamp = row.get('timestamp', datetime.now().isoformat())

    return Participant(
        participant_id=p_id,
        condition=condition,
        manipulation_check=str(mc_val),
        manipulation_check_failed=mc_failed,
        attitude_items=attitude_items,
        usefulness_items=usefulness_items,
        trust_items=trust_items,
        timestamp=timestamp
    )

def ingest_and_clean(raw_data: List[Dict[str, Any]]) -> List[Participant]:
    """
    Ingest raw data, validate, and clean.
    Returns list of valid Participant objects.
    """
    cleaned = []
    total = len(raw_data)
    excluded = 0

    for idx, row in enumerate(raw_data):
        normalized = normalize_row(row)
        participant = validate_and_process_row(normalized, idx)
        if participant:
            cleaned.append(participant)
        else:
            excluded += 1

    info(f"Ingested {total} rows, kept {len(cleaned)}, excluded {excluded} (partial/invalid).")
    return cleaned

def export_cleaned_data(participants: List[Participant], output_path: Path):
    """
    Export cleaned data to CSV with the exact required columns.
    Columns: participant_id, condition, manipulation_check, manipulation_check_failed,
             attitude_item_1..7, usefulness_item_1..3, trust_item_1..4
    """
    if not participants:
        warning("No participants to export.")
        return

    fieldnames = [
        'participant_id', 'condition', 'manipulation_check', 'manipulation_check_failed'
    ]
    # Add attitude items
    for i in range(1, 8):
        fieldnames.append(f'attitude_item_{i}')
    # Add usefulness items
    for i in range(1, 4):
        fieldnames.append(f'usefulness_item_{i}')
    # Add trust items
    for i in range(1, 5):
        fieldnames.append(f'trust_item_{i}')
    # Optional: timestamp
    fieldnames.append('timestamp')

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for p in participants:
            row = {
                'participant_id': p.participant_id,
                'condition': p.condition,
                'manipulation_check': p.manipulation_check,
                'manipulation_check_failed': str(p.manipulation_check_failed),
                'timestamp': p.timestamp
            }
            
            # Flatten lists into individual columns
            for i, val in enumerate(p.attitude_items, 1):
                row[f'attitude_item_{i}'] = val
            for i, val in enumerate(p.usefulness_items, 1):
                row[f'usefulness_item_{i}'] = val
            for i, val in enumerate(p.trust_items, 1):
                row[f'trust_item_{i}'] = val

            writer.writerow(row)

    log_data_operation("export_cleaned_data", f"Exported {len(participants)} participants to {output_path}")

def run_data_collection(raw_path: Optional[Path] = None, output_path: Optional[Path] = None):
    """
    Main entry point for data collection and cleaning.
    """
    base = Path.cwd()
    dirs = setup_directories(base)

    # Default paths
    if raw_path is None:
        raw_path = dirs['raw'] / 'responses.csv'
    if output_path is None:
        output_path = dirs['processed'] / 'cleaned_responses.csv'

    log_script_start("04_data_collection")
    info(f"Input: {raw_path}, Output: {output_path}")

    try:
        # Load
        raw_data = load_raw_data(raw_path)
        
        # Clean
        cleaned_participants = ingest_and_clean(raw_data)
        
        # Export
        export_cleaned_data(cleaned_participants, output_path)
        
        info("Data collection and cleaning completed successfully.")
        return cleaned_participants

    except FileNotFoundError as e:
        error(str(e))
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error during data collection: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Ingest and clean survey response data.")
    parser.add_argument("--input", type=str, help="Path to raw input CSV")
    parser.add_argument("--output", type=str, help="Path to output cleaned CSV")
    args = parser.parse_args()

    raw_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None

    run_data_collection(raw_path, output_path)

if __name__ == "__main__":
    main()
