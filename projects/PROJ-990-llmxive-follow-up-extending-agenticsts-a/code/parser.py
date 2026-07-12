"""
Parser module for extracting per-turn metrics from raw trajectory logs.

This module implements the core parsing logic to extract health, threat,
and deck size metrics from raw trajectory logs located in data/raw/.
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

# Constants
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
TRAJECTORIES_FILE = "trajectories.csv"
OUTPUT_FILE = "per_turn_metrics.csv"

def parse_turn_data(turn_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a single turn record to extract metrics.

    Args:
        turn_record: Dictionary containing turn data with keys like
                    'turn_id', 'health', 'threat_level', 'deck_size', etc.

    Returns:
        Dictionary with extracted metrics or None if record is invalid.
    """
    if not isinstance(turn_record, dict):
        logger.warning(f"Invalid turn record type: {type(turn_record)}")
        return None

    # Extract required fields with defaults
    try:
        metrics = {
            'turn_id': turn_record.get('turn_id', turn_record.get('turn', -1)),
            'health': float(turn_record.get('health', 0)),
            'threat_level': float(turn_record.get('threat_level', turn_record.get('threat', 0))),
            'deck_size': int(turn_record.get('deck_size', turn_record.get('deck', 0))),
            'agent_id': turn_record.get('agent_id', 'unknown'),
            'trajectory_id': turn_record.get('trajectory_id', turn_record.get('trajectory', 'unknown')),
            'timestamp': turn_record.get('timestamp', None)
        }

        # Validate extracted values
        if metrics['turn_id'] == -1:
            logger.warning(f"Invalid turn_id in record: {turn_record}")
            return None

        return metrics

    except (ValueError, TypeError) as e:
        logger.error(f"Failed to parse turn record: {turn_record}, error: {e}")
        return None

def extract_metrics_from_trajectory(trajectory_data: List[Dict[str, Any]], trajectory_id: str) -> List[Dict[str, Any]]:
    """
    Extract per-turn metrics from a complete trajectory.

    Args:
        trajectory_data: List of turn records for a single trajectory.
        trajectory_id: Unique identifier for the trajectory.

    Returns:
        List of parsed turn metric dictionaries.
    """
    if not isinstance(trajectory_data, list):
        logger.error(f"Expected list of turns, got {type(trajectory_data)}")
        return []

    parsed_turns = []
    for idx, turn_record in enumerate(trajectory_data):
        # Ensure trajectory_id is set in each record
        if isinstance(turn_record, dict):
            turn_record['trajectory_id'] = trajectory_id

        parsed = parse_turn_data(turn_record)
        if parsed is not None:
            parsed_turns.append(parsed)
        else:
            logger.debug(f"Skipped invalid turn {idx} in trajectory {trajectory_id}")

    logger.info(f"Extracted {len(parsed_turns)} valid turns from trajectory {trajectory_id}")
    return parsed_turns

