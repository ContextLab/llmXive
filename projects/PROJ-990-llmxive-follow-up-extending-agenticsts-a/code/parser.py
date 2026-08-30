import os
import json
import logging
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/parser.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
SCHEMA_FILE = Path("contracts/trajectory.schema.yaml")
OUTPUT_FILE = PROCESSED_DATA_DIR / "metrics_with_moves.csv"
CHECKSUM_FILE = PROCESSED_DATA_DIR / "data_checksums.json"

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_checksums() -> Dict[str, str]:
    """Load existing checksums from disk."""
    if CHECKSUM_FILE.exists():
        with open(CHECKSUM_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to disk."""
    with open(CHECKSUM_FILE, 'w') as f:
        json.dump(checksums, f, indent=2)

def validate_data_source() -> bool:
    """Check if raw data exists and is not empty."""
    if not RAW_DATA_DIR.exists():
        logger.error(f"Raw data directory {RAW_DATA_DIR} does not exist.")
        return False
    
    jsonl_files = list(RAW_DATA_DIR.glob("*.jsonl"))
    json_files = list(RAW_DATA_DIR.glob("*.json"))
    all_files = jsonl_files + json_files
    
    if not all_files:
        logger.error(f"No JSON/JSONL files found in {RAW_DATA_DIR}.")
        return False
    
    # Check if files are empty
    for file_path in all_files:
        if file_path.stat().st_size == 0:
            logger.error(f"File {file_path} is empty.")
            return False
    
    return True

def load_schema() -> Dict[str, Any]:
    """Load the trajectory schema from YAML file."""
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file {SCHEMA_FILE} not found. Run T003a first.")
    
    with open(SCHEMA_FILE, 'r') as f:
        return yaml.safe_load(f)

def validate_trajectory_against_schema(trajectory: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a trajectory against the schema."""
    errors = []
    
    # Check required top-level fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in trajectory:
            errors.append(f"Missing required field: {field}")
    
    # Check trajectory structure
    if 'turns' in trajectory:
        if not isinstance(trajectory['turns'], list):
            errors.append("'turns' must be a list")
        else:
            for i, turn in enumerate(trajectory['turns']):
                if not isinstance(turn, dict):
                    errors.append(f"Turn {i} must be a dictionary")
                    continue
                
                # Check required turn fields if specified
                turn_required = schema.get('properties', {}).get('turns', {}).get('items', {}).get('required', [])
                for field in turn_required:
                    if field not in turn:
                        errors.append(f"Turn {i} missing required field: {field}")
    
    return len(errors) == 0, errors

def extract_metrics_from_trajectory(trajectory: Dict[str, Any], trajectory_id: str) -> List[Dict[str, Any]]:
    """Extract per-turn metrics from a trajectory."""
    metrics = []
    
    turns = trajectory.get('turns', [])
    if not turns:
        logger.warning(f"No turns found in trajectory {trajectory_id}")
        return metrics
    
    for turn_idx, turn in enumerate(turns):
        # Extract available metrics
        metric_row = {
            'trajectory_id': trajectory_id,
            'turn': turn_idx,
            'timestamp': turn.get('timestamp', None),
            'action': turn.get('action', None),
            'observation': turn.get('observation', None),
            'reward': turn.get('reward', None),
            'done': turn.get('done', False),
            'legal_moves': turn.get('legal_moves', []),
            'selected_move': turn.get('selected_move', None),
            'context_tokens': turn.get('context_tokens', None),
            'response_tokens': turn.get('response_tokens', None),
            'total_tokens': turn.get('total_tokens', None),
            'layer_used': turn.get('layer_used', None),
            'confidence': turn.get('confidence', None),
        }
        
        # Calculate derived metrics
        if metric_row['legal_moves'] and isinstance(metric_row['legal_moves'], list):
            metric_row['num_legal_moves'] = len(metric_row['legal_moves'])
        else:
            metric_row['num_legal_moves'] = 0
        
        metrics.append(metric_row)
    
    return metrics

def parse_trajectories() -> pd.DataFrame:
    """Parse all trajectories from raw data and extract metrics."""
    if not validate_data_source():
        raise FileNotFoundError("Real data missing; pipeline cannot proceed.")
    
    schema = load_schema()
    all_metrics = []
    checksums = load_existing_checksums()
    files_processed = 0
    
    # Process JSONL files
    jsonl_files = list(RAW_DATA_DIR.glob("*.jsonl"))
    for file_path in jsonl_files:
        current_checksum = compute_file_checksum(file_path)
        
        # Check if file has been processed
        if file_path.name in checksums and checksums[file_path.name] == current_checksum:
            logger.info(f"Skipping {file_path.name} (already processed)")
            continue
        
        logger.info(f"Processing {file_path.name}")
        
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        trajectory = json.loads(line)
                        
                        # Validate against schema
                        is_valid, errors = validate_trajectory_against_schema(trajectory, schema)
                        if not is_valid:
                            logger.error(f"Schema validation failed for {file_path.name}:{line_num}: {errors}")
                            raise ValueError(f"Schema mismatch: {errors}")
                        
                        # Extract trajectory ID
                        trajectory_id = trajectory.get('trajectory_id', f"{file_path.stem}_{line_num}")
                        
                        # Extract metrics
                        metrics = extract_metrics_from_trajectory(trajectory, trajectory_id)
                        all_metrics.extend(metrics)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error in {file_path.name}:{line_num}: {e}")
                        raise
        
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            raise
        
        checksums[file_path.name] = current_checksum
        files_processed += 1
    
    # Process JSON files (assuming they contain a list of trajectories)
    json_files = list(RAW_DATA_DIR.glob("*.json"))
    for file_path in json_files:
        current_checksum = compute_file_checksum(file_path)
        
        if file_path.name in checksums and checksums[file_path.name] == current_checksum:
            logger.info(f"Skipping {file_path.name} (already processed)")
            continue
        
        logger.info(f"Processing {file_path.name}")
        
        try:
            with open(file_path, 'r') as f:
                trajectories = json.load(f)
                
                if not isinstance(trajectories, list):
                    logger.warning(f"{file_path.name} does not contain a list of trajectories, treating as single trajectory")
                    trajectories = [trajectories]
                
                for idx, trajectory in enumerate(trajectories):
                    # Validate against schema
                    is_valid, errors = validate_trajectory_against_schema(trajectory, schema)
                    if not is_valid:
                        logger.error(f"Schema validation failed for {file_path.name}[{idx}]: {errors}")
                        raise ValueError(f"Schema mismatch: {errors}")
                    
                    trajectory_id = trajectory.get('trajectory_id', f"{file_path.stem}_{idx}")
                    metrics = extract_metrics_from_trajectory(trajectory, trajectory_id)
                    all_metrics.extend(metrics)
        
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            raise
        
        checksums[file_path.name] = current_checksum
        files_processed += 1
    
    if files_processed == 0:
        logger.warning("No files were processed. Check if data was already processed or if data is missing.")
        if not all_metrics:
            raise FileNotFoundError("No valid trajectories found to process.")
    
    # Create DataFrame
    df = pd.DataFrame(all_metrics)
    
    if df.empty:
        logger.error("No metrics extracted. Check input data format.")
        raise ValueError("No metrics extracted from trajectories.")
    
    # Ensure output directory exists
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save checksums
    save_checksums(checksums)
    
    logger.info(f"Parsed {len(df)} turns from {files_processed} files")
    return df

def main():
    """Main entry point for the parser."""
    try:
        logger.info("Starting trajectory parsing...")
        df = parse_trajectories()
        df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Successfully wrote {len(df)} rows to {OUTPUT_FILE}")
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except ValueError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
