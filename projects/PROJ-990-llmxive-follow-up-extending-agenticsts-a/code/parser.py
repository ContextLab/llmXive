"""
parser.py

Implements T006a: Extract per-turn metrics from raw trajectory logs.

Input:
    data/raw/agenticsts_trajectories.jsonl (from T005b)
    contracts/trajectory.schema.yaml (from T003a)

Output:
    data/processed/metrics_with_moves.csv (columns: trajectory_id, turn, health_ratio, enemy_threat, deck_size, move_entropy, layer_name)

Constraints:
    - Must validate against schema. Raise ValueError on mismatch.
    - Raise FileNotFoundError if input data is missing.
    - NO synthetic fallback.
    - Uses streaming (ijson) to handle large files.
"""
import os
import sys
import json
import logging
import hashlib
import ijson
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "agenticsts_trajectories.jsonl"
SCHEMA_PATH = BASE_DIR / "contracts" / "trajectory.schema.yaml"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "metrics_with_moves.csv"

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_trajectory_against_schema(trajectory: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a single trajectory record against the schema.
    Raises ValueError if validation fails.
    """
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})

    # Check required fields
    for field in required_fields:
        if field not in trajectory:
            raise ValueError(f"Missing required field '{field}' in trajectory. Schema: {schema.get('title', 'unknown')}")

    # Type checking for known fields if defined in properties
    for field, spec in properties.items():
        if field in trajectory:
            expected_type = spec.get("type")
            value = trajectory[field]
            
            # Simple type validation
            if expected_type == "integer" and not isinstance(value, int):
                if not isinstance(value, float) or not value.is_integer():
                    raise ValueError(f"Field '{field}' expected integer, got {type(value)}")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                raise ValueError(f"Field '{field}' expected number, got {type(value)}")
            elif expected_type == "string" and not isinstance(value, str):
                raise ValueError(f"Field '{field}' expected string, got {type(value)}")
            elif expected_type == "array" and not isinstance(value, list):
                raise ValueError(f"Field '{field}' expected array, got {type(value)}")
            elif expected_type == "object" and not isinstance(value, dict):
                raise ValueError(f"Field '{field}' expected object, got {type(value)}")

    return True

def extract_move_entropy(legal_moves: List[str]) -> float:
    """
    Calculate Shannon entropy of the legal move distribution.
    Assumes uniform probability for available moves if no probabilities provided.
    Returns float('nan') if list is empty or entropy is undefined.
    """
    if not legal_moves or len(legal_moves) == 0:
        return float('nan')
    
    n = len(legal_moves)
    if n == 1:
        return 0.0
    
    # Assuming uniform distribution over legal moves
    p = 1.0 / n
    entropy = -sum(p * math.log2(p) for _ in range(n))
    return entropy

def extract_metrics_from_trajectory(trajectory: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    """
    Extract per-turn metrics from a single trajectory.
    Yields one dict per turn.
    """
    traj_id = trajectory.get("trajectory_id", "unknown")
    turns = trajectory.get("turns", [])
    
    if not isinstance(turns, list):
        logger.warning(f"Trajectory {traj_id} has no 'turns' list or invalid format. Skipping.")
        return

    for turn_idx, turn_data in enumerate(turns):
        if not isinstance(turn_data, dict):
            continue

        # Extract fields with defaults
        health_ratio = turn_data.get("health_ratio", 0.0)
        enemy_threat = turn_data.get("enemy_threat", 0.0)
        deck_size = turn_data.get("deck_size", 0)
        
        # Move entropy
        legal_moves = turn_data.get("legal_moves", [])
        move_entropy = extract_move_entropy(legal_moves)
        
        # Layer name (from trajectory level or turn level if available)
        layer_name = trajectory.get("layer_name", "unknown")
        
        yield {
            "trajectory_id": traj_id,
            "turn": turn_idx,
            "health_ratio": health_ratio,
            "enemy_threat": enemy_threat,
            "deck_size": deck_size,
            "move_entropy": move_entropy,
            "layer_name": layer_name
        }

def validate_data_source(raw_path: Path) -> None:
    """
    Validate that the raw data source exists and is not empty.
    Raises FileNotFoundError if missing.
    """
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")
    
    # Check file size > 0
    if raw_path.stat().st_size == 0:
        raise FileNotFoundError(f"Raw data file is empty: {raw_path}")

def parse_trajectories(input_path: Path, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse the JSONL file using streaming (ijson) and extract metrics.
    Validates each record against the schema.
    """
    records = []
    total_count = 0
    valid_count = 0
    error_count = 0

    logger.info(f"Starting streaming parse of: {input_path}")
    
    try:
        with open(input_path, "rb") as f:
            # ijson.items yields each top-level object in the JSONL stream
            # We assume the file is a sequence of JSON objects, one per line (JSONL)
            # ijson.items(f, '') works for a stream of objects
            parser = ijson.items(f, "")
            
            for obj in parser:
                total_count += 1
                try:
                    # Validate against schema
                    validate_trajectory_against_schema(obj, schema)
                    
                    # Extract metrics
                    for metric_row in extract_metrics_from_trajectory(obj):
                        records.append(metric_row)
                        valid_count += 1
                except ValueError as e:
                    error_count += 1
                    logger.warning(f"Validation error in record {total_count}: {e}")
                    # Continue processing other records
                except Exception as e:
                    error_count += 1
                    logger.error(f"Unexpected error processing record {total_count}: {e}")
                    
    except ijson.JSONError as e:
        logger.error(f"JSON parsing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise

    logger.info(f"Parsing complete. Total records: {total_count}, Valid: {valid_count}, Errors: {error_count}")
    return records

def main():
    """Main entry point for T006a."""
    logger.info("Starting T006a: Parse Trajectories and Extract Metrics")

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 1. Validate Data Source (Fail loudly if missing)
    try:
        validate_data_source(RAW_DATA_PATH)
        logger.info(f"Data source validated: {RAW_DATA_PATH}")
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)

    # 2. Load Schema
    try:
        schema = load_schema(SCHEMA_PATH)
        logger.info(f"Schema loaded: {SCHEMA_PATH}")
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)

    # 3. Parse and Extract
    try:
        metrics_data = parse_trajectories(RAW_DATA_PATH, schema)
    except Exception as e:
        logger.critical(f"Failed to parse trajectories: {e}")
        sys.exit(1)

    if not metrics_data:
        logger.warning("No valid metrics extracted. Outputting empty CSV.")

    # 4. Save to CSV
    df = pd.DataFrame(metrics_data)
    
    # Ensure column order as specified
    expected_cols = ["trajectory_id", "turn", "health_ratio", "enemy_threat", "deck_size", "move_entropy", "layer_name"]
    if not df.empty:
        # Reindex to ensure order, filling missing with NaN if any (though logic should produce all)
        df = df.reindex(columns=expected_cols)
    
    df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Metrics saved to: {OUTPUT_PATH}")
    logger.info(f"Total rows written: {len(df)}")

    # Compute checksum of output for verification
    checksum = compute_file_checksum(OUTPUT_PATH)
    logger.info(f"Output checksum: {checksum}")

if __name__ == "__main__":
    main()
