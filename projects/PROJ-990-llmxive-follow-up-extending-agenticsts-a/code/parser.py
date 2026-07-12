"""
Parser module for extracting per-turn metrics from raw trajectory logs.

This module processes raw trajectory data to extract key metrics such as
health, threat level, and deck size for each turn in an agent's trajectory.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_turn_data(turn_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metrics from a single turn record.

    Args:
        turn_record: A dictionary representing a single turn's data.

    Returns:
        A dictionary containing extracted metrics: health, threat, deck_size,
        turn_id, and trajectory_id.
    """
    metrics = {
        'trajectory_id': turn_record.get('trajectory_id', 'unknown'),
        'turn_id': turn_record.get('turn_id', 0),
        'health': None,
        'threat': None,
        'deck_size': None,
        'action': turn_record.get('action', None),
        'context_tokens': turn_record.get('context_tokens', 0),
    }

    # Extract health - try multiple possible keys
    health_keys = ['health', 'hp', 'current_health', 'player_health']
    for key in health_keys:
        if key in turn_record:
            val = turn_record[key]
            if isinstance(val, (int, float)) and not (val != val or val == float('inf')):
                metrics['health'] = float(val)
                break

    # Extract threat level - try multiple possible keys
    threat_keys = ['threat', 'threat_level', 'enemy_threat', 'threat_score']
    for key in threat_keys:
        if key in turn_record:
            val = turn_record[key]
            if isinstance(val, (int, float)) and not (val != val or val == float('inf')):
                metrics['threat'] = float(val)
                break

    # Extract deck size - try multiple possible keys
    deck_keys = ['deck_size', 'remaining_deck', 'cards_in_deck', 'deck_remaining']
    for key in deck_keys:
        if key in turn_record:
            val = turn_record[key]
            if isinstance(val, (int, float)) and not (val != val or val == float('inf')):
                metrics['deck_size'] = int(val)
                break

    # Log if any critical metrics are missing
    missing = []
    if metrics['health'] is None:
        missing.append('health')
    if metrics['threat'] is None:
        missing.append('threat')
    if metrics['deck_size'] is None:
        missing.append('deck_size')

    if missing:
        logger.warning(f"Missing metrics {missing} for turn {turn_record.get('turn_id')} "
                     f"in trajectory {turn_record.get('trajectory_id')}")

    return metrics

def extract_metrics_from_trajectory(trajectory: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract per-turn metrics from a complete trajectory.

    Args:
        trajectory: A dictionary representing a complete trajectory with turns.

    Returns:
        A list of dictionaries, each containing metrics for a single turn.
    """
    trajectory_id = trajectory.get('trajectory_id', 'unknown')
    turns = trajectory.get('turns', [])

    if not turns:
        logger.warning(f"No turns found in trajectory {trajectory_id}")
        return []

    logger.info(f"Processing trajectory {trajectory_id} with {len(turns)} turns")

    metrics_list = []
    for turn in turns:
        # Ensure turn has trajectory_id
        if 'trajectory_id' not in turn:
            turn['trajectory_id'] = trajectory_id

        turn_metrics = parse_turn_data(turn)
        metrics_list.append(turn_metrics)

    return metrics_list

def parse_trajectories(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Parse all trajectory logs from input directory and write metrics to output CSV.

    Args:
        input_path: Path to the directory containing raw trajectory JSON files.
        output_path: Path where the output CSV will be written.

    Returns:
        A pandas DataFrame containing all extracted metrics.
    """
    input_dir = Path(input_path)
    output_file = Path(output_path)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    all_metrics = []
    trajectory_files = list(input_dir.glob("*.json")) + list(input_dir.glob("*.jsonl"))

    if not trajectory_files:
        logger.warning(f"No JSON or JSONL files found in {input_dir}")
        # Create empty output file with schema
        empty_df = pd.DataFrame(columns=[
            'trajectory_id', 'turn_id', 'health', 'threat', 'deck_size',
            'action', 'context_tokens'
        ])
        empty_df.to_csv(output_file, index=False)
        return empty_df

    logger.info(f"Found {len(trajectory_files)} trajectory files")

    for file_path in trajectory_files:
        logger.info(f"Processing file: {file_path}")
        try:
            if file_path.suffix == '.jsonl':
                # JSONL format: one JSON object per line
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            trajectory = json.loads(line)
                            metrics = extract_metrics_from_trajectory(trajectory)
                            all_metrics.extend(metrics)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error in {file_path} at line {line_num}: {e}")
                            continue
            else:
                # Standard JSON format
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle both single trajectory and list of trajectories
                if isinstance(data, list):
                    for trajectory in data:
                        metrics = extract_metrics_from_trajectory(trajectory)
                        all_metrics.extend(metrics)
                elif isinstance(data, dict):
                    # Check if it's a single trajectory or a container
                    if 'turns' in data:
                        metrics = extract_metrics_from_trajectory(data)
                        all_metrics.extend(metrics)
                    elif 'trajectories' in data:
                        for trajectory in data['trajectories']:
                            metrics = extract_metrics_from_trajectory(trajectory)
                            all_metrics.extend(metrics)
                    else:
                        logger.warning(f"Unexpected JSON structure in {file_path}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            continue

    # Create DataFrame
    if all_metrics:
        df = pd.DataFrame(all_metrics)
        
        # Ensure correct column order
        columns = ['trajectory_id', 'turn_id', 'health', 'threat', 'deck_size', 'action', 'context_tokens']
        df = df[[col for col in columns if col in df.columns]]
        
        # Fill NaN with default values for numeric columns
        for col in ['health', 'threat', 'deck_size']:
            if col in df.columns:
                df[col] = df[col].fillna(0)
                df[col] = df[col].astype(float if col != 'deck_size' else int)

        # Sort by trajectory_id and turn_id
        df = df.sort_values(by=['trajectory_id', 'turn_id']).reset_index(drop=True)
    else:
        logger.warning("No metrics extracted from any files")
        df = pd.DataFrame(columns=['trajectory_id', 'turn_id', 'health', 'threat', 'deck_size', 'action', 'context_tokens'])

    # Write to CSV
    df.to_csv(output_file, index=False)
    logger.info(f"Wrote {len(df)} records to {output_file}")

    return df

def main():
    """
    Main entry point for the parser script.
    Reads from data/raw/trajectories.csv (or JSON files) and outputs to data/processed/trajectory_metrics.csv
    """
    # Default paths
    input_path = "data/raw/trajectories.csv"
    output_path = "data/processed/trajectory_metrics.csv"

    # Check if CSV input exists, otherwise look for JSON files
    if not os.path.exists(input_path):
        # Look for JSON files in data/raw/
        raw_dir = Path("data/raw")
        json_files = list(raw_dir.glob("*.json")) + list(raw_dir.glob("*.jsonl"))
        if json_files:
            # If multiple JSON files, we'll process the directory
            input_path = "data/raw"
            output_path = "data/processed/trajectory_metrics.csv"
            logger.info(f"Using JSON files from {input_path}")
        else:
            logger.error(f"No input data found at {input_path} or in data/raw/ as JSON files")
            return

    # Parse trajectories
    try:
        df = parse_trajectories(input_path, output_path)
        logger.info("Parsing completed successfully")
        print(f"Successfully extracted {len(df)} turn metrics to {output_path}")
    except Exception as e:
        logger.error(f"Failed to parse trajectories: {e}")
        raise

if __name__ == "__main__":
    main()
