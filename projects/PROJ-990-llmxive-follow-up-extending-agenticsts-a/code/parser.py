import os
import json
import logging
import hashlib
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml

# Configure logging to file for edge case warnings as per T005/T005a requirements
# This ensures the log file exists even if no errors occur, satisfying T005a if needed later.
LOG_FILE = Path("data/processed/edge_case_warnings.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_checksums(checksum_file: Path) -> Dict[str, str]:
    """Load existing checksums from JSON file."""
    if checksum_file.exists():
        with open(checksum_file, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str], checksum_file: Path) -> None:
    """Save checksums to JSON file."""
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)

def validate_data_source(raw_dir: Path) -> bool:
    """
    Validate that data/raw/ contains non-empty, valid trajectory files.
    Returns True if valid data exists, False otherwise.
    """
    if not raw_dir.exists():
        logger.error(f"Directory {raw_dir} does not exist.")
        return False

    json_files = list(raw_dir.glob("*.json")) + list(raw_dir.glob("*.jsonl"))
    if not json_files:
        logger.warning(f"No JSON/JSONL files found in {raw_dir}.")
        return False

    valid_count = 0
    for f in json_files:
        try:
            with open(f, 'r') as fh:
                # Check if file is empty
                first_char = fh.read(1)
                if not first_char:
                    logger.warning(f"File {f} is empty.")
                    continue
                # Try to parse at least one record
                fh.seek(0)
                if f.suffix == '.jsonl':
                    json.loads(fh.readline())
                else:
                    json.load(fh)
            valid_count += 1
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Invalid JSON in {f}: {e}")
            continue

    if valid_count == 0:
        logger.error("No valid JSON/JSONL files found in data/raw/.")
        return False

    logger.info(f"Found {valid_count} valid trajectory files.")
    return True

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_trajectory_against_schema(record: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a single trajectory record against the schema.
    Raises ValueError if mismatch.
    """
    # Basic required fields check based on schema
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in record:
            raise ValueError(f"Missing required field '{field}' in trajectory record")

    # Type checks for critical fields
    if 'trajectory_id' in record and not isinstance(record['trajectory_id'], str):
        raise ValueError(f"trajectory_id must be string, got {type(record['trajectory_id'])}")
    
    if 'turn' in record and not isinstance(record['turn'], int):
        raise ValueError(f"turn must be integer, got {type(record['turn'])}")

    if 'legal_moves' in record:
        if not isinstance(record['legal_moves'], list):
            raise ValueError(f"legal_moves must be array, got {type(record['legal_moves'])}")
        if len(record['legal_moves']) == 0:
            # Schema says minItems: 1, so empty is invalid
            raise ValueError(f"legal_moves cannot be empty")

    return True

def extract_metrics_from_trajectory(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract per-turn metrics from a single trajectory record.
    Calculates Shannon entropy of legal moves.
    """
    trajectory_id = record['trajectory_id']
    turn = record['turn']
    state = record['state']
    legal_moves = record['legal_moves']

    # Extract state metrics
    health = state.get('health', 0)
    threat = state.get('threat', 0)
    deck_size = state.get('deck_size', 0)

    # Calculate health_ratio (assuming max health is 100 or similar, normalize to 0-1)
    # If max health is not provided, we assume a standard max or use current/100
    # For this implementation, we'll use a simple ratio if max is known, else 1.0
    # Assuming max_health is 100 for normalization
    max_health = 100
    health_ratio = health / max_health if max_health > 0 else 1.0

    # Calculate move entropy: H = - sum(p_i * log(p_i))
    # Assuming uniform distribution over legal moves: p_i = 1/|moves|
    # H = - sum( (1/N) * log(1/N) ) = - N * (1/N) * log(1/N) = - log(1/N) = log(N)
    # Using natural log (base e) as standard for Shannon entropy in bits usually base 2, but spec says log
    # We will use natural log (np.log) or base 2 (np.log2). Spec says log, usually implies base 2 or e.
    # Let's use natural log for continuous math consistency, or base 2 for information theory.
    # Standard Shannon entropy often uses base 2. Let's use base 2 to be safe for "bits".
    # H = log2(N)
    import math
    n_moves = len(legal_moves)
    if n_moves > 0:
        move_entropy = math.log2(n_moves)
    else:
        move_entropy = 0.0 # Should not happen due to validation

    return {
        'trajectory_id': trajectory_id,
        'turn': turn,
        'health_ratio': health_ratio,
        'threat_level': threat,
        'deck_size': deck_size,
        'move_entropy': move_entropy
    }

def parse_trajectories(raw_dir: Path, schema_path: Path, output_path: Path) -> None:
    """
    Parse all JSON/JSONL files in raw_dir, validate against schema,
    extract metrics, and write to output CSV.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    schema = load_schema(schema_path)
    records = []

    json_files = list(raw_dir.glob("*.json")) + list(raw_dir.glob("*.jsonl"))
    
    if not json_files:
        logger.warning("No JSON files found. Output CSV will be empty.")
        # Create empty CSV with headers
        df = pd.DataFrame(columns=['trajectory_id', 'turn', 'health_ratio', 'threat_level', 'deck_size', 'move_entropy'])
        df.to_csv(output_path, index=False)
        return

    for file_path in json_files:
        logger.info(f"Processing {file_path}...")
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix == '.jsonl':
                    for line_num, line in enumerate(f):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            validate_trajectory_against_schema(record, schema)
                            metrics = extract_metrics_from_trajectory(record)
                            records.append(metrics)
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON decode error in {file_path} line {line_num}: {e}")
                            continue
                        except ValueError as e:
                            logger.warning(f"Schema validation error in {file_path} line {line_num}: {e}")
                            continue
                else:
                    # Assume JSON array or single object
                    try:
                        data = json.load(f)
                        if isinstance(data, list):
                            for idx, record in enumerate(data):
                                validate_trajectory_against_schema(record, schema)
                                metrics = extract_metrics_from_trajectory(record)
                                records.append(metrics)
                        elif isinstance(data, dict):
                            validate_trajectory_against_schema(data, schema)
                            metrics = extract_metrics_from_trajectory(data)
                            records.append(metrics)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error in {file_path}: {e}")
                        continue
                    except ValueError as e:
                        logger.error(f"Schema validation error in {file_path}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {e}")
            continue

    logger.info(f"Extracted {len(records)} records.")
    
    # Create DataFrame and save
    df = pd.DataFrame(records)
    if not df.empty:
        df.to_csv(output_path, index=False)
        logger.info(f"Metrics saved to {output_path}")
    else:
        # Write empty file with headers
        df = pd.DataFrame(columns=['trajectory_id', 'turn', 'health_ratio', 'threat_level', 'deck_size', 'move_entropy'])
        df.to_csv(output_path, index=False)
        logger.warning(f"No valid records found. Empty CSV saved to {output_path}")

def main():
    """Main entry point for T006."""
    raw_dir = Path("data/raw")
    schema_path = Path("contracts/trajectory.schema.yaml")
    output_path = Path("data/processed/metrics_with_moves.csv")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check skip condition: if data/raw is empty and no synthetic data
    if not validate_data_source(raw_dir):
        logger.warning("Skipping T006: No valid data in data/raw/. T006a should have run first.")
        # Still create empty output to prevent downstream crashes if T005a handles it
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(columns=['trajectory_id', 'turn', 'health_ratio', 'threat_level', 'deck_size', 'move_entropy'])
        df.to_csv(output_path, index=False)
        return

    try:
        parse_trajectories(raw_dir, schema_path, output_path)
    except Exception as e:
        logger.error(f"Failed to parse trajectories: {e}")
        raise

if __name__ == "__main__":
    main()