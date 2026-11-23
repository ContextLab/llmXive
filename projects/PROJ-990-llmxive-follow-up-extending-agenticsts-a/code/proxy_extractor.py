"""
Proxy Extractor (T007c): Extract static-log-derived utility from raw trajectory logs.

This module implements the extraction of a static proxy for layer utility based on
the frequency of layer retrieval in the validation set. It reads the master metrics
file and the validation set IDs to ensure no data leakage from the training set.

Output: data/processed/static_log_proxy.json
Schema: {trajectory_id, layer_id, utility_score}
"""

import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
METRICS_FILE = DATA_PROCESSED_DIR / "metrics_with_moves.csv"
VALIDATION_IDS_FILE = DATA_PROCESSED_DIR / "validation_set_ids.json"
OUTPUT_FILE = DATA_PROCESSED_DIR / "static_log_proxy.json"

def load_validation_ids() -> List[str]:
    """
    Load the list of trajectory IDs designated for the validation set.

    Returns:
        List[str]: List of trajectory IDs.

    Raises:
        FileNotFoundError: If the validation IDs file does not exist.
        ValueError: If the file is empty or not a valid list.
    """
    if not VALIDATION_IDS_FILE.exists():
        raise FileNotFoundError(
            f"Validation set IDs file not found: {VALIDATION_IDS_FILE}. "
            "Ensure T014a (splitter) has run successfully."
        )

    with open(VALIDATION_IDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(
            f"Validation set IDs file {VALIDATION_IDS_FILE} is empty or invalid. "
            "T014a must produce a non-empty list of IDs."
        )

    logger.info(f"Loaded {len(data)} validation trajectory IDs.")
    return data

def load_metrics_master() -> pd.DataFrame:
    """
    Load the master metrics file containing per-turn data for all trajectories.

    Returns:
        pd.DataFrame: DataFrame with columns including 'trajectory_id', 'layer_id', etc.

    Raises:
        FileNotFoundError: If the metrics file does not exist.
        ValueError: If the required columns are missing.
    """
    if not METRICS_FILE.exists():
        raise FileNotFoundError(
            f"Metrics master file not found: {METRICS_FILE}. "
            "Ensure T006 (parser) has run successfully."
        )

    df = pd.read_csv(METRICS_FILE)

    required_cols = ['trajectory_id', 'layer_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Metrics file {METRICS_FILE} is missing required columns: {missing_cols}"
        )

    logger.info(f"Loaded metrics master file with {len(df)} rows.")
    return df

def extract_static_proxy(
    metrics_df: pd.DataFrame,
    validation_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Calculate the normalized frequency of layer retrieval for each trajectory in the validation set.

    Logic:
    1. Filter the master DataFrame to include ONLY rows where trajectory_id is in validation_ids.
    2. Group by 'trajectory_id' and 'layer_id'.
    3. Count the occurrences (frequency) of each layer per trajectory.
    4. Normalize the frequency per trajectory to get a utility_score (frequency / total_turns for that trajectory).

    Args:
        metrics_df: The full metrics DataFrame.
        validation_ids: List of valid trajectory IDs.

    Returns:
        List[Dict]: List of records with {trajectory_id, layer_id, utility_score}.
    """
    # Filter for validation set only
    validation_df = metrics_df[metrics_df['trajectory_id'].isin(validation_ids)].copy()

    if validation_df.empty:
        logger.warning("No data found for the specified validation set IDs.")
        return []

    # Count frequency of each layer per trajectory
    # Assuming 'layer_id' represents the layer retrieved at that turn
    layer_counts = validation_df.groupby(['trajectory_id', 'layer_id']).size().reset_index(name='count')

    # Calculate total turns per trajectory to normalize
    total_turns = validation_df.groupby('trajectory_id').size().reset_index(name='total_turns')

    # Merge counts with totals
    proxy_df = layer_counts.merge(total_turns, on='trajectory_id')

    # Calculate normalized utility score
    proxy_df['utility_score'] = proxy_df['count'] / proxy_df['total_turns']

    # Select and format output columns
    result = proxy_df[['trajectory_id', 'layer_id', 'utility_score']].to_dict(orient='records')

    logger.info(f"Extracted static proxy for {len(result)} (trajectory, layer) pairs.")
    return result

def save_proxy_json(proxy_data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the extracted proxy data to a JSON file.

    Args:
        proxy_data: List of proxy records.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(proxy_data, f, indent=2)
    logger.info(f"Saved static proxy to {output_path}")

def main() -> None:
    """
    Main entry point for the proxy extraction task (T007c).
    """
    try:
        # 1. Load Validation IDs (Critical Check)
        validation_ids = load_validation_ids()

        # 2. Load Master Metrics
        metrics_df = load_metrics_master()

        # 3. Extract Proxy (Validation Set Only)
        proxy_data = extract_static_proxy(metrics_df, validation_ids)

        # 4. Save Output
        save_proxy_json(proxy_data, OUTPUT_FILE)

        logger.info("T007c completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during proxy extraction: {e}")
        raise

if __name__ == "__main__":
    main()
