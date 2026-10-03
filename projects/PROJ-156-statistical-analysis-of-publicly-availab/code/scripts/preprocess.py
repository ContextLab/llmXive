import csv
import json
import logging
import os
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('code/logs/preprocess.log')
    ]
)
logger = logging.getLogger(__name__)

# Import checkpoint utilities
from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, get_checkpoint_path

# Constants
DATA_RAW_DIR = Path('data/raw')
DATA_PROCESSED_DIR = Path('data/processed')
DATA_CHECKPOINTS_DIR = Path('data/checkpoints')
CONFIG_PATH = Path('code/config.yaml')
SCHEMA_PATH = Path('contracts/run_record.schema.yaml')

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        import yaml
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except ModuleNotFoundError:
        logger.warning("PyYAML not found, attempting manual parse. This may fail for complex YAML.")
        # Simple fallback for basic YAML
        config = {}
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if value.isdigit():
                                value = int(value)
                            elif value.replace('.', '', 1).isdigit():
                                value = float(value)
                            elif value.lower() in ('true', 'false'):
                                value = value.lower() == 'true'
                            elif value.startswith('[') and value.endswith(']'):
                                # Simple list parsing
                                items = value[1:-1].split(',')
                                value = [item.strip().strip('"').strip("'") for item in items if item.strip()]
                            config[key] = value
        if not config.get('games'):
            raise ValueError("No games specified in config.yaml")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise

def load_schema() -> Dict[str, Any]:
    """Load JSON schema for validation."""
    with open(SCHEMA_PATH, 'r') as f:
        return json.load(f)

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate a single record against the schema."""
    # Basic validation - check required fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in record or record[field] is None:
            return False
    return True

def load_raw_data(game_id: str) -> List[Dict[str, Any]]:
    """Load raw JSON data for a specific game."""
    raw_file = DATA_RAW_DIR / f"{game_id}_raw.json"
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_file}")
    
    with open(raw_file, 'r') as f:
        data = json.load(f)
    
    # Handle different API response structures
    if isinstance(data, dict):
        # speedrun.com API typically returns {'runs': [...]}
        return data.get('runs', [])
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected data format in {raw_file}")

def remove_duplicates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate records based on run_id."""
    seen_ids = set()
    unique_records = []
    
    for record in records:
        run_id = record.get('id')
        if run_id and run_id not in seen_ids:
            seen_ids.add(run_id)
            unique_records.append(record)
        elif not run_id:
            logger.warning(f"Record missing ID, skipping: {record}")
    
    return unique_records

