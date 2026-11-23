"""
Data processing module for the Implicit Bias experiment.
Handles trial filtering, D-score calculation, and aggregation.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import logging
from datetime import datetime
from pathlib import Path

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants for filtering
MIN_LATENCY_MS = 300
MAX_LATENCY_MS = 10000
MIN_VALID_TRIALS = 10
LATENCY_BLOCK_THRESHOLD = 10000  # Trials > this are blocked


def filter_trials(
    df: pd.DataFrame,
    min_latency: float = MIN_LATENCY_MS,
    max_latency: float = MAX_LATENCY_MS
) -> pd.DataFrame:
    """
    Filter trials based on latency bounds and error handling.

    Args:
        df: DataFrame containing raw trials.
        min_latency: Minimum reaction time in ms.
        max_latency: Maximum reaction time in ms.

    Returns:
        Filtered DataFrame.
    """
    logger.info(f"Filtering trials: [{min_latency}ms, {max_latency}ms]")
    initial_count = len(df)

    # Filter by latency
    filtered = df[
        (df['reaction_time'] >= min_latency) &
        (df['reaction_time'] <= max_latency)
    ]

    # Filter by correctness (optional, depending on analysis needs)
    # For D-score calculation, we typically keep errors but penalize them
    # or exclude them. Greenwald D2 includes errors by adding a penalty.

    excluded_count = initial_count - len(filtered)
    logger.info(f"Filtered {excluded_count} trials ({excluded_count/initial_count:.2%})")

    return filtered


def calculate_d_score(
    session_data: pd.DataFrame,
    include_errors: bool = True
) -> Tuple[float, int]:
    """
    Calculate Greenwald D2 score for a single session.

    The D-score is calculated as:
    D = (mean_RT_incompatible - mean_RT_compatible) / pooled_SD

    Errors are handled by adding a penalty (600ms or 1200ms depending on block).

    Args:
        session_data: DataFrame with trials for one session.
        include_errors: Whether to include error penalties.

    Returns:
        Tuple of (d_score, n_valid_trials).
    """
    if len(session_data) == 0:
        return np.nan, 0

    # Separate by condition
    compatible = session_data[session_data['condition'] == 'compatible']
    incompatible = session_data[session_data['condition'] == 'incompatible']

    if len(compatible) == 0 or len(incompatible) == 0:
        logger.warning("Missing condition data for D-score calculation.")
        return np.nan, 0

    # Handle errors (Greenwald D2 method)
    if include_errors:
        # Add penalty for errors (600ms for first block, 1200ms for second)
        # Simplified: add 600ms penalty per error
        error_penalty = 600

        compatible_rt = compatible['reaction_time'].values.copy()
        incompatible_rt = incompatible['reaction_time'].values.copy()

        error_mask_compat = compatible['is_correct'] == 0
        error_mask_incompat = incompatible['is_correct'] == 0

        compatible_rt[error_mask_compat] += error_penalty
        incompatible_rt[error_mask_incompat] += error_penalty

        mean_compat = np.mean(compatible_rt)
        mean_incompat = np.mean(incompatible_rt)

        # Pooled SD
        sd_compat = np.std(compatible_rt, ddof=1)
        sd_incompat = np.std(incompatible_rt, ddof=1)

        # Avoid division by zero
        pooled_sd = np.sqrt((sd_compat**2 + sd_incompat**2) / 2)
        if pooled_sd == 0:
            pooled_sd = 1.0

        d_score = (mean_incompat - mean_compat) / pooled_sd
    else:
        mean_compat = compatible['reaction_time'].mean()
        mean_incompat = incompatible['reaction_time'].mean()

        sd_compat = compatible['reaction_time'].std(ddof=1)
        sd_incompat = incompatible['reaction_time'].std(ddof=1)

        pooled_sd = np.sqrt((sd_compat**2 + sd_incompat**2) / 2)
        if pooled_sd == 0:
            pooled_sd = 1.0

        d_score = (mean_incompat - mean_compat) / pooled_sd

    n_valid = len(session_data)
    return d_score, n_valid


def load_raw_logs_to_dict(
    df: pd.DataFrame
) -> Dict[str, pd.DataFrame]:
    """
    Load raw logs and group by participant and session.

    Args:
        df: DataFrame with all raw logs.

    Returns:
        Dictionary mapping (participant_id, session_id) to DataFrame.
    """
    grouped = {}
    for (p_id, s_id), group in df.groupby(['participant_id', 'session_id']):
        grouped[(p_id, s_id)] = group.reset_index(drop=True)
    return grouped


def aggregate_d_scores(
    df: pd.DataFrame,
    min_valid_trials: int = MIN_VALID_TRIALS
) -> pd.DataFrame:
    """
    Aggregate D-scores for all participants and sessions.

    Args:
        df: Filtered DataFrame with valid trials.
        min_valid_trials: Minimum trials required to calculate D-score.

    Returns:
        DataFrame with aggregated D-scores.
    """
    logger.info(f"Aggregating D-scores (min_trials={min_valid_trials})")
    grouped_data = load_raw_logs_to_dict(df)

    results = []
    exclusion_log = []

    for (p_id, s_id), session_df in grouped_data.items():
        n_trials = len(session_df)

        if n_trials < min_valid_trials:
            exclusion_log.append({
                'participant_id': p_id,
                'session_id': s_id,
                'reason': 'insufficient_trials',
                'n_trials': n_trials,
                'min_required': min_valid_trials
            })
            results.append({
                'participant_id': p_id,
                'session_id': s_id,
                'd_score': np.nan,
                'n_trials_valid': n_trials,
                'status': 'excluded'
            })
        else:
            d_score, n_valid = calculate_d_score(session_df)
            results.append({
                'participant_id': p_id,
                'session_id': s_id,
                'd_score': d_score,
                'n_trials_valid': n_valid,
                'status': 'valid' if not np.isnan(d_score) else 'invalid'
            })

    # Log exclusions
    if exclusion_log:
        logger.warning(f"Excluded {len(exclusion_log)} sessions due to insufficient trials.")
        # Save exclusion report
        exclusion_df = pd.DataFrame(exclusion_log)
        logs_dir = get_project_root() / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        exclusion_df.to_csv(logs_dir / "exclusion_report.log", index=False)

    return pd.DataFrame(results)


def save_aggregated_scores(
    df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Save aggregated D-scores to CSV.

    Args:
        df: DataFrame with aggregated scores.
        output_path: Optional output path.

    Returns:
        Path to saved file.
    """
    if output_path is None:
        output_path = get_project_root() / "data" / "processed" / "d_scores_raw.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved aggregated scores to {output_path}")
    return output_path


def main():
    """
    Main entry point for data processing.
    """
    import argparse
    from utils.logging import setup_logging

    parser = argparse.ArgumentParser(
        description="Process response logs and calculate D-scores."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input CSV file with raw response logs."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for aggregated D-scores."
    )
    parser.add_argument(
        "--min-trials",
        type=int,
        default=MIN_VALID_TRIALS,
        help=f"Minimum trials required (default: {MIN_VALID_TRIALS})."
    )

    args = parser.parse_args()
    setup_logging()

    try:
        # Load data
        df = pd.read_csv(args.input)
        logger.info(f"Loaded {len(df)} rows from {args.input}")

        # Filter trials
        filtered_df = filter_trials(df)

        # Aggregate D-scores
        aggregated_df = aggregate_d_scores(filtered_df, args.min_trials)

        # Save results
        output_path = save_aggregated_scores(aggregated_df, args.output)
        logger.info(f"Processing complete. Results saved to {output_path}")

    except Exception as e:
        logger.exception(f"Error during processing: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
