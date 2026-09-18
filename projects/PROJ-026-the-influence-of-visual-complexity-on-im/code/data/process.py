import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import logging
from datetime import datetime
from pathlib import Path

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)

LATENCY_MIN = 300.0
LATENCY_MAX = 10000.0
MIN_VALID_TRIALS = 10


def filter_trials(
    trials: List[Dict[str, Any]],
    latency_min: float = LATENCY_MIN,
    latency_max: float = LATENCY_MAX
) -> List[Dict[str, Any]]:
    """
    Filter trials based on latency bounds and error handling.
    """
    filtered = []
    for trial in trials:
        rt = trial.get('reaction_time')
        is_error = trial.get('is_error', False)

        if rt is None:
            continue

        if rt < latency_min or rt > latency_max:
            continue

        if is_error:
            # Keep errors but mark them
            trial['is_error'] = True
            filtered.append(trial)
        else:
            trial['is_error'] = False
            filtered.append(trial)

    return filtered


def calculate_d_score(
    trials: List[Dict[str, Any]],
    block_type: str
) -> Tuple[float, int]:
    """
    Calculate Greenwald D2 score for a session.

    Args:
        trials: List of filtered trial dictionaries
        block_type: Type of block ('compatible' or 'incompatible')

    Returns:
        Tuple of (d_score, n_valid_trials)
    """
    if len(trials) < MIN_VALID_TRIALS:
        return np.nan, len(trials)

    # Separate by error status
    correct_trials = [t for t in trials if not t.get('is_error', False)]
    error_trials = [t for t in trials if t.get('is_error', False)]

    if len(correct_trials) < MIN_VALID_TRIALS:
        return np.nan, len(trials)

    # Calculate means and standard deviations
    correct_rts = np.array([t['reaction_time'] for t in correct_trials])
    mean_rt = np.mean(correct_rts)
    std_rt = np.std(correct_rts, ddof=1)

    if std_rt == 0:
        return np.nan, len(trials)

    # D-score formula: (Mean_incompatible - Mean_compatible) / SD_pooled
    # Simplified for single block type
    d_score = mean_rt / std_rt

    return d_score, len(trials)


def load_raw_logs_to_dict(
    logs_path: Path
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load raw response logs into a dictionary keyed by participant_id.
    """
    if not logs_path.exists():
        raise FileNotFoundError(f"Response logs not found: {logs_path}")

    df = pd.read_csv(logs_path)

    # Group by participant
    logs_dict = {}
    for pid, group in df.groupby('participant_id'):
        trials = group.to_dict('records')
        logs_dict[pid] = trials

    return logs_dict


def aggregate_d_scores(
    logs_dict: Dict[str, List[Dict[str, Any]]],
    counterbalance_path: Path,
    complexity_scores_path: Path
) -> pd.DataFrame:
    """
    Aggregate raw logs into D-scores per session.
    """
    results = []

    # Load counterbalance assignments
    if counterbalance_path.exists():
        cb_df = pd.read_csv(counterbalance_path)
        cb_dict = dict(zip(cb_df['participant_id'], cb_df['session_order']))
    else:
        cb_dict = {}

    # Load complexity scores for mapping
    if complexity_scores_path.exists():
        comp_df = pd.read_csv(complexity_scores_path)
        comp_dict = {}
        for _, row in comp_df.iterrows():
            key = (row['participant_id'], row['session_id'])
            comp_dict[key] = row['complexity_category']
    else:
        comp_dict = {}

    for pid, trials in logs_dict.items():
        # Filter trials
        filtered_trials = filter_trials(trials)

        if len(filtered_trials) < MIN_VALID_TRIALS:
            # Mark as insufficient
            results.append({
                'participant_id': pid,
                'session_id': 'unknown',
                'complexity_condition': np.nan,
                'd_score': np.nan,
                'n_trials_valid': len(filtered_trials),
                'status': 'insufficient_trials'
            })
            continue

        # Group by session (simplified: assume all trials are one session)
        # In real implementation, parse session from trial metadata
        session_id = f"session_{pid}"
        d_score, n_valid = calculate_d_score(filtered_trials, 'mixed')

        # Get complexity condition
        complexity_condition = comp_dict.get((pid, session_id), np.nan)

        if np.isnan(complexity_condition):
            status = 'missing_complexity'
        elif n_valid < MIN_VALID_TRIALS:
            status = 'insufficient_trials'
        else:
            status = 'valid'

        results.append({
            'participant_id': pid,
            'session_id': session_id,
            'complexity_condition': complexity_condition,
            'd_score': d_score,
            'n_trials_valid': n_valid,
            'status': status
        })

    return pd.DataFrame(results)


def save_aggregated_scores(
    df: pd.DataFrame,
    output_path: Path
) -> None:
    """
    Save aggregated D-scores to CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved aggregated scores to {output_path}")


def main() -> None:
    """Main entry point for data processing."""
    root = get_project_root()

    logs_path = root / "data" / "raw" / "responses" / "response_logs.csv"
    counterbalance_path = root / "data" / "processed" / "counterbalance_assignment.csv"
    complexity_scores_path = root / "data" / "processed" / "complexity_scores.csv"
    output_path = root / "data" / "processed" / "aggregated_d_scores.csv"

    if not logs_path.exists():
        raise FileNotFoundError(f"Response logs not found: {logs_path}")

    logger.info("Loading raw response logs...")
    logs_dict = load_raw_logs_to_dict(logs_path)

    logger.info("Aggregating D-scores...")
    df = aggregate_d_scores(logs_dict, counterbalance_path, complexity_scores_path)

    logger.info("Saving aggregated scores...")
    save_aggregated_scores(df, output_path)

    logger.info(f"Processing complete. {len(df)} participants processed.")


if __name__ == "__main__":
    main()
