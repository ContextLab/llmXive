"""
Preprocessing script for speedrun data (T013a).

Responsibilities:
1. Load raw JSON data from data/raw/ (produced by fetch_data.py).
2. Remove duplicates and filter incomplete runs (FR-002).
3. Compute 'total_prior_runs' and 'time_since_first_run_days' (FR-003).
4. Validate output against contracts/run_record.schema.yaml.
5. Save cleaned data to data/processed/run_records.csv.
6. Generate runner_profiles.csv (T013c requirement).
7. Calculate lagged_competitive_pressure (T014 requirement).
"""
import json
import csv
import os
import sys
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import yaml

# Project root relative path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "run_record.schema.yaml"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "preprocess.log")
    ]
)
logger = logging.getLogger(__name__)

# Ensure output directories exist
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "logs").mkdir(parents=True, exist_ok=True)

def load_config() -> Dict[str, Any]:
    """Load project configuration."""
    if not CONFIG_PATH.exists():
        logger.error(f"Config file not found: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_schema() -> Dict[str, Any]:
    """Load the run_record schema."""
    if not SCHEMA_PATH.exists():
        logger.error(f"Schema file not found: {SCHEMA_PATH}")
        sys.exit(1)
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate a single record against the schema."""
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in record or record[field] is None:
            return False
    # Type checks (basic)
    if 'run_time_seconds' in record:
        if not isinstance(record['run_time_seconds'], (int, float)):
            return False
    if 'attempt_number' in record:
        if not isinstance(record['attempt_number'], int):
            return False
    return True

def load_raw_data() -> List[Dict[str, Any]]:
    """Load all raw JSON files from data/raw/."""
    records = []
    if not DATA_RAW_DIR.exists():
        logger.warning(f"Raw data directory not found: {DATA_RAW_DIR}")
        return records

    json_files = list(DATA_RAW_DIR.glob("*.json"))
    if not json_files:
        logger.warning("No JSON files found in data/raw/")
        return records

    for file_path in json_files:
        logger.info(f"Loading {file_path.name}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Handle case where data is a list or a dict with a 'runs' key
                if isinstance(data, list):
                    records.extend(data)
                elif isinstance(data, dict):
                    if 'runs' in data:
                        records.extend(data['runs'])
                    else:
                        # Assume the dict itself is a record or contains a list of records
                        if 'run_id' in data:
                            records.append(data)
                        elif isinstance(data.get('data'), list):
                            records.extend(data['data'])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error reading {file_path}: {e}")
    
    logger.info(f"Total raw records loaded: {len(records)}")
    return records

def remove_duplicates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate runs based on run_id."""
    seen_ids: Set[str] = set()
    unique_records = []
    duplicates_count = 0

    for record in records:
        run_id = record.get('run_id')
        if not run_id:
            # If no ID, try to create a composite key for uniqueness
            # This is a fallback; ideally run_id is always present
            key = json.dumps(record, sort_keys=True)
            if key not in seen_ids:
                seen_ids.add(key)
                unique_records.append(record)
            else:
                duplicates_count += 1
        else:
            if run_id not in seen_ids:
                seen_ids.add(run_id)
                unique_records.append(record)
            else:
                duplicates_count += 1

    logger.info(f"Removed {duplicates_count} duplicates. Remaining: {len(unique_records)}")
    return unique_records

def filter_incomplete_runs(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out records missing critical fields."""
    required_fields = ['run_id', 'run_time_seconds', 'runner_id', 'attempt_number', 'category', 'submission_date', 'game_id']
    valid_records = []
    filtered_count = 0

    for record in records:
        if all(field in record and record[field] is not None for field in required_fields):
            valid_records.append(record)
        else:
            filtered_count += 1

    retention_rate = (len(valid_records) / len(records) * 100) if records else 0
    logger.info(f"Filtered {filtered_count} incomplete runs. Retention rate: {retention_rate:.2f}%")
    
    if retention_rate < 95:
        logger.warning(f"Retention rate ({retention_rate:.2f}%) is below the 95% threshold.")
    
    return valid_records

def hash_runner_id(runner_id: str, salt: str) -> str:
    """Hash runner_id with salt for anonymization."""
    if not runner_id:
        return ""
    combined = f"{runner_id}{salt}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def compute_runner_metrics(records: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Compute 'total_prior_runs' and 'time_since_first_run_days' for every record.
    Also computes 'games_played_count' for runner profiles.
    """
    salt = config.get('salt', '')
    
    # Group by original runner_id to calculate metrics
    # We need to map original IDs to hashed IDs
    runner_data: Dict[str, List[Dict[str, Any]]] = {}
    
    for record in records:
        orig_id = record.get('runner_id')
        if not orig_id:
            continue
        
        # Anonymize immediately
        hashed_id = hash_runner_id(orig_id, salt)
        record['runner_id'] = hashed_id  # Update in place
        
        if hashed_id not in runner_data:
            runner_data[hashed_id] = []
        runner_data[hashed_id].append(record)

    # Sort each runner's runs by submission_date
    for hashed_id, runs in runner_data.items():
        runs.sort(key=lambda x: x.get('submission_date', ''))
        
        first_run_date = None
        for i, run in enumerate(runs):
            try:
                run_date = datetime.fromisoformat(run['submission_date'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                # Fallback for non-ISO formats if necessary, though API usually returns ISO
                run_date = datetime.now() 
            
            if first_run_date is None:
                first_run_date = run_date
                run['time_since_first_run_days'] = 0.0
            else:
                delta = run_date - first_run_date
                run['time_since_first_run_days'] = delta.days
            
            # total_prior_runs is the index (0-based) in the sorted list
            run['total_prior_runs'] = i

    return records

def calculate_lagged_competitive_pressure(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate lagged_competitive_pressure: count of active runners in the 30-day window prior to run date.
    """
    # Group by game_id and date to facilitate window calculation
    # We need to know how many unique runners were active in the 30 days before each run
    
    # First, organize runs by game_id
    game_runs: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        game_id = record.get('game_id')
        if game_id not in game_runs:
            game_runs[game_id] = []
        game_runs[game_id].append(record)

    for game_id, runs in game_runs.items():
        # Sort by date
        runs.sort(key=lambda x: x.get('submission_date', ''))
        
        for i, run in enumerate(runs):
            try:
                run_date = datetime.fromisoformat(run['submission_date'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                run['lagged_competitive_pressure'] = 0
                continue
            
            window_start = run_date - timedelta(days=30)
            window_end = run_date # Exclusive of current run? Usually "prior" means < run_date
            
            # Count unique runner_ids in the window [window_start, run_date)
            active_runners = set()
            # Optimization: Since list is sorted, we could use a sliding window, 
            # but for N < 100k, O(N^2) is acceptable. If needed, optimize later.
            for other_run in runs:
                try:
                    other_date = datetime.fromisoformat(other_run['submission_date'].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    continue
                
                if window_start <= other_date < run_date:
                    active_runners.add(other_run.get('runner_id'))
            
            run['lagged_competitive_pressure'] = len(active_runners)

    return records

def save_to_csv(records: List[Dict[str, Any]], output_path: Path):
    """Save records to CSV."""
    if not records:
        logger.warning("No records to save.")
        return

    # Determine fields from the first record
    fields = list(records[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Saved {len(records)} records to {output_path}")

def generate_runner_profiles(records: List[Dict[str, Any]], output_path: Path):
    """Aggregate per-runner statistics and save to runner_profiles.csv."""
    runner_stats: Dict[str, Dict[str, Any]] = {}
    
    for record in records:
        runner_id = record.get('runner_id')
        if not runner_id:
            continue
        
        if runner_id not in runner_stats:
            runner_stats[runner_id] = {
                'runner_id': runner_id,
                'total_runs': 0,
                'games_played': set(),
                'first_run_date': None,
                'last_run_date': None
            }
        
        stats = runner_stats[runner_id]
        stats['total_runs'] += 1
        stats['games_played'].add(record.get('game_id'))
        
        sub_date = record.get('submission_date')
        if sub_date:
            if stats['first_run_date'] is None or sub_date < stats['first_run_date']:
                stats['first_run_date'] = sub_date
            if stats['last_run_date'] is None or sub_date > stats['last_run_date']:
                stats['last_run_date'] = sub_date
    
    # Convert to list and calculate derived fields
    profiles = []
    for runner_id, stats in runner_stats.items():
        profile = {
            'runner_id': runner_id,
            'total_prior_runs': stats['total_runs'] - 1, # Approximation based on total runs
            'games_played_count': len(stats['games_played']),
            'first_run_date': stats['first_run_date'],
            'last_run_date': stats['last_run_date']
        }
        if stats['first_run_date'] and stats['last_run_date']:
            try:
                first = datetime.fromisoformat(stats['first_run_date'].replace('Z', '+00:00'))
                last = datetime.fromisoformat(stats['last_run_date'].replace('Z', '+00:00'))
                profile['career_span_days'] = (last - first).days
            except:
                profile['career_span_days'] = 0
        profiles.append(profile)
    
    # Sort by total runs descending
    profiles.sort(key=lambda x: x['total_prior_runs'], reverse=True)
    
    save_to_csv(profiles, output_path)

def main():
    logger.info("Starting preprocessing pipeline (T013a).")
    
    config = load_config()
    schema = load_schema()
    
    # 1. Load Raw Data
    raw_records = load_raw_data()
    if not raw_records:
        logger.error("No raw data found. Exiting.")
        sys.exit(1)
    
    # 2. Remove Duplicates
    deduped_records = remove_duplicates(raw_records)
    
    # 3. Filter Incomplete
    valid_records = filter_incomplete_runs(deduped_records)
    
    # 4. Compute Runner Metrics (Hashing, Prior Runs, Time Since First)
    processed_records = compute_runner_metrics(valid_records, config)
    
    # 5. Calculate Lagged Competitive Pressure
    processed_records = calculate_lagged_competitive_pressure(processed_records)
    
    # 6. Validate against Schema
    invalid_count = 0
    for i, record in enumerate(processed_records):
        if not validate_record(record, schema):
            invalid_count += 1
            if invalid_count <= 5:
                logger.warning(f"Invalid record at index {i}: {record}")
    
    if invalid_count > 0:
        logger.warning(f"Total invalid records after processing: {invalid_count}")
    
    # 7. Save Run Records
    output_path = DATA_PROCESSED_DIR / "run_records.csv"
    save_to_csv(processed_records, output_path)
    
    # 8. Generate Runner Profiles (T013c requirement)
    profiles_path = DATA_PROCESSED_DIR / "runner_profiles.csv"
    generate_runner_profiles(processed_records, profiles_path)
    
    logger.info("Preprocessing pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
