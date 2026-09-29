"""
Preprocessing module for speedrun data.
Handles data cleaning, feature engineering, and runner anonymization.
"""

import csv
import json
import logging
import os
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/preprocess.log')
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to config file (default: code/config.yaml)
        
    Returns:
        Dictionary containing configuration values
    """
    import yaml
    
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def load_schema(schema_path: str = "contracts/run_record.schema.yaml") -> Dict[str, Any]:
    """Load JSON schema for run records.
    
    Args:
        schema_path: Path to schema file
        
    Returns:
        Schema dictionary
    """
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    return schema


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a run record against the schema.
    
    Args:
        record: Run record dictionary
        schema: Schema dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    required_fields = schema.get('required', [])
    field_types = schema.get('properties', {})
    
    for field in required_fields:
        if field not in record or record[field] is None:
            errors.append(f"Missing required field: {field}")
    
    for field, value in record.items():
        if field in field_types:
            expected_type = field_types[field].get('type')
            if expected_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Field {field} must be numeric, got {type(value)}")
            elif expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Field {field} must be string, got {type(value)}")
            elif expected_type == 'integer' and not isinstance(value, int):
                errors.append(f"Field {field} must be integer, got {type(value)}")
    
    return len(errors) == 0, errors


def load_raw_data(raw_data_dir: str = "data/raw") -> List[Dict[str, Any]]:
    """Load all raw JSON data files from the raw data directory.
    
    Args:
        raw_data_dir: Directory containing raw JSON files
        
    Returns:
        List of run records
    """
    records = []
    
    if not os.path.exists(raw_data_dir):
        logger.error(f"Raw data directory not found: {raw_data_dir}")
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    json_files = [f for f in os.listdir(raw_data_dir) if f.endswith('.json')]
    
    for filename in json_files:
        file_path = os.path.join(raw_data_dir, filename)
        logger.info(f"Loading {filename}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different API response structures
        if 'data' in data:
            records.extend(data['data'])
        elif 'runs' in data:
            records.extend(data['runs'])
        else:
            logger.warning(f"Unexpected structure in {filename}, treating as list")
            if isinstance(data, list):
                records.extend(data)
    
    logger.info(f"Loaded {len(records)} raw records")
    return records


def remove_duplicates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate records based on run_id and submission_date.
    
    Args:
        records: List of run records
        
    Returns:
        Deduplicated list of records
    """
    seen_ids: Set[Tuple[str, str]] = set()
    unique_records = []
    duplicates_removed = 0
    
    for record in records:
        run_id = record.get('run_id', record.get('id', ''))
        submission_date = record.get('submission_date', record.get('date', ''))
        
        key = (run_id, submission_date)
        
        if key not in seen_ids:
            seen_ids.add(key)
            unique_records.append(record)
        else:
            duplicates_removed += 1
    
    logger.info(f"Removed {duplicates_removed} duplicate records")
    return unique_records


def filter_incomplete_runs(records: List[Dict[str, Any]], 
                            required_fields: List[str] = None) -> List[Dict[str, Any]]:
    """Filter out records with missing required fields.
    
    Args:
        records: List of run records
        required_fields: List of fields that must be present
        
    Returns:
        Filtered list of records
    """
    if required_fields is None:
        required_fields = ['run_time_seconds', 'runner_id', 'attempt_number', 
                         'category', 'submission_date', 'game_id']
    
    filtered_records = []
    removed_count = 0
    
    for record in records:
        is_complete = all(field in record and record[field] is not None 
                        for field in required_fields)
        
        if is_complete:
            filtered_records.append(record)
        else:
            removed_count += 1
            missing = [f for f in required_fields if f not in record or record[f] is None]
            logger.debug(f"Removing record with missing fields: {missing}")
    
    logger.info(f"Removed {removed_count} incomplete records")
    return filtered_records


def hash_runner_id(runner_id: str, salt: str) -> str:
    """Hash a runner ID using SHA-256 with a project-specific salt.
    
    This implements Constitution Principle III by anonymizing runner IDs
    while preserving the ability to group runs by the same runner.
    
    Args:
        runner_id: The original runner ID from the API
        salt: Project-specific salt string from config.yaml
        
    Returns:
        Hex digest of the salted SHA-256 hash
        
    Raises:
        ValueError: If runner_id or salt is empty
    """
    if not runner_id:
        raise ValueError("runner_id cannot be empty")
    if not salt:
        raise ValueError("salt cannot be empty")
    
    # Combine salt and runner_id
    salted_id = f"{salt}:{runner_id}"
    
    # Compute SHA-256 hash
    hash_object = hashlib.sha256(salted_id.encode('utf-8'))
    digest = hash_object.hexdigest()
    
    return digest


