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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
CONTRACTS_DIR = Path("contracts")
SCHEMA_FILE = CONTRACTS_DIR / "trajectory.schema.yaml"
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
    """Load existing checksums if the file exists."""
    if CHECKSUM_FILE.exists():
        with open(CHECKSUM_FILE, "r") as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to file."""
    with open(CHECKSUM_FILE, "w") as f:
        json.dump(checksums, f, indent=2)

def validate_data_source() -> None:
    """
    Validate that the raw data source exists and is not empty.
    Raises FileNotFoundError if data is missing.
    """
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Real data missing; pipeline cannot proceed. Directory {RAW_DATA_DIR} does not exist.")
    
    jsonl_files = list(RAW_DATA_DIR.glob("*.jsonl"))
    json_files = list(RAW_DATA_DIR.glob("*.json"))
    
    if not jsonl_files and not json_files:
        raise FileNotFoundError(f"Real data missing; pipeline cannot proceed. No JSON/JSONL files found in {RAW_DATA_DIR}.")

def load_schema() -> Dict[str, Any]:
    """Load the trajectory schema from the contracts directory."""
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file missing: {SCHEMA_FILE}. Run T003a first.")
    
    with open(SCHEMA_FILE, "r") as f:
        return yaml.safe_load(f)

def validate_trajectory_against_schema(trajectory: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a single trajectory against the schema.
    Raises ValueError if schema mismatch is found.
    """
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    
    # Check required fields
    for field in required_fields:
        if field not in trajectory:
            raise ValueError(f"Trajectory missing required field: {field}")
    
    # Basic type validation for known fields
    if "trajectory_id" in trajectory and not isinstance(trajectory["trajectory_id"], str):
        raise ValueError(f"trajectory_id must be a string, got {type(trajectory['trajectory_id'])}")
    
    if "turns" in trajectory:
        if not isinstance(trajectory["turns"], list):
            raise ValueError(f"turns must be a list, got {type(trajectory['turns'])}")
        
        for turn_idx, turn in enumerate(trajectory["turns"]):
            if not isinstance(turn, dict):
                raise ValueError(f"Turn {turn_idx} must be a dictionary")
            
            # Check for legal_moves if defined in schema
            if "legal_moves" in properties.get("turns", {}).get("items", {}).get("properties", {}):
                if "legal_moves" not in turn:
                    raise ValueError(f"Turn {turn_idx} missing required field: legal_moves")
                if not isinstance(turn["legal_moves"], list):
                    raise ValueError(f"Turn {turn_idx} legal_moves must be a list")
    
    return True

def extract_metrics_from_trajectory(trajectory: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract per-turn metrics from a trajectory.
    Returns a list of rows ready for CSV export.
    """
    rows = []
    trajectory_id = trajectory.get("trajectory_id", "unknown")
    turns = trajectory.get("turns", [])
    
    for turn_idx, turn in enumerate(turns):
        turn_id = turn.get("turn_id", turn_idx)
        
        # Extract legal moves
        legal_moves = turn.get("legal_moves", [])
        legal_moves_count = len(legal_moves)
        legal_moves_str = json.dumps(legal_moves) if legal_moves else "[]"
        
        # Extract other potential metrics
        action = turn.get("action", "")
        reward = turn.get("reward", 0.0)
        done = turn.get("done", False)
        state_hash = turn.get("state_hash", "")
        
        row = {
            "trajectory_id": trajectory_id,
            "turn_id": turn_id,
            "legal_moves": legal_moves_str,
            "legal_moves_count": legal_moves_count,
            "action": action,
            "reward": reward,
            "done": done,
            "state_hash": state_hash
        }
        rows.append(row)
    
    return rows

def parse_trajectories() -> pd.DataFrame:
    """
    Main function to parse all trajectories from raw data.
    Validates against schema and extracts metrics.
    Returns a DataFrame with all extracted metrics.
    """
    # Validate data source
    validate_data_source()
    
    # Load schema
    schema = load_schema()
    
    # Load existing checksums
    existing_checksums = load_existing_checksums()
    
    all_rows = []
    current_checksums = {}
    
    # Process JSONL files
    jsonl_files = list(RAW_DATA_DIR.glob("*.jsonl"))
    for file_path in jsonl_files:
        file_key = str(file_path.relative_to(RAW_DATA_DIR))
        current_checksum = compute_file_checksum(file_path)
        current_checksums[file_key] = current_checksum
        
        # Skip if checksum matches (optimization)
        if existing_checksums.get(file_key) == current_checksum:
            logger.info(f"Skipping {file_key} (checksum match)")
            continue
        
        logger.info(f"Processing {file_path}")
        
        try:
            with open(file_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        trajectory = json.loads(line)
                        # Validate against schema
                        validate_trajectory_against_schema(trajectory, schema)
                        # Extract metrics
                        rows = extract_metrics_from_trajectory(trajectory)
                        all_rows.extend(rows)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON at line {line_num} in {file_path}: {e}")
                    except ValueError as e:
                        logger.error(f"Schema validation failed for trajectory at line {line_num} in {file_path}: {e}")
                        raise
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    # Process JSON files (assuming list of trajectories)
    json_files = list(RAW_DATA_DIR.glob("*.json"))
    for file_path in json_files:
        file_key = str(file_path.relative_to(RAW_DATA_DIR))
        current_checksum = compute_file_checksum(file_path)
        current_checksums[file_key] = current_checksum
        
        # Skip if checksum matches
        if existing_checksums.get(file_key) == current_checksum:
            logger.info(f"Skipping {file_key} (checksum match)")
            continue
        
        logger.info(f"Processing {file_path}")
        
        try:
            with open(file_path, "r") as f:
                trajectories = json.load(f)
                
            if not isinstance(trajectories, list):
                trajectories = [trajectories]
            
            for trajectory in trajectories:
                validate_trajectory_against_schema(trajectory, schema)
                rows = extract_metrics_from_trajectory(trajectory)
                all_rows.extend(rows)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    # Update checksums
    save_checksums(current_checksums)
    
    if not all_rows:
        logger.warning("No valid trajectory data extracted. Output CSV will be header-only.")
    
    # Create DataFrame
    df = pd.DataFrame(all_rows)
    
    # Ensure columns are in expected order
    expected_columns = [
        "trajectory_id", "turn_id", "legal_moves", "legal_moves_count",
        "action", "reward", "done", "state_hash"
    ]
    
    # Reorder columns if they exist, otherwise just use what we have
    existing_cols = [col for col in expected_columns if col in df.columns]
    other_cols = [col for col in df.columns if col not in expected_columns]
    df = df[existing_cols + other_cols]
    
    return df

def main():
    """Entry point for the parser script."""
    logger.info("Starting trajectory parsing phase (T006a)")
    
    try:
        # Ensure output directory exists
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Parse trajectories
        df = parse_trajectories()
        
        # Save to CSV
        df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Parsing complete. Output saved to {OUTPUT_FILE}")
        logger.info(f"Total rows extracted: {len(df)}")
        
        return 0
    except FileNotFoundError as e:
        logger.error(f"Data source error: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during parsing: {e}")
        raise

if __name__ == "__main__":
    main()