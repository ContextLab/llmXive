"""
Proxy Extractor (T007c): Extract static-log-derived utility (frequency of layer retrieval)
from raw trajectory logs as a distinct artifact.

Input:
  - data/processed/metrics_with_moves.csv (master file from T006)
  - data/processed/validation_set_ids.json (from T014a)

Output:
  - data/processed/static_log_proxy.json (schema: {trajectory_id, layer_id, utility_score})

Logic:
  1. Read validation_set_ids.json to filter the master file for the validation set.
  2. Calculate utility_score as the normalized frequency of layer retrieval for each trajectory.
  3. Output JSON with trajectory_id, layer_id, and utility_score.

Constraints:
  - Must process ONLY the validation set to prevent data leakage.
  - Must assert validation_set_ids.json exists and is non-empty before processing.
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
METRICS_CSV_PATH = PROJECT_ROOT / "data" / "processed" / "metrics_with_moves.csv"
VALIDATION_IDS_PATH = PROJECT_ROOT / "data" / "processed" / "validation_set_ids.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "static_log_proxy.json"


def load_validation_ids() -> List[str]:
    """
    Load validation set IDs from JSON file.
    Raises ValueError if file is missing or empty.
    """
    if not VALIDATION_IDS_PATH.exists():
        raise FileNotFoundError(
            f"Validation set IDs file not found: {VALIDATION_IDS_PATH}. "
            "Ensure T014a (splitter) has run successfully."
        )

    with open(VALIDATION_IDS_PATH, 'r') as f:
        data = json.load(f)

    ids = data.get('validation_set_ids', [])
    if not ids:
        raise ValueError(
            f"Validation set IDs file is empty or 'validation_set_ids' key is missing: {VALIDATION_IDS_PATH}. "
            "Ensure T014a produced a non-empty validation set (>= 20 trajectories)."
        )

    logger.info(f"Loaded {len(ids)} validation trajectory IDs.")
    return ids


def load_metrics_master() -> pd.DataFrame:
    """
    Load the master metrics CSV file from T006.
    Raises FileNotFoundError if the file is missing.
    """
    if not METRICS_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Master metrics file not found: {METRICS_CSV_PATH}. "
            "Ensure T006 (parser) has run successfully."
        )

    df = pd.read_csv(METRICS_CSV_PATH)
    logger.info(f"Loaded master metrics with {len(df)} rows.")
    return df


def extract_static_proxy(
    metrics_df: pd.DataFrame,
    validation_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Filter metrics to validation set and calculate normalized frequency of layer retrieval.

    Assumption: The 'metrics_with_moves.csv' contains a column 'layer_id' representing
    the retrieved layer for that turn/trajectory. If the column is missing, we infer
    layer retrieval from the presence of 'legal_moves' or a specific marker, but
    based on T006 description, we assume 'layer_id' or similar exists.

    If 'layer_id' is not present, we assume the task implies counting occurrences
    of specific move patterns or a placeholder. However, T006 output schema is:
    `trajectory_id`, `turn`, `health_ratio`, `threat_level`, `deck_size`, `move_entropy`.
    It does NOT explicitly list `layer_id`.

    Correction based on T007c description: "frequency of layer retrieval".
    If the CSV does not have `layer_id`, we must look for a column that indicates
    retrieval. If none exists, we might need to infer from the trajectory data.
    However, the task says "Input: metrics_with_moves.csv".
    Let's assume the CSV *should* have been extended to include `layer_id` or
    we derive it.
    Wait, T006 description says: "Output: data/processed/metrics_with_moves.csv with columns:
    trajectory_id, turn, health_ratio, threat_level, deck_size, move_entropy."
    It does NOT mention layer_id.

    Re-reading T007c: "extract static-log-derived utility (frequency of layer retrieval)
    from raw trajectory logs".
    Input: "data/processed/metrics_with_moves.csv".
    This implies the CSV *must* contain layer retrieval info.
    Perhaps the T006 description was incomplete, or we need to read the RAW logs again?
    But the task says "Input: metrics_with_moves.csv".
    Let's assume the CSV has a `layer_id` column (common in such pipelines) or
    we calculate frequency based on `trajectory_id` counts if `layer_id` is implicit.

    Actually, looking at the schema for T007c output: `{trajectory_id, layer_id, utility_score}`.
    This implies we need to group by `trajectory_id` and `layer_id`.
    If `layer_id` is missing in the input CSV, we cannot do this.
    However, T006 description says "parse the legal_moves array...".
    Maybe `layer_id` is derived from `legal_moves`? No, that's move entropy.
    Let's assume the `metrics_with_moves.csv` *does* have a `layer_id` column
    because otherwise T007c is impossible with the stated input.
    OR, perhaps the "raw trajectory logs" mentioned in the description implies we
    should read the raw logs for the validation set, not the CSV?
    "Input: data/processed/metrics_with_moves.csv (master file from T006) AND data/processed/validation_set_ids.json".
    This is explicit.
    Hypothesis: The T006 description in tasks.md might be slightly outdated or
    the `layer_id` is a column that was added but not listed in the summary.
    I will check for `layer_id`. If missing, I will check for `retrieved_layer` or similar.
    If still missing, I will raise an error, as I cannot fabricate data.

    Let's assume the column is named `layer_id`.
    """
    # Filter for validation set
    validation_df = metrics_df[metrics_df['trajectory_id'].isin(validation_ids)]

    if validation_df.empty:
        raise ValueError("No matching rows found in metrics CSV for the validation set IDs.")

    logger.info(f"Filtered to {len(validation_df)} rows for validation set.")

    # Check for layer_id column
    if 'layer_id' not in validation_df.columns:
        # Try common alternatives
        possible_cols = ['retrieved_layer', 'layer', 'retrieval_id']
        found_col = None
        for col in possible_cols:
            if col in validation_df.columns:
                found_col = col
                break

        if found_col:
            logger.warning(f"Column 'layer_id' not found. Using '{found_col}' as layer identifier.")
            validation_df = validation_df.rename(columns={found_col: 'layer_id'})
        else:
            # If no layer column, we cannot calculate frequency of layer retrieval.
            # However, the task requires it. We must fail loudly.
            raise KeyError(
                f"Input CSV {METRICS_CSV_PATH} lacks 'layer_id' column. "
                "Cannot calculate layer retrieval frequency. "
                "Columns found: {list(validation_df.columns)}"
            )

    # Calculate frequency per trajectory_id and layer_id
    # Group by trajectory_id and layer_id, count occurrences
    freq_counts = validation_df.groupby(['trajectory_id', 'layer_id']).size().reset_index(name='count')

    # Normalize: utility_score = count / total_turns_in_trajectory
    # First, get total turns per trajectory
    total_turns = validation_df.groupby('trajectory_id').size().reset_index(name='total_turns')

    # Merge
    result_df = freq_counts.merge(total_turns, on='trajectory_id')
    result_df['utility_score'] = result_df['count'] / result_df['total_turns']

    # Select and format output
    output_data = result_df[['trajectory_id', 'layer_id', 'utility_score']].to_dict(orient='records')

    logger.info(f"Extracted {len(output_data)} proxy records.")
    return output_data


def save_proxy_json(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the proxy data to JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved proxy data to {output_path}")


def main() -> None:
    """
    Main entry point for T007c.
    """
    logger.info("Starting T007c: Proxy Extractor")

    try:
        # 1. Load validation IDs
        validation_ids = load_validation_ids()

        # 2. Load master metrics
        metrics_df = load_metrics_master()

        # 3. Extract proxy
        proxy_data = extract_static_proxy(metrics_df, validation_ids)

        # 4. Save output
        save_proxy_json(proxy_data, OUTPUT_PATH)

        logger.info("T007c completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except KeyError as e:
        logger.error(f"Data structure error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
