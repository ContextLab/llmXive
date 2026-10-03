import argparse
import csv
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Import from existing project utilities
from utils.logger import setup_logger, log_script_start, log_script_end, log_data_operation, error
from utils.data_validation import validate_liker_scale, validate_participant_id, validate_condition
from utils.random_utils import set_global_seed

@dataclass
class Participant:
    """Data class representing a cleaned participant record."""
    participant_id: str
    condition: str
    manipulation_check: str
    manipulation_check_failed: bool
    attitude_item_1: Optional[int] = None
    attitude_item_2: Optional[int] = None
    attitude_item_3: Optional[int] = None
    attitude_item_4: Optional[int] = None
    attitude_item_5: Optional[int] = None
    attitude_item_6: Optional[int] = None
    attitude_item_7: Optional[int] = None
    usefulness_item_1: Optional[int] = None
    usefulness_item_2: Optional[int] = None
    usefulness_item_3: Optional[int] = None
    trust_item_1: Optional[int] = None
    trust_item_2: Optional[int] = None
    trust_item_3: Optional[int] = None
    trust_item_4: Optional[int] = None
    timestamp: Optional[str] = None

def setup_directories():
    """Ensure required output directories exist."""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir

def load_raw_data(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load raw survey data from CSV.
    If input_path is None, looks for default raw data files.
    """
    if input_path:
        path = Path(input_path)
    else:
        # Try to find raw data in data/raw
        base_dir = Path(__file__).parent.parent
        raw_dir = base_dir / "data" / "raw"
        if raw_dir.exists():
            csv_files = list(raw_dir.glob("*.csv"))
            if csv_files:
                path = csv_files[0]
            else:
                raise FileNotFoundError(f"No CSV files found in {raw_dir}")
        else:
            raise FileNotFoundError(f"Raw data directory {raw_dir} not found")
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize row keys to lowercase and strip whitespace."""
    return {k.strip().lower(): v.strip() if isinstance(v, str) else v for k, v in row.items()}

def is_partial_response(row: Dict[str, Any]) -> bool:
    """
    Check if a response is partial (abandoned halfway).
    A response is partial if key survey sections (Attitude, Usefulness, Trust) 
    have fewer than 50% of expected items filled.
    """
    # Expected items counts
    attitude_count = 0
    usefulness_count = 0
    trust_count = 0
    total_filled = 0

    for i in range(1, 8):
        key = f"attitude_item_{i}"
        if row.get(key) not in [None, '', 'NA', 'N/A']:
            attitude_count += 1
            total_filled += 1

    for i in range(1, 4):
        key = f"usefulness_item_{i}"
        if row.get(key) not in [None, '', 'NA', 'N/A']:
            usefulness_count += 1
            total_filled += 1

    for i in range(1, 5):
        key = f"trust_item_{i}"
        if row.get(key) not in [None, '', 'NA', 'N/A']:
            trust_count += 1
            total_filled += 1

    # Total expected items: 7 (attitude) + 3 (usefulness) + 4 (trust) = 14
    total_expected = 14
    completion_rate = total_filled / total_expected if total_expected > 0 else 0

    # Flag as partial if less than 50% completed
    return completion_rate < 0.5

def validate_and_process_row(row: Dict[str, Any]) -> Optional[Participant]:
    """
    Validate a raw row and convert to a Participant object.
    Returns None if validation fails or if it's a partial response.
    """
    # Normalize keys
    row = normalize_row(row)

    # Extract core fields
    pid = row.get('participant_id', row.get('participantid', ''))
    condition = row.get('condition', '')
    manip_check = row.get('manipulation_check', row.get('manipulationcheck', ''))
    
    # Validate Participant ID
    if not validate_participant_id(pid):
        return None

    # Validate Condition
    if not validate_condition(condition):
        return None

    # Check for partial response (Task T022)
    if is_partial_response(row):
        return None

    # Extract Likert items and validate
    attitude_items = []
    for i in range(1, 8):
        val = row.get(f'attitude_item_{i}')
        if val is None or val == '':
            attitude_items.append(None)
        else:
            try:
                int_val = int(val)
                if not validate_liker_scale(int_val):
                    return None # Invalid Likert value
                attitude_items.append(int_val)
            except (ValueError, TypeError):
                return None

    usefulness_items = []
    for i in range(1, 4):
        val = row.get(f'usefulness_item_{i}')
        if val is None or val == '':
            usefulness_items.append(None)
        else:
            try:
                int_val = int(val)
                if not validate_liker_scale(int_val):
                    return None
                usefulness_items.append(int_val)
            except (ValueError, TypeError):
                return None

    trust_items = []
    for i in range(1, 5):
        val = row.get(f'trust_item_{i}')
        if val is None or val == '':
            trust_items.append(None)
        else:
            try:
                int_val = int(val)
                if not validate_liker_scale(int_val):
                    return None
                trust_items.append(int_val)
            except (ValueError, TypeError):
                return None

    # Determine manipulation check failure (Task T021)
    # Assuming manipulation_check contains "correct" or "true" if passed, else failed.
    # Logic: If the string is empty, or explicitly "false", "incorrect", "fail", mark as failed.
    # Otherwise, assume passed.
    manip_failed = False
    if not manip_check:
        manip_failed = True
    else:
        mc_lower = str(manip_check).lower()
        if mc_lower in ['false', 'incorrect', 'fail', 'failed', 'no']:
            manip_failed = True
        elif mc_lower in ['true', 'correct', 'pass', 'passed', 'yes']:
            manip_failed = False
        else:
            # If it's a specific answer key, we might need more logic, but default to failed if ambiguous
            # For now, if it's not clearly a pass, we flag it as failed to be safe, 
            # or assume the raw value is the answer and compare to expected.
            # Given the spec, we just flag the boolean based on the check.
            # Let's assume if it's not a clear pass, it's a fail for safety in cleaning.
            # However, usually MC is "Did you read? (Yes/No)". If "No", failed=True.
            # If "Yes", failed=False.
            if mc_lower == 'no':
                manip_failed = True
            else:
                # If it's "Yes" or some other affirmative, assume passed unless it looks like an error
                manip_failed = False

    # Get timestamp if available
    timestamp = row.get('timestamp', row.get('submitted_at', datetime.now().isoformat()))

    return Participant(
        participant_id=pid,
        condition=condition,
        manipulation_check=manip_check,
        manipulation_check_failed=manip_failed,
        attitude_item_1=attitude_items[0], attitude_item_2=attitude_items[1],
        attitude_item_3=attitude_items[2], attitude_item_4=attitude_items[3],
        attitude_item_5=attitude_items[4], attitude_item_6=attitude_items[5],
        attitude_item_7=attitude_items[6],
        usefulness_item_1=usefulness_items[0], usefulness_item_2=usefulness_items[1],
        usefulness_item_3=usefulness_items[2],
        trust_item_1=trust_items[0], trust_item_2=trust_items[1],
        trust_item_3=trust_items[2], trust_item_4=trust_items[3],
        timestamp=timestamp
    )

def ingest_and_clean(input_path: Optional[str] = None) -> List[Participant]:
    """
    Main ingestion pipeline: load, validate, filter partials, and return clean list.
    """
    raw_data = load_raw_data(input_path)
    cleaned = []
    skipped = 0
    for i, row in enumerate(raw_data):
        try:
            participant = validate_and_process_row(row)
            if participant:
                cleaned.append(participant)
            else:
                skipped += 1
        except Exception as e:
            error(f"Error processing row {i}: {e}")
            skipped += 1
    
    log_data_operation("Ingestion", f"Processed {len(raw_data)} rows, kept {len(cleaned)}, skipped {skipped}")
    return cleaned

def export_cleaned_data(participants: List[Participant], output_path: str):
    """
    Export cleaned participants to CSV with the exact schema required by T023.
    Columns: participant_id, condition, manipulation_check, manipulation_check_failed,
    attitude_item_1..7, usefulness_item_1..3, trust_item_1..4
    """
    fieldnames = [
        'participant_id', 'condition', 'manipulation_check', 'manipulation_check_failed',
        'attitude_item_1', 'attitude_item_2', 'attitude_item_3', 'attitude_item_4',
        'attitude_item_5', 'attitude_item_6', 'attitude_item_7',
        'usefulness_item_1', 'usefulness_item_2', 'usefulness_item_3',
        'trust_item_1', 'trust_item_2', 'trust_item_3', 'trust_item_4'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in participants:
            row = asdict(p)
            # Remove timestamp if not in fieldnames (it's not in the required list for T023)
            # But asdict includes it. We can just let it be or filter.
            # The spec says "with columns: ...", implying these are the required ones.
            # We will write only the required columns to be precise.
            filtered_row = {k: v for k, v in row.items() if k in fieldnames}
            writer.writerow(filtered_row)
    
    log_data_operation("Export", f"Wrote {len(participants)} records to {output_path}")

def run_data_collection(input_path: Optional[str] = None, output_path: Optional[str] = None):
    """
    Orchestrate the data collection pipeline.
    """
    base_dir = Path(__file__).parent.parent
    if not output_path:
        output_path = str(base_dir / "data" / "processed" / "cleaned_responses.csv")
    
    log_script_start("04_data_collection", input_path, output_path)
    
    try:
        participants = ingest_and_clean(input_path)
        export_cleaned_data(participants, output_path)
        log_script_end("04_data_collection", "Success")
        return participants
    except Exception as e:
        error(f"Pipeline failed: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Ingest and clean survey data.")
    parser.add_argument("--input", type=str, help="Path to raw CSV input file")
    parser.add_argument("--output", type=str, help="Path to output cleaned CSV")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    set_global_seed(args.seed)
    run_data_collection(args.input, args.output)

if __name__ == "__main__":
    main()
