import csv
import json
import logging
import os
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATE_FORMAT = "%Y-%m-%d"
LAG_WINDOW_DAYS = 30

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from file."""
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate a record against a schema (basic validation)."""
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in record or record[field] is None:
            return False
    return True

def load_raw_data(raw_data_dir: str) -> List[Dict[str, Any]]:
    """Load all raw JSON files from the specified directory."""
    records = []
    if not os.path.exists(raw_data_dir):
        logger.warning(f"Raw data directory not found: {raw_data_dir}")
        return records
    
    for filename in os.listdir(raw_data_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(raw_data_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        records.extend(data)
                    elif isinstance(data, dict):
                        records.append(data)
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    return records

def remove_duplicates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate records based on run_id and submission_date."""
    seen = set()
    unique_records = []
    for record in records:
        run_id = record.get('run_id')
        date = record.get('submission_date')
        key = (run_id, date)
        if key not in seen:
            seen.add(key)
            unique_records.append(record)
    return unique_records

def filter_incomplete_runs(records: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filter out records missing required fields."""
    return [r for r in records if validate_record(r, schema)]

def hash_runner_id(runner_id: str, salt: str) -> str:
    """Compute SHA-256 hash of runner_id with salt."""
    if not runner_id:
        return ""
    salted = f"{runner_id}{salt}"
    return hashlib.sha256(salted.encode('utf-8')).hexdigest()

def compute_runner_metrics(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Compute per-runner metrics: total_prior_runs, time_since_first_run_days, games_played_count."""
    runner_data = defaultdict(lambda: {
        'run_ids': [],
        'dates': [],
        'games': set()
    })
    
    for record in records:
        runner_id = record.get('runner_id')
        if not runner_id:
            continue
        
        run_date_str = record.get('submission_date')
        if not run_date_str:
            continue
        
        try:
            run_date = datetime.strptime(run_date_str, DATE_FORMAT)
        except ValueError:
            continue
        
        game_id = record.get('game_id')
        
        runner_data[runner_id]['run_ids'].append(record.get('run_id'))
        runner_data[runner_id]['dates'].append(run_date)
        if game_id:
            runner_data[runner_id]['games'].add(game_id)
    
    profiles = {}
    for runner_id, data in runner_data.items():
        dates = sorted(data['dates'])
        first_date = dates[0]
        total_runs = len(dates)
        
        profiles[runner_id] = {
            'total_prior_runs': total_runs,
            'first_run_date': first_date.strftime(DATE_FORMAT),
            'games_played_count': len(data['games']),
            'games_played': list(data['games'])
        }
    
    return profiles

def generate_runner_profiles(runner_metrics: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert runner metrics to a list of RunnerProfile records."""
    profiles = []
    for runner_id, metrics in runner_metrics.items():
        profiles.append({
            'runner_id': runner_id,
            'total_prior_runs': metrics['total_prior_runs'],
            'first_run_date': metrics['first_run_date'],
            'games_played_count': metrics['games_played_count'],
            'games_played': ','.join(sorted(metrics['games_played']))
        })
    return profiles

def calculate_lagged_competitive_pressure(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate lagged competitive_pressure for each record.
    
    competitive_pressure = count of active runners in the 30-day window prior to the run date.
    A runner is 'active' in a window if they have at least one run in that window.
    
    This function modifies records in-place to add 'lagged_competitive_pressure'.
    """
    if not records:
        return records
    
    # Parse dates and organize by runner
    runner_runs: Dict[str, List[datetime]] = defaultdict(list)
    parsed_records = []
    
    for record in records:
        date_str = record.get('submission_date')
        runner_id = record.get('runner_id')
        
        if not date_str or not runner_id:
            parsed_records.append((record, None, None))
            continue
        
        try:
            run_date = datetime.strptime(date_str, DATE_FORMAT)
        except ValueError:
            parsed_records.append((record, None, None))
            continue
        
        runner_runs[runner_id].append(run_date)
        parsed_records.append((record, run_date, runner_id))
    
    # Sort runner runs for efficient window calculation
    for runner_id in runner_runs:
        runner_runs[runner_id].sort()
    
    # Calculate lagged pressure for each record
    for record, run_date, runner_id in parsed_records:
        if run_date is None:
            record['lagged_competitive_pressure'] = 0
            continue
        
        window_start = run_date - timedelta(days=LAG_WINDOW_DAYS)
        window_end = run_date  # Exclusive end for "prior to"
        
        active_count = 0
        
        # Count runners with at least one run in (window_start, window_end]
        # Exclude the current runner's own runs to avoid self-inflation? 
        # The spec says "active_runners_count in 30-day window prior". 
        # Usually competitive pressure includes others. We will count ALL active runners
        # in that window to represent the "pressure" of the environment.
        # If we want to exclude self, we'd subtract 1 if self is active, but 
        # "pressure" usually implies the field. Let's count all unique runners active.
        
        for other_runner_id, other_dates in runner_runs.items():
            # Check if other_runner has any run in (window_start, window_end]
            has_run_in_window = False
            
            # Binary search or simple iteration (since lists are sorted)
            for d in other_dates:
                if window_start < d <= window_end:
                    has_run_in_window = True
                    break
                if d > window_end:
                    break
            
            if has_run_in_window:
                active_count += 1
        
        record['lagged_competitive_pressure'] = active_count
    
    return records

def save_to_csv(records: List[Dict[str, Any]], output_path: str, fieldnames: Optional[List[str]] = None):
    """Save records to a CSV file."""
    if not records:
        logger.warning(f"No records to save to {output_path}")
        # Create empty file with headers if possible
        if fieldnames:
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
        return
    
    if fieldnames is None:
        # Infer fieldnames from the first record
        fieldnames = list(records[0].keys())
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def main():
    """Main entry point for preprocessing pipeline."""
    config = load_config()
    
    # Paths
    raw_data_dir = config.get('paths', {}).get('raw_data', 'data/raw')
    processed_data_dir = config.get('paths', {}).get('processed_data', 'data/processed')
    schema_path = config.get('paths', {}).get('run_record_schema', 'contracts/run_record.schema.yaml')
    
    # Ensure output directory exists
    os.makedirs(processed_data_dir, exist_ok=True)
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Load raw data
    logger.info("Loading raw data...")
    raw_records = load_raw_data(raw_data_dir)
    logger.info(f"Loaded {len(raw_records)} raw records")
    
    # Remove duplicates
    logger.info("Removing duplicates...")
    unique_records = remove_duplicates(raw_records)
    logger.info(f"Records after deduplication: {len(unique_records)}")
    
    # Filter incomplete
    logger.info("Filtering incomplete runs...")
    filtered_records = filter_incomplete_runs(unique_records, schema)
    logger.info(f"Records after filtering: {len(filtered_records)}")
    
    # Hash runner IDs
    salt = config.get('salt', '')
    logger.info(f"Hashing runner IDs with salt...")
    for record in filtered_records:
        original_id = record.get('runner_id')
        record['runner_id'] = hash_runner_id(original_id, salt)
    
    # Compute runner metrics (for T013c)
    logger.info("Computing runner metrics...")
    runner_metrics = compute_runner_metrics(filtered_records)
    
    # Generate runner profiles (T013c)
    runner_profiles = generate_runner_profiles(runner_metrics)
    profiles_path = os.path.join(processed_data_dir, 'runner_profiles.csv')
    save_to_csv(runner_profiles, profiles_path)
    logger.info(f"Saved runner profiles to {profiles_path}")
    
    # Calculate lagged competitive pressure (T014)
    logger.info("Calculating lagged competitive pressure...")
    records_with_pressure = calculate_lagged_competitive_pressure(filtered_records)
    
    # Prepare final records for run_records.csv
    # Ensure all required fields are present and types are correct
    final_records = []
    for record in records_with_pressure:
        final_record = {
            'run_id': record.get('run_id'),
            'runner_id': record.get('runner_id'),
            'attempt_number': record.get('attempt_number'),
            'category': record.get('category'),
            'submission_date': record.get('submission_date'),
            'game_id': record.get('game_id'),
            'run_time_seconds': record.get('run_time_seconds'),
            'total_prior_runs': record.get('total_prior_runs', 0), # Derived from runner_metrics if needed, or 0 if not computed yet in this flow
            'time_since_first_run_days': record.get('time_since_first_run_days', 0),
            'lagged_competitive_pressure': record.get('lagged_competitive_pressure', 0)
        }
        final_records.append(final_record)
    
    # Save run_records.csv
    output_path = os.path.join(processed_data_dir, 'run_records.csv')
    save_to_csv(final_records, output_path)
    logger.info(f"Saved run records to {output_path}")
    
    logger.info("Preprocessing complete.")

if __name__ == "__main__":
    main()