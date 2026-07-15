import csv
import json
import logging
import os
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema from file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a record against a schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    for field in required_fields:
        if field not in record or record[field] is None:
            errors.append(f"Missing required field: {field}")

    for field, value in record.items():
        if field in properties:
            field_schema = properties[field]
            expected_type = field_schema.get('type')
            if expected_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' must be a number, got {type(value)}")
            elif expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string, got {type(value)}")
            elif expected_type == 'integer' and not isinstance(value, int):
                errors.append(f"Field '{field}' must be an integer, got {type(value)}")

    return len(errors) == 0, errors

def load_raw_data(raw_dir: str) -> List[Dict[str, Any]]:
    """Load all raw JSON files from the data/raw directory."""
    raw_data = []
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    json_files = list(raw_path.glob("*.json"))
    if not json_files:
        logger.warning(f"No JSON files found in {raw_dir}")
        return raw_data

    for json_file in json_files:
        logger.info(f"Loading {json_file.name}")
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Handle cases where data is a list or a dict with a 'runs' key
                if isinstance(data, list):
                    raw_data.extend(data)
                elif isinstance(data, dict) and 'runs' in data:
                    raw_data.extend(data['runs'])
                elif isinstance(data, dict):
                    raw_data.append(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON in {json_file.name}: {e}")
    return raw_data

def remove_duplicates(records: List[Dict[str, Any]], key_fields: List[str]) -> List[Dict[str, Any]]:
    """Remove duplicate records based on key_fields."""
    seen = set()
    unique_records = []
    duplicates_count = 0

    for record in records:
        key = tuple(record.get(field, '') for field in key_fields)
        if key not in seen:
            seen.add(key)
            unique_records.append(record)
        else:
            duplicates_count += 1

    logger.info(f"Removed {duplicates_count} duplicate records.")
    return unique_records

def filter_incomplete_runs(records: List[Dict[str, Any]], required_fields: List[str]) -> List[Dict[str, Any]]:
    """Filter out records missing any required fields."""
    valid_records = []
    invalid_count = 0

    for record in records:
        if all(record.get(field) is not None and record.get(field) != '' for field in required_fields):
            valid_records.append(record)
        else:
            invalid_count += 1

    logger.info(f"Filtered out {invalid_count} incomplete records.")
    return valid_records

def hash_runner_id(runner_id: str, salt: str) -> str:
    """Compute SHA-256 hash of runner_id with salt."""
    if not runner_id:
        return ""
    salted = f"{runner_id}{salt}"
    return hashlib.sha256(salted.encode('utf-8')).hexdigest()

def compute_runner_metrics(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Compute per-runner metrics from raw records.
    Returns a dict keyed by hashed runner_id.
    """
    runner_data = defaultdict(lambda: {
        'run_times': [],
        'dates': [],
        'games': set()
    })

    for record in records:
        # Expect runner_id to be already hashed in the input records for this task
        # If not, we assume the caller has handled hashing (T013b)
        rid = record.get('runner_id')
        if not rid:
            continue

        try:
            run_time = float(record.get('run_time_seconds', 0))
            # Parse date string to datetime for sorting
            date_str = record.get('submission_date', '')
            # Simple date parsing assuming ISO format YYYY-MM-DD or similar
            # We store the string for now to avoid dependency on dateutil in this specific function
            game_id = record.get('game_id', 'unknown')
            
            runner_data[rid]['run_times'].append(run_time)
            runner_data[rid]['dates'].append(date_str)
            runner_data[rid]['games'].add(game_id)
        except (ValueError, TypeError):
            continue

    profiles = {}
    for rid, data in runner_data.items():
        dates = data['dates']
        # Sort dates to find first run
        # Simple string sort works for ISO dates
        dates.sort()
        first_run_date = dates[0] if dates else None
        last_run_date = dates[-1] if dates else None

        profiles[rid] = {
            'runner_id': rid,
            'total_prior_runs': len(data['run_times']),
            'first_run_date': first_run_date,
            'last_run_date': last_run_date,
            'games_played_count': len(data['games'])
        }
    return profiles

def calculate_lagged_competitive_pressure(records: List[Dict[str, Any]], window_days: int = 30) -> List[Dict[str, Any]]:
    """
    Calculate lagged competitive pressure for each record.
    This counts active runners in the 30-day window prior to the run date.
    Note: This is a placeholder implementation for T014. 
    For T013c, we focus on generating RunnerProfile.
    """
    # Implementation deferred to T014 as per dependencies
    return records

def save_to_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """Save a list of dictionaries to a CSV file."""
    if not data:
        logger.warning("No data to save to CSV.")
        return

    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(data[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def generate_runner_profiles(records: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate RunnerProfile entity and save to CSV.
    Aggregates per-runner statistics: total_prior_runs, time_since_first_run_days (placeholder), games_played_count.
    """
    logger.info("Generating Runner Profiles...")
    profiles = compute_runner_metrics(records)
    
    # Convert dict to list for CSV saving
    profile_list = []
    for rid, profile in profiles.items():
        profile_list.append(profile)
    
    # Sort by total prior runs descending for readability
    profile_list.sort(key=lambda x: x['total_prior_runs'], reverse=True)
    
    save_to_csv(profile_list, output_path)
    logger.info(f"Saved {len(profile_list)} runner profiles to {output_path}")

def main():
    """Main entry point for preprocessing script."""
    logger.info("Starting preprocessing pipeline...")
    
    try:
        config = load_config()
        games = config.get('games', [])
        salt = config.get('salt', '')
        min_sample_size = config.get('min_sample_size', 100)
        
        # Load schema
        schema_path = "contracts/run_record.schema.yaml"
        # Since load_schema expects JSON, and schema is YAML, we need to handle this carefully.
        # For this implementation, we assume a JSON version exists or we load YAML and convert.
        # However, the API surface says load_schema returns Dict. Let's assume the file is JSON or we handle YAML.
        # The provided API surface for load_schema implies it loads JSON. 
        # Given T004 created a .yaml file, we need to be careful. 
        # But the task T013c specifically asks to generate RunnerProfile.
        # We will proceed with data loading and profile generation.
        
        raw_dir = "data/raw"
        processed_dir = "data/processed"
        
        # Load raw data
        raw_records = load_raw_data(raw_dir)
        logger.info(f"Loaded {len(raw_records)} raw records.")
        
        # Remove duplicates
        unique_records = remove_duplicates(raw_records, ['run_id', 'game_id', 'attempt_number'])
        
        # Filter incomplete runs
        required_fields = ['run_time_seconds', 'runner_id', 'game_id', 'submission_date']
        valid_records = filter_incomplete_runs(unique_records, required_fields)
        logger.info(f"Filtered to {len(valid_records)} valid records.")
        
        # Hash runner IDs if not already done (T013b logic)
        # Assuming T013b ran, but if we are running T013c in isolation or as part of a chain:
        # We check if runner_id looks like a hash (64 chars hex). If not, hash it.
        for record in valid_records:
            rid = record.get('runner_id', '')
            if len(rid) != 64 or not all(c in '0123456789abcdef' for c in rid.lower()):
                record['runner_id'] = hash_runner_id(rid, salt)
        
        # Generate Runner Profiles (T013c)
        profile_output_path = os.path.join(processed_dir, "runner_profiles.csv")
        generate_runner_profiles(valid_records, profile_output_path)
        
        # Save processed run records (T013a continuation)
        records_output_path = os.path.join(processed_dir, "run_records.csv")
        save_to_csv(valid_records, records_output_path)
        
        logger.info("Preprocessing pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in preprocessing pipeline: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()