import csv
import json
import logging
import os
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Import checkpoint utilities from the shared utils module
from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, get_checkpoint_path

# Import logging setup from fetch_data to ensure consistent logging behavior
# We will re-implement setup_logging here to ensure the log directory exists before use
def setup_logging(script_name: str) -> logging.Logger:
    """Configure logging for the script, ensuring the log directory exists."""
    log_dir = Path("code/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"{script_name}.log"
    
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates in repeated runs
    if logger.hasHandlers():
        logger.handlers.clear()
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    logger.addHandler(fh)
    
    return logger

def load_config():
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Simple YAML parser for basic key-value and list structures
    config = {}
    with open(config_path, 'r') as f:
        lines = f.readlines()
        
    current_key = None
    current_list = []
    
    for line in lines:
        line = line.rstrip()
        if not line or line.startswith('#'):
            continue
        
        if line.startswith('  - '):
            # List item
            if current_key:
                current_list.append(line[4:].strip().strip('"').strip("'"))
        elif ':' in line:
            # New key
            if current_key and current_list:
                config[current_key] = current_list
                current_list = []
            
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            
            if value:
                # Simple key: value
                config[key] = value
            else:
                # Key expecting a list
                current_key = key
                current_list = []
    
    if current_key and current_list:
        config[current_key] = current_list
        
    return config

def load_schema():
    schema_path = Path("contracts/run_record.schema.yaml")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # In a real implementation, we would parse the YAML schema and validate
    # For now, we return a basic structure
    return {
        "required": ["run_time_seconds", "runner_id", "attempt_number", "category", "submission_date", "game_id"]
    }

def validate_record(record, schema):
    for field in schema.get("required", []):
        if field not in record:
            return False, f"Missing required field: {field}"
    return True, None

def load_raw_data(game_id):
    raw_path = Path(f"data/raw/{game_id}_raw.json")
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data not found for game {game_id}: {raw_path}")
    
    with open(raw_path, 'r') as f:
        data = json.load(f)
    
    return data.get('runs', [])

def remove_duplicates(runs):
    seen = set()
    unique_runs = []
    for run in runs:
        # Create a unique key based on run ID and submission date
        key = (run.get('id'), run.get('submission_date'))
        if key not in seen:
            seen.add(key)
            unique_runs.append(run)
    return unique_runs

def filter_incomplete_runs(runs, schema):
    filtered = []
    for run in runs:
        is_valid, reason = validate_record(run, schema)
        if is_valid:
            filtered.append(run)
        else:
            logging.debug(f"Filtered incomplete run: {reason}")
    return filtered

def hash_runner_id(runner_id, salt):
    """Hash runner_id with salt for anonymization."""
    combined = f"{runner_id}{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()

def compute_runner_metrics(runs, runner_id_map):
    """Compute total_prior_runs and time_since_first_run_days for each runner."""
    runner_data = defaultdict(list)
    
    for run in runs:
        original_id = run.get('runner_id')
        hashed_id = runner_id_map.get(original_id, hash_runner_id(original_id, "default"))
        runner_data[hashed_id].append({
            'submission_date': datetime.fromisoformat(run['submission_date'].replace('Z', '+00:00')),
            'game_id': run['game_id']
        })
    
    profiles = {}
    for runner_id, runs_list in runner_data.items():
        runs_list.sort(key=lambda x: x['submission_date'])
        total_prior = len(runs_list)
        time_span = (runs_list[-1]['submission_date'] - runs_list[0]['submission_date']).days
        games_played = len(set(r['game_id'] for r in runs_list))
        
        profiles[runner_id] = {
            'total_prior_runs': total_prior,
            'time_since_first_run_days': time_span,
            'games_played_count': games_played
        }
    
    return profiles

def calculate_lagged_pressure(runs, runner_id_map, window_days=30):
    """Calculate lagged competitive pressure for each run."""
    # Group runs by date and runner
    runs_by_date = defaultdict(list)
    for run in runs:
        date = datetime.fromisoformat(run['submission_date'].replace('Z', '+00:00')).date()
        runs_by_date[date].append(run)
    
    sorted_dates = sorted(runs_by_date.keys())
    
    # Pre-calculate cumulative runner sets
    cumulative_runners = {}
    current_runners = set()
    
    for date in sorted_dates:
        for run in runs_by_date[date]:
            original_id = run.get('runner_id')
            hashed_id = runner_id_map.get(original_id, hash_runner_id(original_id, "default"))
            current_runners.add(hashed_id)
        cumulative_runners[date] = current_runners.copy()
    
    # Calculate pressure for each run
    for run in runs:
        run_date = datetime.fromisoformat(run['submission_date'].replace('Z', '+00:00')).date()
        start_date = run_date - timedelta(days=window_days)
        end_date = run_date - timedelta(days=1)
        
        # Count unique runners in the window
        unique_runners = set()
        for date in sorted_dates:
            if start_date <= date <= end_date:
                for r in runs_by_date[date]:
                    original_id = r.get('runner_id')
                    hashed_id = runner_id_map.get(original_id, hash_runner_id(original_id, "default"))
                    unique_runners.add(hashed_id)
        
        run['lagged_competitive_pressure'] = len(unique_runners)
    
    return runs

def generate_runner_profiles(runs, runner_id_map):
    """Generate runner profiles from processed runs."""
    profiles = compute_runner_metrics(runs, runner_id_map)
    return profiles

def save_to_csv(data, output_path, fieldnames):
    """Save data to CSV file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    """Main preprocessing pipeline with checkpoint support."""
    logger = setup_logging("preprocess")
    logger.info("Starting preprocessing pipeline")
    
    config = load_config()
    games = config.get('games', [])
    salt = config.get('salt', 'default_salt')
    min_sample_size = config.get('min_sample_size', 100)
    
    # Initialize checkpoint path
    checkpoint_path = get_checkpoint_path("preprocess")
    checkpoint_data = load_checkpoint(checkpoint_path)
    
    # Determine starting point
    start_game_idx = 0
    processed_runs = []
    all_runner_profiles = {}
    
    if checkpoint_data:
        logger.info(f"Resuming from checkpoint. Last processed game index: {checkpoint_data.get('last_game_idx', 0)}")
        start_game_idx = checkpoint_data.get('last_game_idx', 0)
        processed_runs = checkpoint_data.get('processed_runs', [])
        all_runner_profiles = checkpoint_data.get('runner_profiles', {})
    
    # Process games
    for idx in range(start_game_idx, len(games)):
        game_id = games[idx]
        logger.info(f"Processing game: {game_id}")
        
        try:
            # Load raw data
            raw_runs = load_raw_data(game_id)
            logger.info(f"Loaded {len(raw_runs)} runs for {game_id}")
            
            # Remove duplicates
            unique_runs = remove_duplicates(raw_runs)
            logger.info(f"Removed duplicates. Remaining: {len(unique_runs)}")
            
            # Filter incomplete runs
            schema = load_schema()
            valid_runs = filter_incomplete_runs(unique_runs, schema)
            logger.info(f"Filtered incomplete runs. Remaining: {len(valid_runs)}")
            
            # Hash runner IDs
            runner_id_map = {}
            for run in valid_runs:
                original_id = run.get('runner_id')
                if original_id:
                    hashed_id = hash_runner_id(original_id, salt)
                    runner_id_map[original_id] = hashed_id
                    run['runner_id'] = hashed_id
            
            # Compute runner metrics
            profiles = compute_runner_metrics(valid_runs, runner_id_map)
            
            # Calculate lagged pressure
            valid_runs = calculate_lagged_pressure(valid_runs, runner_id_map)
            
            # Merge profiles into runs
            for run in valid_runs:
                hashed_id = run.get('runner_id')
                if hashed_id in profiles:
                    run['total_prior_runs'] = profiles[hashed_id]['total_prior_runs']
                    run['time_since_first_run_days'] = profiles[hashed_id]['time_since_first_run_days']
            
            # Update global state
            processed_runs.extend(valid_runs)
            all_runner_profiles.update(profiles)
            
            # Save checkpoint after each game
            checkpoint_data = {
                'last_game_idx': idx + 1,
                'processed_runs': processed_runs,
                'runner_profiles': all_runner_profiles,
                'timestamp': datetime.now().isoformat()
            }
            save_checkpoint(checkpoint_path, checkpoint_data)
            logger.info(f"Checkpoint saved after processing game {game_id}")
            
        except Exception as e:
            logger.error(f"Error processing game {game_id}: {e}")
            raise
    
    # Save final outputs
    logger.info("Saving final outputs")
    
    # Save run records
    run_record_fieldnames = [
        'run_time_seconds', 'runner_id', 'attempt_number', 'category', 
        'submission_date', 'game_id', 'total_prior_runs', 
        'time_since_first_run_days', 'lagged_competitive_pressure'
    ]
    save_to_csv(processed_runs, "data/processed/run_records.csv", run_record_fieldnames)
    
    # Save runner profiles
    profile_fieldnames = ['runner_id', 'total_prior_runs', 'time_since_first_run_days', 'games_played_count']
    profile_data = [
        {'runner_id': k, **v} for k, v in all_runner_profiles.items()
    ]
    save_to_csv(profile_data, "data/processed/runner_profiles.csv", profile_fieldnames)
    
    logger.info("Preprocessing pipeline completed successfully")
    
    # Clean up checkpoint on successful completion
    if Path(checkpoint_path).exists():
        os.remove(checkpoint_path)
        logger.info("Checkpoint file removed after successful completion")

if __name__ == "__main__":
    main()
