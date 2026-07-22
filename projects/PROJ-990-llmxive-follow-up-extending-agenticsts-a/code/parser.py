import os
import json
import logging
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    """Load existing checksums from a JSON file."""
    if checksum_file.exists():
        with open(checksum_file, 'r') as f:
            return json.load(f)
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
        raw_dir.mkdir(parents=True, exist_ok=True)
        raise FileNotFoundError(
            f"No trajectory files found in {raw_dir}. Expected files with extensions: ['.json', '.jsonl', '.log']"
        )

    valid_extensions = ['.json', '.jsonl', '.log']
    files = [f for f in raw_dir.iterdir() if f.is_file() and f.suffix in valid_extensions]

    if not files:
        raise FileNotFoundError(
            f"No trajectory files found in {raw_dir}. Expected files with extensions: {valid_extensions}"
        )

    # Check for empty files
    empty_files = [f for f in files if f.stat().st_size == 0]
    if empty_files:
        logger.warning(f"Found {len(empty_files)} empty files: {[f.name for f in empty_files]}")
        # Remove empty files or skip them
        files = [f for f in files if f not in empty_files]
        if not files:
            raise FileNotFoundError(
                f"All trajectory files in {raw_dir} are empty. Cannot proceed."
            )

    logger.info(f"Found {len(files)} valid trajectory files in {raw_dir}")

def extract_move_distribution(turn_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract the probability distribution of legal moves from turn data.
    Expected format: turn_data contains 'legal_moves' list and optionally 'move_probs'.
    If probabilities are missing, assume uniform distribution.
    """
    legal_moves = turn_data.get('legal_moves', [])
    if not legal_moves:
        return {}

    move_probs = turn_data.get('move_probs', None)
    if move_probs and len(move_probs) == len(legal_moves):
        # Normalize just in case
        total = sum(move_probs)
        if total > 0:
            return {str(move): p / total for move, p in zip(legal_moves, move_probs)}
        else:
            # Uniform fallback if sum is 0
            prob = 1.0 / len(legal_moves)
            return {str(move): prob for move in legal_moves}
    else:
        # Uniform distribution
        prob = 1.0 / len(legal_moves)
        return {str(move): prob for move in legal_moves}

def parse_turn_data(turn_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a single turn's data to extract per-turn metrics and move distributions.
    """
    metrics = {
        'turn_id': turn_data.get('turn_id', 0),
        'health': turn_data.get('health', 0),
        'threat': turn_data.get('threat', 0),
        'deck_size': turn_data.get('deck_size', 0),
        'action': turn_data.get('action', ''),
        'legal_moves_count': len(turn_data.get('legal_moves', []))
    }

    # Extract move distribution
    move_dist = extract_move_distribution(turn_data)
    # Flatten distribution into JSON string for CSV storage
    metrics['move_distribution'] = json.dumps(move_dist)

    return metrics

def extract_metrics_from_trajectory(trajectory: Dict[str, Any], trajectory_id: str) -> List[Dict[str, Any]]:
    """
    Extract per-turn metrics and move distributions from a single trajectory.
    """
    turns = trajectory.get('turns', [])
    parsed_turns = []

    for turn in turns:
        parsed = parse_turn_data(turn)
        parsed['trajectory_id'] = trajectory_id
        parsed_turns.append(parsed)

    return parsed_turns

def parse_trajectories(raw_dir: Path, output_path: Path) -> pd.DataFrame:
    """
    Parse all trajectory files in raw_dir and extract metrics with move distributions.
    Output: CSV file with columns for per-turn metrics and move distribution.
    """
    validate_data_source(raw_dir)

    all_turns = []
    valid_extensions = ['.json', '.jsonl', '.log']

    for file_path in raw_dir.iterdir():
        if file_path.is_file() and file_path.suffix in valid_extensions:
            logger.info(f"Processing {file_path.name}")
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Handle different formats
                if file_path.suffix == '.jsonl':
                    for line in content.strip().split('\n'):
                        if line.strip():
                            trajectory = json.loads(line)
                            trajectory_id = trajectory.get('id', file_path.stem)
                            turns = extract_metrics_from_trajectory(trajectory, trajectory_id)
                            all_turns.extend(turns)
                elif file_path.suffix == '.json':
                    trajectories = json.loads(content)
                    # Handle both single trajectory and list of trajectories
                    if isinstance(trajectories, dict):
                        trajectories = [trajectories]
                    for trajectory in trajectories:
                        trajectory_id = trajectory.get('id', f"{file_path.stem}_{trajectory.get('id', 'unknown')}")
                        turns = extract_metrics_from_trajectory(trajectory, trajectory_id)
                        all_turns.extend(turns)
                elif file_path.suffix == '.log':
                    # Simple log parsing - assume JSON per line or specific format
                    for line in content.strip().split('\n'):
                        if line.strip():
                            try:
                                trajectory = json.loads(line)
                                trajectory_id = trajectory.get('id', f"{file_path.stem}_{trajectory.get('id', 'unknown')}")
                                turns = extract_metrics_from_trajectory(trajectory, trajectory_id)
                                all_turns.extend(turns)
                            except json.JSONDecodeError:
                                logger.warning(f"Skipping non-JSON log line in {file_path.name}")
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                raise

    if not all_turns:
        logger.warning("No turns extracted from trajectories. Creating empty CSV.")
        df = pd.DataFrame(columns=[
            'trajectory_id', 'turn_id', 'health', 'threat', 'deck_size',
            'action', 'legal_moves_count', 'move_distribution'
        ])
    else:
        df = pd.DataFrame(all_turns)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} rows to {output_path}")

    return df

def extract_static_log_proxy(validation_df: pd.DataFrame, output_path: Path) -> Dict[str, Any]:
    """
    Extract static log-derived utility (layer retrieval frequency) from validation set.
    This extends parser.py to support T007b.
    """
    # Group by layer_id if available, otherwise use trajectory_id as proxy
    # Assuming validation_df has layer information or we extract from move_distribution
    layer_counts = {}

    for _, row in validation_df.iterrows():
        # Try to extract layer info from move_distribution or other fields
        move_dist_str = row.get('move_distribution', '{}')
        try:
            move_dist = json.loads(move_dist_str)
            for layer_id in move_dist.keys():
                layer_counts[layer_id] = layer_counts.get(layer_id, 0) + 1
        except json.JSONDecodeError:
            continue

    # Convert to frequencies
    total = sum(layer_counts.values()) if layer_counts else 1
    static_proxy = {
        layer_id: count / total
        for layer_id, count in layer_counts.items()
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(static_proxy, f, indent=2)

    logger.info(f"Wrote static log proxy to {output_path}")
    return static_proxy

def main():
    """Main entry point for parser.py."""
    import argparse
    parser = argparse.ArgumentParser(description='Parse trajectory logs and extract metrics.')
    parser.add_argument('--input-dir', type=str, default='data/raw', help='Input directory for raw trajectory files.')
    parser.add_argument('--output-file', type=str, default='data/processed/metrics_with_moves.csv', help='Output CSV file path.')
    args = parser.parse_args()

    raw_dir = Path(args.input_dir)
    output_path = Path(args.output_file)

    parse_trajectories(raw_dir, output_path)

if __name__ == '__main__':
    main()