def compute_runner_metrics(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Compute per-runner metrics from raw records.
    
    Args:
        records: List of run records
        
    Returns:
        Dictionary mapping runner_id to metrics
    """
    runner_data = defaultdict(lambda: {
        'runs': [],
        'first_run_date': None,
        'last_run_date': None,
        'games_played': set()
    })
    
    for record in records:
        runner_id = record['runner_id']
        submission_date = record['submission_date']
        game_id = record['game_id']
        
        runner_data[runner_id]['runs'].append(record)
        runner_data[runner_id]['games_played'].add(game_id)
        
        date_obj = datetime.fromisoformat(submission_date.replace('Z', '+00:00'))
        
        if runner_data[runner_id]['first_run_date'] is None or date_obj < runner_data[runner_id]['first_run_date']:
            runner_data[runner_id]['first_run_date'] = date_obj
        
        if runner_data[runner_id]['last_run_date'] is None or date_obj > runner_data[runner_id]['last_run_date']:
            runner_data[runner_id]['last_run_date'] = date_obj
    
    # Compute final metrics
    metrics = {}
    for runner_id, data in runner_data.items():
        total_runs = len(data['runs'])
        
        if data['first_run_date'] and data['last_run_date']:
            time_span = (data['last_run_date'] - data['first_run_date']).days
        else:
            time_span = 0
        
        metrics[runner_id] = {
            'total_runs': total_runs,
            'first_run_date': data['first_run_date'].isoformat() if data['first_run_date'] else None,
            'time_since_first_run_days': time_span,
            'games_played_count': len(data['games_played'])
        }
    
    return metrics


def generate_runner_profiles(records: List[Dict[str, Any]], 
                             salt: str) -> List[Dict[str, Any]]:
    """Generate RunnerProfile entities from processed records.
    
    Args:
        records: List of processed run records
        salt: Salt for hashing runner IDs
        
    Returns:
        List of runner profile dictionaries
    """
    # First compute metrics
    metrics = compute_runner_metrics(records)
    
    profiles = []
    for runner_id, metrics_data in metrics.items():
        # Hash the runner ID for the profile
        hashed_id = hash_runner_id(runner_id, salt)
        
        profile = {
            'runner_id': hashed_id,
            'total_prior_runs': metrics_data['total_runs'],
            'time_since_first_run_days': metrics_data['time_since_first_run_days'],
            'games_played_count': metrics_data['games_played_count']
        }
        profiles.append(profile)
    
    logger.info(f"Generated {len(profiles)} runner profiles")
    return profiles


def calculate_lagged_competitive_pressure(records: List[Dict[str, Any]], 
                                         window_days: int = 30) -> List[Dict[str, Any]]:
    """Calculate lagged competitive pressure for each record.
    
    Competitive pressure is defined as the number of active runners
    in the 30-day window prior to each run's submission date.
    
    Args:
        records: List of run records
        window_days: Number of days for the rolling window
        
    Returns:
        Updated list of records with lagged_competitive_pressure column
    """
    # Sort records by submission date
    sorted_records = sorted(records, key=lambda x: x['submission_date'])
    
    # Pre-compute date objects
    for record in sorted_records:
        record['_date_obj'] = datetime.fromisoformat(
            record['submission_date'].replace('Z', '+00:00')
        )
    
    # For each record, count active runners in the prior window
    for i, record in enumerate(sorted_records):
        run_date = record['_date_obj']
        window_start = run_date - timedelta(days=window_days)
        
        # Count unique runners in the window before this run
        active_runners = set()
        for j in range(i):
            other_date = sorted_records[j]['_date_obj']
            if window_start <= other_date < run_date:
                active_runners.add(sorted_records[j]['runner_id'])
        
        record['lagged_competitive_pressure'] = len(active_runners)
    
    # Remove temporary date objects
    for record in sorted_records:
        del record['_date_obj']
    
    logger.info("Calculated lagged competitive pressure for all records")
    return sorted_records


def save_to_csv(records: List[Dict[str, Any]], output_path: str) -> None:
    """Save records to a CSV file.
    
    Args:
        records: List of record dictionaries
        output_path: Path to output CSV file
    """
    if not records:
        logger.warning("No records to save")
        return
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = list(records[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Saved {len(records)} records to {output_path}")


def main():
    """Main entry point for preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline...")
    
    # Load configuration
    config = load_config()
    salt = config.get('salt', '')
    
    if not salt:
        logger.error("Salt not found in config. Cannot proceed with anonymization.")
        raise ValueError("Salt missing from config")
    
    # Load raw data
    raw_records = load_raw_data()
    logger.info(f"Loaded {len(raw_records)} raw records")
    
    # Remove duplicates
    deduped_records = remove_duplicates(raw_records)
    logger.info(f"After deduplication: {len(deduped_records)} records")
    
    # Filter incomplete runs
    filtered_records = filter_incomplete_runs(deduped_records)
    logger.info(f"After filtering: {len(filtered_records)} records")
    
    # Anonymize runner IDs
    for record in filtered_records:
        original_id = record['runner_id']
        record['runner_id'] = hash_runner_id(original_id, salt)
    
    logger.info("Runner IDs anonymized")
    
    # Compute runner metrics and generate profiles
    runner_profiles = generate_runner_profiles(filtered_records, salt)
    save_to_csv(runner_profiles, 'data/processed/runner_profiles.csv')
    
    # Calculate lagged competitive pressure
    processed_records = calculate_lagged_competitive_pressure(filtered_records)
    
    # Save processed records
    save_to_csv(processed_records, 'data/processed/run_records.csv')
    
    logger.info("Preprocessing pipeline completed successfully")
    
    return processed_records


if __name__ == "__main__":
    main()