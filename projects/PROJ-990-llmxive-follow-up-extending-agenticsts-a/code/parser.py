import os
import json
import logging
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
CHECKSUM_FILE = Path("data/.checksums.json")
METRICS_OUTPUT = PROCESSED_DATA_DIR / "metrics_with_moves.csv"

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_checksums() -> Dict[str, str]:
    """Load previously saved checksums."""
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
    Validate that data/raw/ contains non-empty, checksum-verified trajectory files.
    Raises ValueError if missing or corrupted.
    """
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Data directory {RAW_DATA_DIR} does not exist.")
    
    json_files = list(RAW_DATA_DIR.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {RAW_DATA_DIR}.")
    
    saved_checksums = load_existing_checksums()
    current_checksums = {}
    missing_files = []
    corrupted_files = []

    for file_path in json_files:
        current_checksum = compute_file_checksum(file_path)
        current_checksums[str(file_path)] = current_checksum
        
        if str(file_path) in saved_checksums:
            if saved_checksums[str(file_path)] != current_checksum:
                corrupted_files.append(str(file_path))
        else:
            # New file, check if empty
            if file_path.stat().st_size == 0:
                missing_files.append(str(file_path))
    
    if corrupted_files:
        raise ValueError(f"Corrupted files detected (checksum mismatch): {corrupted_files}")
    if missing_files:
        raise ValueError(f"Empty files detected: {missing_files}")
    
    save_checksums(current_checksums)
    logger.info(f"Data source validation passed. Found {len(json_files)} files.")

def extract_metrics_from_trajectory(trajectory_data: Dict) -> List[Dict]:
    """
    Extract per-turn metrics from a single trajectory record.
    
    Input schema:
    {
        "trajectory_id": str,
        "turn": int,
        "health_ratio": float,  # Optional, if present in raw data
        "threat_level": float,  # Optional
        "deck_size": int,       # Optional
        "legal_moves": List[str]
    }
    
    If optional metrics are missing, they will be set to None or derived if possible.
    """
    trajectory_id = trajectory_data.get("trajectory_id")
    turn = trajectory_data.get("turn")
    legal_moves = trajectory_data.get("legal_moves", [])
    
    # Handle optional fields - if missing, we might need to infer or leave as None
    # For this implementation, we assume the raw data might have these or we set defaults
    health_ratio = trajectory_data.get("health_ratio")
    threat_level = trajectory_data.get("threat_level")
    deck_size = trajectory_data.get("deck_size")
    
    # Calculate move entropy
    # H = - sum(p_i * log(p_i)) where p_i = 1/|legal_moves| for uniform distribution
    move_entropy = float('nan')
    if legal_moves and len(legal_moves) > 0:
        n_moves = len(legal_moves)
        if n_moves == 1:
            move_entropy = 0.0
        else:
            # Uniform probability distribution
            p = 1.0 / n_moves
            move_entropy = -n_moves * (p * math.log2(p))
    
    # Handle edge cases for entropy (NaN/Inf)
    if math.isnan(move_entropy) or math.isinf(move_entropy):
        # Log warning if this is an edge case
        logger.warning(f"NaN/Inf entropy detected for trajectory {trajectory_id}, turn {turn}")
    
    return {
        "trajectory_id": trajectory_id,
        "turn": turn,
        "health_ratio": health_ratio,
        "threat_level": threat_level,
        "deck_size": deck_size,
        "move_entropy": move_entropy,
        "legal_moves_count": len(legal_moves),
        "legal_moves_json": json.dumps(legal_moves) # Store for reference
    }

def parse_trajectories(input_dir: Path = RAW_DATA_DIR) -> List[Dict]:
    """
    Parse all JSON trajectory logs in the input directory.
    
    Returns a list of dictionaries containing per-turn metrics.
    """
    all_metrics = []
    json_files = list(input_dir.glob("*.json"))
    
    for file_path in json_files:
        logger.info(f"Processing file: {file_path}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Handle both single record and list of records
            records = data if isinstance(data, list) else [data]
            
            for record in records:
                metrics = extract_metrics_from_trajectory(record)
                all_metrics.append(metrics)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            raise
    
    return all_metrics

def extract_static_log_proxy(metrics_data: List[Dict]) -> Dict[str, Dict]:
    """
    Extract static log proxy (frequency of layer retrieval) from parsed metrics.
    
    Note: This is a simplified version. In a real scenario, we would need
    more detailed log data about layer retrieval frequencies.
    
    Returns a dictionary mapping trajectory_id to proxy data.
    """
    proxy_data = {}
    
    for record in metrics_data:
        tid = record["trajectory_id"]
        if tid not in proxy_data:
            proxy_data[tid] = {
                "trajectory_id": tid,
                "layer_id": "default_layer", # Placeholder
                "utility_score": 0.0,
                "turn_count": 0
            }
        proxy_data[tid]["turn_count"] += 1
    
    # Normalize utility_score based on turn count (simplified proxy)
    max_turns = max([v["turn_count"] for v in proxy_data.values()]) if proxy_data else 1
    for tid, data in proxy_data.items():
        data["utility_score"] = data["turn_count"] / max_turns
    
    return proxy_data

def main():
    """
    Main entry point for the parser.
    
    1. Validates data source
    2. Parses all trajectory logs
    3. Extracts metrics and move distributions
    4. Writes output to data/processed/metrics_with_moves.csv
    5. Optionally extracts static log proxy
    """
    # Ensure output directory exists
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Validate data source
        logger.info("Validating data source...")
        validate_data_source()
        
        # Step 2: Parse trajectories
        logger.info("Parsing trajectories...")
        metrics_data = parse_trajectories()
        
        if not metrics_data:
            raise ValueError("No valid trajectory data found to process.")
        
        # Step 3: Write metrics to CSV
        logger.info(f"Writing {len(metrics_data)} records to {METRICS_OUTPUT}")
        df = pd.DataFrame(metrics_data)
        
        # Select only the required columns for output
        output_columns = [
            "trajectory_id", "turn", "health_ratio", 
            "threat_level", "deck_size", "move_entropy"
        ]
        
        # Ensure all required columns exist (fill missing with NaN)
        for col in output_columns:
            if col not in df.columns:
                df[col] = float('nan')
        
        df = df[output_columns]
        df.to_csv(METRICS_OUTPUT, index=False)
        
        logger.info(f"Successfully wrote metrics to {METRICS_OUTPUT}")
        
        # Step 4: Extract and save static log proxy (optional, but good for pipeline)
        # Note: T007c will handle the formal extraction, but we can prepare data here
        # proxy_data = extract_static_log_proxy(metrics_data)
        # with open(PROCESSED_DATA_DIR / "static_log_proxy_pre.json", "w") as f:
        #     json.dump(proxy_data, f, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"Parser execution failed: {e}")
        raise

if __name__ == "__main__":
    main()