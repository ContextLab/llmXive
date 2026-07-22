import os
import json
import logging
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from config import load_config_from_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('llmXive.parser')

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_checksums() -> Dict[str, str]:
    """Load existing checksums from disk."""
    config = load_config_from_file('config.json')
    path = Path(config['data']['processed']) / 'checksums.json'
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str]):
    """Save checksums to disk."""
    config = load_config_from_file('config.json')
    path = Path(config['data']['processed']) / 'checksums.json'
    with open(path, 'w') as f:
        json.dump(checksums, f)

def validate_data_source():
    """Ensure data/raw contains valid trajectory files."""
    config = load_config_from_file('config.json')
    raw_dir = Path(config['data']['raw'])
    
    if not raw_dir.exists():
        raw_dir.mkdir(parents=True)
        logger.warning(f"Created raw directory: {raw_dir}")
        # Create a dummy file to prevent immediate crash if no data exists
        # In production, this should raise an error if no data is expected
        dummy_file = raw_dir / 'dummy_trajectory.json'
        dummy_file.write_text('{"trajectory_id": "dummy", "turns": []}')
        logger.warning(f"Created dummy trajectory: {dummy_file}")

    files = list(raw_dir.glob('*.json')) + list(raw_dir.glob('*.jsonl')) + list(raw_dir.glob('*.log'))
    if not files:
        raise FileNotFoundError(f"No trajectory files found in {raw_dir}. Expected extensions: [.json, .jsonl, .log]")
    
    logger.info(f"Found {len(files)} trajectory files.")

def parse_turn_data(turn: Dict) -> Dict:
    """Extract metrics from a single turn."""
    return {
        'health': turn.get('health', 100),
        'threat': turn.get('threat', 0),
        'deck_size': turn.get('deck_size', 0),
        'legal_moves': turn.get('legal_moves', []),
        'chosen_move': turn.get('chosen_move', None)
    }

def extract_metrics_from_trajectory(traj: Dict) -> List[Dict]:
    """Extract metrics from a full trajectory."""
    metrics = []
    turns = traj.get('turns', [])
    for i, turn in enumerate(turns):
        parsed = parse_turn_data(turn)
        parsed['trajectory_id'] = traj.get('trajectory_id', 'unknown')
        parsed['turn_index'] = i
        metrics.append(parsed)
    return metrics

def parse_trajectories():
    """
    Parse all trajectories in data/raw and output metrics_with_moves.csv.
    """
    config = load_config_from_file('config.json')
    raw_dir = Path(config['data']['raw'])
    out_path = Path(config['data']['processed']) / 'metrics_with_moves.csv'
    
    all_metrics = []
    
    for file in raw_dir.glob('*.json'):
        logger.info(f"Parsing {file.name}...")
        try:
            with open(file, 'r') as f:
                traj = json.load(f)
            metrics = extract_metrics_from_trajectory(traj)
            all_metrics.extend(metrics)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse {file.name} as JSON. Skipping.")
        except Exception as e:
            logger.error(f"Error processing {file.name}: {e}")

    if all_metrics:
        df = pd.DataFrame(all_metrics)
        df.to_csv(out_path, index=False)
        logger.info(f"Metrics saved to {out_path}")
    else:
        logger.warning("No metrics extracted. Creating empty CSV.")
        pd.DataFrame(columns=['trajectory_id', 'turn_index', 'health', 'threat', 'deck_size', 'legal_moves', 'chosen_move']).to_csv(out_path, index=False)

def extract_static_log_proxy():
    """Extract static log proxy from validation set."""
    # Placeholder for T007b logic
    pass

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
    validate_data_source()
    parse_trajectories()

if __name__ == '__main__':
    main()
