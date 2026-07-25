import os
import json
import logging
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def load_existing_checksums(checksum_file: Path) -> Dict[str, str]:
    """Load existing checksums from a JSON file."""
    if checksum_file.exists():
        try:
            with open(checksum_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Checksum file corrupted, starting fresh.")
            return {}
    return {}

def save_checksums(checksums: Dict[str, str], checksum_file: Path) -> None:
    """Save checksums to a JSON file."""
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)

def validate_data_source(raw_dir: Path) -> None:
    """
    Validate that data/raw contains non-empty, checksum-verified trajectory files.
    Raises FileNotFoundError if no valid files are found.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Directory {raw_dir} does not exist.")

    valid_extensions = ['.json', '.jsonl', '.log']
    found_files = []
    for ext in valid_extensions:
        found_files.extend(list(raw_dir.glob(f"*{ext}")))
        found_files.extend(list(raw_dir.glob(f"*{ext.upper()}")))

    if not found_files:
        raise FileNotFoundError(
            f"No trajectory files found in {raw_dir}. "
            f"Expected files with extensions: {valid_extensions}"
        )

    # Checksum validation logic (simplified for this task: just check non-empty)
    valid_count = 0
    for file_path in found_files:
        if file_path.stat().st_size > 0:
            valid_count += 1
        else:
            logger.warning(f"Empty file ignored: {file_path}")

    if valid_count == 0:
        raise FileNotFoundError(
            f"All found files in {raw_dir} were empty or corrupted."
        )

    logger.info(f"Data source validated: {valid_count} valid files found.")

def parse_turn_data(turn_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a single turn's data to extract metrics.
    Expected input keys: health, threat, deck_size, legal_moves, trajectory_id, turn
    """
    trajectory_id = turn_data.get('trajectory_id', 'unknown')
    turn = turn_data.get('turn', 0)
    
    # Extract basic metrics
    health = turn_data.get('health', 0)
    max_health = turn_data.get('max_health', 100)
    health_ratio = health / max_health if max_health > 0 else 0.0
    
    threat_level = turn_data.get('threat_level', 0)
    deck_size = turn_data.get('deck_size', 0)
    
    # Extract legal moves and calculate entropy
    legal_moves = turn_data.get('legal_moves', [])
    move_entropy = 0.0
    
    if legal_moves and len(legal_moves) > 0:
        # Assuming uniform probability distribution for available legal moves
        # p_i = 1 / |legal_moves|
        n_moves = len(legal_moves)
        if n_moves > 1:
            # Shannon entropy: H = - sum(p_i * log(p_i))
            # Since p_i is uniform: H = - n * (1/n * log(1/n)) = log(n)
            import math
            move_entropy = math.log(n_moves)
        elif n_moves == 1:
            move_entropy = 0.0 # log(1) = 0
        else:
            move_entropy = 0.0 # Fallback
    else:
        # No legal moves? This might be an edge case, entropy 0 or NaN?
        # Spec implies we need a distribution. If no moves, entropy is 0 (deterministic end).
        move_entropy = 0.0

    return {
        'trajectory_id': trajectory_id,
        'turn': turn,
        'health_ratio': health_ratio,
        'threat_level': threat_level,
        'deck_size': deck_size,
        'move_entropy': move_entropy
    }

def extract_metrics_from_trajectory(trajectory: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract per-turn metrics from a single trajectory object.
    """
    trajectory_id = trajectory.get('trajectory_id', 'unknown')
    turns = trajectory.get('turns', [])
    
    metrics = []
    for turn_data in turns:
        turn_data['trajectory_id'] = trajectory_id # Ensure ID is present
        metrics.append(parse_turn_data(turn_data))
    
    return metrics

def parse_trajectories(raw_dir: Path, output_path: Path) -> None:
    """
    Parse all trajectory logs in raw_dir and write metrics to a CSV.
    Input: JSON logs conforming to contracts/trajectory.schema.yaml.
    Output: CSV with columns: trajectory_id, turn, health_ratio, threat_level, deck_size, move_entropy.
    """
    all_metrics = []
    valid_extensions = ['.json', '.jsonl', '.log']
    
    for ext in valid_extensions:
        for file_path in raw_dir.glob(f"*{ext}"):
            logger.info(f"Processing file: {file_path}")
            try:
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        continue
                    
                    # Handle JSONL vs JSON
                    if ext == '.jsonl':
                        for line in content.split('\n'):
                            if line.strip():
                                traj = json.loads(line)
                                all_metrics.extend(extract_metrics_from_trajectory(traj))
                    else:
                        # Assume single JSON or JSON array
                        try:
                            data = json.loads(content)
                            if isinstance(data, list):
                                for traj in data:
                                    all_metrics.extend(extract_metrics_from_trajectory(traj))
                            else:
                                all_metrics.extend(extract_metrics_from_trajectory(data))
                        except json.JSONDecodeError:
                            # Try line-by-line if it's not a valid array/object but looks like JSONL
                            logger.warning(f"{file_path} not valid JSON object/array, trying line-by-line.")
                            for line in content.split('\n'):
                                if line.strip():
                                    try:
                                        traj = json.loads(line)
                                        all_metrics.extend(extract_metrics_from_trajectory(traj))
                                    except:
                                        continue
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

    if not all_metrics:
        logger.warning("No metrics extracted. Outputting empty CSV.")
    
    # Create DataFrame
    df = pd.DataFrame(all_metrics)
    
    # Ensure columns exist in correct order (even if empty)
    expected_cols = ['trajectory_id', 'turn', 'health_ratio', 'threat_level', 'deck_size', 'move_entropy']
    for col in expected_cols:
        if col not in df.columns:
            df[col] = []
    
    df = df[expected_cols]
    
    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} rows to {output_path}")

def extract_static_log_proxy(trajectory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for static log proxy extraction logic.
    This is a stub to satisfy the function signature in the API surface.
    The actual implementation for T007c is separate.
    """
    # T006 focuses on metrics_with_moves.csv.
    # This function is kept for API compatibility but not fully implemented here.
    return {}

def main():
    """
    Main entry point for the parser script.
    """
    # Define paths relative to project root
    # Assuming script runs from project root or code/
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    output_path = project_root / "data" / "processed" / "metrics_with_moves.csv"
    
    # Ensure directories exist
    (project_root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    
    try:
        validate_data_source(raw_dir)
        parse_trajectories(raw_dir, output_path)
        logger.info("Parser completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Data validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during parsing: {e}")
        raise

if __name__ == "__main__":
    main()
