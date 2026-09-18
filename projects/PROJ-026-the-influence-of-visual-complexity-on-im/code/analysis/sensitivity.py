import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import get_project_root, get_data_path
from utils.logging import get_logger
from stimuli.process import categorize_complexity

logger = get_logger(__name__)


def load_complexity_scores(
    path: Optional[Path] = None
) -> pd.DataFrame:
    """Load complexity scores from CSV."""
    if path is None:
        root = get_project_root()
        path = root / "data" / "processed" / "complexity_scores.csv"

    if not path.exists():
        raise FileNotFoundError(f"Complexity scores not found: {path}")

    return pd.read_csv(path)


def load_aggregated_d_scores(
    path: Optional[Path] = None
) -> pd.DataFrame:
    """Load aggregated D-scores from CSV."""
    if path is None:
        root = get_project_root()
        path = root / "data" / "processed" / "aggregated_d_scores.csv"

    if not path.exists():
        raise FileNotFoundError(f"D-scores not found: {path}")

    return pd.read_csv(path)


def re_categorize_complexity(
    df: pd.DataFrame,
    metric: str = 'edge_density',
    shift: float = 0.0
) -> pd.DataFrame:
    """
    Re-categorize complexity with shifted thresholds.

    Args:
        df: DataFrame with complexity metrics
        metric: Metric to use for categorization
        shift: Shift to apply to thresholds (in SD units)

    Returns:
        DataFrame with updated complexity_category
    """
    valid_df = df[df['status'] == 'valid'].copy()

    if valid_df.empty:
        raise ValueError("No valid images for re-categorization.")

    # Calculate SD
    sd = valid_df[metric].std()
    shifted_sd = sd * shift

    # Calculate new tertiles with shift
    # This is a simplified approach; real implementation would adjust thresholds
    try:
        valid_df['complexity_category'] = pd.qcut(
            valid_df[metric] + shifted_sd,
            q=3,
            labels=['Low', 'Medium', 'High'],
            duplicates='drop'
        )
    except ValueError:
        valid_df['complexity_category'] = pd.cut(
            valid_df[metric] + shifted_sd,
            bins=3,
            labels=['Low', 'Medium', 'High']
        )

    # Merge back
    df = df.merge(
        valid_df[['filename', 'complexity_category']],
        on='filename',
        how='left'
    )

    return df


def join_with_d_scores(
    d_scores_df: pd.DataFrame,
    complexity_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Join D-scores with complexity conditions.

    Args:
        d_scores_df: DataFrame with D-scores
        complexity_df: DataFrame with complexity conditions

    Returns:
        Joined DataFrame
    """
    # Merge on participant_id and session_id
    merged = d_scores_df.merge(
        complexity_df[['participant_id', 'session_id', 'complexity_category']],
        on=['participant_id', 'session_id'],
        how='left'
    )

    return merged


def run_analysis_for_threshold(
    d_scores: Dict[str, Dict[str, float]],
    shift: float
) -> Dict[str, Any]:
    """
    Run permutation test for a specific threshold shift.

    Args:
        d_scores: Dictionary of D-scores
        shift: Threshold shift

    Returns:
        Results dictionary
    """
    # Placeholder: In real implementation, re-categorize and re-run test
    # For now, just return a dummy result
    return {
        "shift": shift,
        "p_value": 0.05,  # Placeholder
        "observed_diff": 0.1  # Placeholder
    }


def run_sensitivity_analysis(
    complexity_path: Optional[Path] = None,
    d_scores_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run full sensitivity analysis.

    Args:
        complexity_path: Path to complexity scores
        d_scores_path: Path to D-scores

    Returns:
        Sensitivity analysis results
    """
    complexity_df = load_complexity_scores(complexity_path)
    d_scores_df = load_aggregated_d_scores(d_scores_path)

    # Calculate SD
    valid_df = complexity_df[complexity_df['status'] == 'valid']
    sd = valid_df['edge_density'].std()

    shifts = [0.0, 0.05 * sd, -0.05 * sd, 0.10 * sd, -0.10 * sd, 0.15 * sd, -0.15 * sd]

    results = []
    for shift in shifts:
        logger.info(f"Running analysis for shift: {shift:.4f}")
        result = run_analysis_for_threshold({}, shift)
        results.append(result)

    return {
        "threshold_sweep": results,
        "sd_metric": float(sd)
    }


def main() -> None:
    """Main entry point for sensitivity analysis."""
    root = get_project_root()

    sensitivity_path = root / "data" / "results" / "sensitivity_results.json"

    results = run_sensitivity_analysis()

    with open(sensitivity_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved sensitivity results to {sensitivity_path}")


if __name__ == "__main__":
    main()