def parse_trajectories(raw_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Parse all trajectory files from the raw data directory.

    This function:
    1. Reads trajectory files from data/raw/
    2. Extracts per-turn metrics (health, threat, deck size)
    3. Returns a consolidated DataFrame

    Args:
        raw_dir: Optional path to raw data directory. Defaults to data/raw/.

    Returns:
        pandas DataFrame with columns: turn_id, health, threat_level,
        deck_size, agent_id, trajectory_id, timestamp
    """
    if raw_dir is None:
        raw_dir = RAW_DATA_DIR

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    all_metrics = []

    # Handle both CSV and JSONL/JSON formats
    csv_file = raw_dir / TRAJECTORIES_FILE
    if csv_file.exists():
        logger.info(f"Reading trajectories from CSV: {csv_file}")
        try:
            df = pd.read_csv(csv_file)

            # Handle different data structures
            # Case 1: Each row is a turn (already flat)
            if 'turn_id' in df.columns or 'turn' in df.columns:
                logger.info("Detected flat trajectory format (one row per turn)")
                # Convert to list of dicts for consistent processing
                records = df.to_dict('records')
                for record in records:
                    parsed = parse_turn_data(record)
                    if parsed:
                        all_metrics.append(parsed)

            # Case 2: Nested structure (trajectory_id with nested turns)
            elif 'trajectory_id' in df.columns and 'turns' in df.columns:
                logger.info("Detected nested trajectory format")
                for _, row in df.iterrows():
                    traj_id = str(row['trajectory_id'])
                    turns_data = row['turns']

                    # Parse turns from string or list
                    if isinstance(turns_data, str):
                        try:
                            turns_list = json.loads(turns_data)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON in turns column for trajectory {traj_id}")
                            continue
                    elif isinstance(turns_data, list):
                        turns_list = turns_data
                    else:
                        logger.error(f"Unexpected turns data type: {type(turns_data)}")
                        continue

                    parsed_turns = extract_metrics_from_trajectory(turns_list, traj_id)
                    all_metrics.extend(parsed_turns)

            # Case 3: Single column with JSON strings
            elif 'data' in df.columns or 'json' in df.columns:
                json_col = 'data' if 'data' in df.columns else 'json'
                logger.info(f"Detected JSON string format in column: {json_col}")
                for _, row in df.iterrows():
                    traj_id = str(row.get('trajectory_id', f"unknown_{_}"))
                    try:
                        turns_data = json.loads(row[json_col])
                        if isinstance(turns_data, list):
                            parsed_turns = extract_metrics_from_trajectory(turns_data, traj_id)
                            all_metrics.extend(parsed_turns)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.error(f"Failed to parse JSON for trajectory {traj_id}: {e}")

        except pd.errors.EmptyDataError:
            logger.error(f"Empty CSV file: {csv_file}")
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise

    # Check for JSONL files
    for jsonl_file in raw_dir.glob("*.jsonl"):
        logger.info(f"Reading trajectories from JSONL: {jsonl_file}")
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        parsed = parse_turn_data(record)
                        if parsed:
                            all_metrics.append(parsed)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON on line {line_num} in {jsonl_file}: {e}")
        except Exception as e:
            logger.error(f"Error reading JSONL file {jsonl_file}: {e}")
            raise

    # Check for JSON directory with individual files
    json_dir = raw_dir / "trajectories"
    if json_dir.exists() and json_dir.is_dir():
        logger.info(f"Reading trajectory files from directory: {json_dir}")
        for json_file in json_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                traj_id = json_file.stem
                if isinstance(data, list):
                    parsed_turns = extract_metrics_from_trajectory(data, traj_id)
                    all_metrics.extend(parsed_turns)
                elif isinstance(data, dict) and 'turns' in data:
                    parsed_turns = extract_metrics_from_trajectory(data['turns'], traj_id)
                    all_metrics.extend(parsed_turns)
            except Exception as e:
                logger.error(f"Error reading JSON file {json_file}: {e}")

    if not all_metrics:
        logger.warning("No valid turn metrics extracted. Check input data format.")
        # Return empty DataFrame with expected schema
        return pd.DataFrame(columns=[
            'turn_id', 'health', 'threat_level', 'deck_size',
            'agent_id', 'trajectory_id', 'timestamp'
        ])

    # Create DataFrame
    df = pd.DataFrame(all_metrics)

    # Ensure correct data types
    df['turn_id'] = df['turn_id'].astype(int)
    df['health'] = df['health'].astype(float)
    df['threat_level'] = df['threat_level'].astype(float)
    df['deck_size'] = df['deck_size'].astype(int)

    # Sort by trajectory_id and turn_id
    df = df.sort_values(['trajectory_id', 'turn_id']).reset_index(drop=True)

    logger.info(f"Successfully parsed {len(df)} turns from raw trajectory logs")
    return df

def main():
    """
    Main entry point for parsing raw trajectory logs.

    Reads from data/raw/trajectories.csv (or other formats in data/raw/)
    and outputs per-turn metrics to data/processed/per_turn_metrics.csv
    """
    logger.info("Starting trajectory parsing...")

    try:
        # Ensure output directory exists
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Parse trajectories
        df = parse_trajectories()

        # Save output
        output_path = PROCESSED_DATA_DIR / OUTPUT_FILE
        df.to_csv(output_path, index=False)
        logger.info(f"Saved parsed metrics to: {output_path}")

        # Print summary
        logger.info(f"Summary:")
        logger.info(f"  - Total turns: {len(df)}")
        if 'trajectory_id' in df.columns:
            logger.info(f"  - Unique trajectories: {df['trajectory_id'].nunique()}")
        if 'health' in df.columns:
            logger.info(f"  - Health range: [{df['health'].min():.2f}, {df['health'].max():.2f}]")
        if 'threat_level' in df.columns:
            logger.info(f"  - Threat range: [{df['threat_level'].min():.2f}, {df['threat_level'].max():.2f}]")
        if 'deck_size' in df.columns:
            logger.info(f"  - Deck size range: [{df['deck_size'].min()}, {df['deck_size'].max()}]")

        return df

    except Exception as e:
        logger.error(f"Failed to parse trajectories: {e}")
        raise

if __name__ == "__main__":
    main()
