"""
Parser module for extracting per-turn metrics from raw AgenticSTS trajectories.

This module implements T006a:
- Reads raw JSONL/JSON files from data/raw/
- Validates against contracts/trajectory.schema.yaml
- Extracts metrics (turn, legal_moves count, win/loss flags, state hash)
- Outputs data/processed/metrics_with_moves.csv
"""
import os
import json
import logging
import hashlib
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
SCHEMA_PATH = Path("contracts/trajectory.schema.yaml")
OUTPUT_PATH = PROCESSED_DIR / "metrics_with_moves.csv"
INPUT_FILE_PATTERN = "agenticsts_trajectories.jsonl"

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and return the YAML schema."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a valid YAML dictionary")
    
    return schema

def validate_trajectory_against_schema(
    trajectory: Dict[str, Any], 
    schema: Dict[str, Any],
    trajectory_id: str
) -> bool:
    """
    Validate a single trajectory record against the schema.
    Returns True if valid, raises ValueError if invalid.
    """
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    
    for field in required_fields:
        if field not in trajectory:
            raise ValueError(
                f"Trajectory {trajectory_id} missing required field: '{field}'"
            )
    
    # Basic type validation for known fields
    if "turn" in trajectory and not isinstance(trajectory["turn"], int):
        raise ValueError(
            f"Trajectory {trajectory_id}: 'turn' must be an integer"
        )
    
    if "win" in trajectory and not isinstance(trajectory["win"], bool):
        # Handle cases where win might be string "true"/"false"
        if isinstance(trajectory["win"], str) and trajectory["win"].lower() in ["true", "false"]:
            trajectory["win"] = trajectory["win"].lower() == "true"
        else:
            raise ValueError(
                f"Trajectory {trajectory_id}: 'win' must be a boolean"
            )
    
    if "loss" in trajectory and not isinstance(trajectory["loss"], bool):
        if isinstance(trajectory["loss"], str) and trajectory["loss"].lower() in ["true", "false"]:
            trajectory["loss"] = trajectory["loss"].lower() == "true"
        else:
            raise ValueError(
                f"Trajectory {trajectory_id}: 'loss' must be a boolean"
            )
    
    if "legal_moves" in trajectory:
        if not isinstance(trajectory["legal_moves"], (list, int)):
            # If it's a string representation of a list, try to parse it
            if isinstance(trajectory["legal_moves"], str):
                try:
                    trajectory["legal_moves"] = json.loads(trajectory["legal_moves"])
                except json.JSONDecodeError:
                    raise ValueError(
                        f"Trajectory {trajectory_id}: 'legal_moves' must be a list or integer"
                    )
            else:
                raise ValueError(
                    f"Trajectory {trajectory_id}: 'legal_moves' must be a list or integer"
                )
    
    return True

def extract_metrics_from_trajectory(
    trajectory: Dict[str, Any],
    trajectory_id: str
) -> Dict[str, Any]:
    """
    Extract per-turn metrics from a single trajectory record.
    Returns a dictionary of metrics suitable for CSV output.
    """
    metrics = {
        "trajectory_id": trajectory_id,
        "turn": trajectory.get("turn", 0),
        "legal_moves_count": len(trajectory.get("legal_moves", [])) if isinstance(trajectory.get("legal_moves"), list) else trajectory.get("legal_moves", 0),
        "win": trajectory.get("win", False),
        "loss": trajectory.get("loss", False),
        "initial_state_hash": trajectory.get("initial_state_hash", ""),
        "timestamp": trajectory.get("timestamp", ""),
        "agent_id": trajectory.get("agent_id", "")
    }
    
    # Ensure win/loss are boolean
    if not isinstance(metrics["win"], bool):
        metrics["win"] = bool(metrics["win"])
    if not isinstance(metrics["loss"], bool):
        metrics["loss"] = bool(metrics["loss"])
        
    return metrics

def parse_trajectories(
    input_file: Path,
    schema: Dict[str, Any]
) -> pd.DataFrame:
    """
    Parse trajectories from a JSONL file, validate against schema,
    and extract metrics.
    
    Args:
        input_file: Path to the JSONL file
        schema: The schema dictionary for validation
        
    Returns:
        DataFrame with extracted metrics
    """
    records = []
    line_number = 0
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    logger.info(f"Parsing trajectories from: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line_number += 1
            line = line.strip()
            if not line:
                continue
            
            try:
                trajectory = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON at line {line_number}: {e}")
                continue
            
            # Extract trajectory_id for error reporting
            trajectory_id = trajectory.get("trajectory_id", f"line_{line_number}")
            
            try:
                # Validate against schema
                validate_trajectory_against_schema(trajectory, schema, trajectory_id)
                
                # Extract metrics
                metrics = extract_metrics_from_trajectory(trajectory, trajectory_id)
                records.append(metrics)
                
            except ValueError as e:
                logger.warning(f"Validation failed for {trajectory_id}: {e}")
                continue
    
    if not records:
        logger.warning("No valid records extracted from the input file.")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=[
            "trajectory_id", "turn", "legal_moves_count", 
            "win", "loss", "initial_state_hash", "timestamp", "agent_id"
        ])
    
    df = pd.DataFrame(records)
    logger.info(f"Successfully extracted {len(df)} records.")
    return df

def validate_data_source() -> Path:
    """
    Validate that the raw data source exists and is accessible.
    Raises FileNotFoundError if data is missing.
    """
    input_file = RAW_DATA_DIR / INPUT_FILE_PATTERN
    
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(
            "Real data missing; pipeline cannot proceed. "
            f"Directory {RAW_DATA_DIR} does not exist."
        )
    
    if not input_file.exists():
        raise FileNotFoundError(
            "Real data missing; pipeline cannot proceed. "
            f"File {input_file} not found. "
            "Please ensure T005b (Ingest Real AgenticSTS Trajectories) has run successfully."
        )
    
    logger.info(f"Data source validated: {input_file}")
    return input_file

def main():
    """Main entry point for the parser task (T006a)."""
    logger.info("Starting T006a: Parser for per-turn metrics extraction")
    
    # Ensure output directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Validate data source (fail loudly if missing)
        input_file = validate_data_source()
        
        # Step 2: Load schema
        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(
                f"Schema file missing: {SCHEMA_PATH}. "
                "Please ensure T003a (Generate Trajectory Schema) has run."
            )
        
        schema = load_schema(SCHEMA_PATH)
        logger.info(f"Schema loaded from: {SCHEMA_PATH}")
        
        # Step 3: Parse trajectories
        df = parse_trajectories(input_file, schema)
        
        # Step 4: Write output
        df.to_csv(OUTPUT_PATH, index=False)
        logger.info(f"Metrics written to: {OUTPUT_PATH}")
        logger.info(f"Output shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Verify output
        if df.empty:
            logger.warning("Output DataFrame is empty. Check input data quality.")
        else:
            logger.info("T006a completed successfully.")
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during parsing: {e}")
        raise

if __name__ == "__main__":
    main()