def filter_incomplete_runs(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out runs with missing critical data."""
    valid_records = []
    for record in records:
        # Check required fields
        if (record.get('run_time_seconds') is not None and 
            record.get('runner_id') is not None and
            record.get('attempt_number') is not None and
            record.get('category') is not None and
            record.get('submission_date') is not None and
            record.get('game_id') is not None):
            valid_records.append(record)
        else:
            logger.debug(f"Filtered incomplete run: {record.get('id', 'unknown')}")
    
    return valid_records

def hash_runner_id(runner_id: str, salt: str) -> str:
    """Hash runner_id with project salt for anonymization."""
    combined = f"{runner_id}{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()

def compute_runner_metrics(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Compute per-runner statistics."""
    runner_data = defaultdict(lambda: {
        'runs': [],
        'first_run_date': None,
        'games': set()
    })
    
    for record in records:
        runner_id = record['runner_id']
        submission_date = datetime.fromisoformat(record['submission_date'].replace('Z', '+00:00'))
        
        runner_data[runner_id]['runs'].append(record)
        runner_data[runner_id]['games'].add(record['game_id'])
        
        if (runner_data[runner_id]['first_run_date'] is None or 
            submission_date < runner_data[runner_id]['first_run_date']):
            runner_data[runner_id]['first_run_date'] = submission_date
    
    profiles = {}
    for runner_id, data in runner_data.items():
        profiles[runner_id] = {
            'runner_id': runner_id,
            'total_runs': len(data['runs']),
            'first_run_date': data['first_run_date'].isoformat(),
            'games_played_count': len(data['games'])
        }
    
    return profiles

def calculate_lagged_pressure(records: List[Dict[str, Any]], runner_id: str, run_date: datetime, all_records: List[Dict[str, Any]]) -> int:
    """
    Calculate lagged competitive pressure for a specific run.
    
    Args:
        records: All records in the dataset
        runner_id: The runner's ID for this run
        run_date: The submission date of this run
        all_records: The full list of records to search for context
    
    Returns:
        Count of unique active runners in the 30 days prior to this run
    """
    window_start = run_date - timedelta(days=30)
    window_end = run_date - timedelta(days=1)
    
    active_runners = set()
    
    for other_record in all_records:
        other_date = datetime.fromisoformat(other_record['submission_date'].replace('Z', '+00:00'))
        other_runner = other_record['runner_id']
        
        # Skip the current run itself
        if other_record['id'] == next((r['id'] for r in records if r['runner_id'] == runner_id and datetime.fromisoformat(r['submission_date'].replace('Z', '+00:00')) == run_date), {}).get('id'):
            continue
        
        if window_start <= other_date <= window_end:
            # Include all runners except the current one to avoid self-influence
            if other_runner != runner_id:
                active_runners.add(other_runner)
    
    return len(active_runners)

def generate_runner_profiles(runner_metrics: Dict[str, Dict[str, Any]], output_path: Path) -> None:
    """Save runner profiles to CSV."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['runner_id', 'total_runs', 'first_run_date', 'games_played_count'])
        writer.writeheader()
        for profile in runner_metrics.values():
            writer.writerow(profile)
    logger.info(f"Saved {len(runner_metrics)} runner profiles to {output_path}")

def save_to_csv(records: List[Dict[str, Any]], output_path: Path, fieldnames: List[str]) -> None:
    """Save records to CSV file."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    logger.info(f"Saved {len(records)} records to {output_path}")

def main():
    """Main preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline...")
    
    # Load configuration
    config = load_config()
    games = config['games']
    salt = config.get('salt', 'default-salt')
    checkpoint_dir = DATA_CHECKPOINTS_DIR
    
    # Ensure output directories exist
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load schema
    schema = load_schema()
    
    # Check for existing checkpoint
    checkpoint_path = get_checkpoint_path(checkpoint_dir, 'preprocess')
    checkpoint = load_checkpoint(checkpoint_path) if checkpoint_path.exists() else None
    
    completed_games = checkpoint.get('completed_games', []) if checkpoint else []
    current_index = checkpoint.get('current_game_index', 0) if checkpoint else 0
    
    all_processed_records = []
    all_runner_profiles = {}
    
    for i, game_id in enumerate(games):
        if i < current_index:
            logger.info(f"Skipping already processed game: {game_id}")
            continue
        
        logger.info(f"Processing game {i+1}/{len(games)}: {game_id}")
        
        try:
            # Load raw data
            raw_records = load_raw_data(game_id)
            logger.info(f"Loaded {len(raw_records)} raw records for {game_id}")
            
            # Remove duplicates
            unique_records = remove_duplicates(raw_records)
            logger.info(f"Removed duplicates: {len(unique_records)} remaining")
            
            # Filter incomplete runs
            valid_records = filter_incomplete_runs(unique_records)
            retention_rate = len(valid_records) / len(raw_records) if raw_records else 0
            logger.info(f"Retention rate: {retention_rate:.2%} ({len(valid_records)}/{len(raw_records)})")
            
            if retention_rate < 0.95:
                logger.warning(f"Retention rate below 95% for {game_id}: {retention_rate:.2%}")
            
            # Hash runner IDs
            for record in valid_records:
                original_id = record['runner_id']
                record['runner_id'] = hash_runner_id(original_id, salt)
                record['game_id'] = game_id
            
            # Compute runner metrics
            game_profiles = compute_runner_metrics(valid_records)
            all_runner_profiles.update(game_profiles)
            
            # Calculate lagged competitive pressure
            # First, combine with previously processed records for context
            combined_records = all_processed_records + valid_records
            
            for record in valid_records:
                run_date = datetime.fromisoformat(record['submission_date'].replace('Z', '+00:00'))
                lagged_pressure = calculate_lagged_pressure(
                    combined_records, 
                    record['runner_id'], 
                    run_date, 
                    combined_records
                )
                record['lagged_competitive_pressure'] = lagged_pressure
            
            # Add to all processed records
            all_processed_records.extend(valid_records)
            
            # Save checkpoint after each game
            checkpoint_data = {
                'completed_games': games[:i+1],
                'current_game_index': i + 1,
                'total_records_processed': len(all_processed_records),
                'timestamp': datetime.now().isoformat()
            }
            save_checkpoint(checkpoint_dir, 'preprocess', checkpoint_data)
            
        except Exception as e:
            logger.error(f"Error processing game {game_id}: {e}")
            raise
    
    # Save final outputs
    run_records_path = DATA_PROCESSED_DIR / 'run_records.csv'
    fieldnames = ['id', 'run_time_seconds', 'runner_id', 'attempt_number', 'category', 'submission_date', 'game_id', 'lagged_competitive_pressure']
    save_to_csv(all_processed_records, run_records_path, fieldnames)
    
    runner_profiles_path = DATA_PROCESSED_DIR / 'runner_profiles.csv'
    generate_runner_profiles(all_runner_profiles, runner_profiles_path)
    
    logger.info("Preprocessing pipeline completed successfully!")
    logger.info(f"Total records processed: {len(all_processed_records)}")
    logger.info(f"Total unique runners: {len(all_runner_profiles)}")

if __name__ == '__main__':
    main()