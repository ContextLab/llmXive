import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from ..data.models import ParticipantResponse, AggregatedScore
import logging
from datetime import datetime
from pathlib import Path

from ..config import get_data_path

logger = logging.getLogger(__name__)

def filter_trials(
    trials: pd.DataFrame,
    min_latency: float = 300.0,
    max_latency: float = 10000.0
) -> pd.DataFrame:
    """
    Filter trials based on latency bounds and error handling.
    
    Args:
        trials: DataFrame of raw trials.
        min_latency: Minimum valid reaction time in ms.
        max_latency: Maximum valid reaction time in ms.
        
    Returns:
        Filtered DataFrame.
    """
    if "reaction_time" not in trials.columns:
        raise ValueError("DataFrame must contain 'reaction_time' column.")
    
    valid_trials = trials[
        (trials["reaction_time"] >= min_latency) &
        (trials["reaction_time"] <= max_latency)
    ].copy()
    
    logger.info(f"Filtered {len(trials) - len(valid_trials)} trials (latency bounds).")
    return valid_trials

def calculate_d_score(trials: pd.DataFrame) -> float:
    """
    Calculate Greenwald D2 score for a set of trials.
    
    Args:
        trials: DataFrame containing trials with 'reaction_time' and 'is_correct'.
        
    Returns:
        Calculated D-score.
    """
    if trials.empty:
        return float('nan')
    
    # Split into compatible and incompatible blocks (simplified logic)
    # In a real IAT, this would depend on session_id and block structure
    # Here we assume session_id 1 is compatible, 2 is incompatible
    
    if "session_id" not in trials.columns:
        # Fallback: calculate simple difference if session structure is missing
        mean_rt = trials["reaction_time"].mean()
        std_rt = trials["reaction_time"].std()
        if std_rt == 0:
            return 0.0
        return (mean_rt - mean_rt) / std_rt  # Dummy for single session

    compatible = trials[trials["session_id"] == 1]
    incompatible = trials[trials["session_id"] == 2]
    
    if compatible.empty or incompatible.empty:
        return float('nan')
    
    mean_c = compatible["reaction_time"].mean()
    mean_i = incompatible["reaction_time"].mean()
    
    # Pooled SD
    n_c, n_i = len(compatible), len(incompatible)
    std_c = compatible["reaction_time"].std()
    std_i = incompatible["reaction_time"].std()
    
    pooled_std = np.sqrt(((n_c - 1) * std_c**2 + (n_i - 1) * std_i**2) / (n_c + n_i - 2))
    
    if pooled_std == 0:
        return 0.0
    
    d_score = (mean_i - mean_c) / pooled_std
    return float(d_score)

def aggregate_d_scores(
    raw_df: pd.DataFrame,
    min_valid_trials: int = 10
) -> pd.DataFrame:
    """
    Aggregate raw logs into D-scores per participant and session.
    
    Args:
        raw_df: Raw response DataFrame.
        min_valid_trials: Minimum valid trials required to compute a score.
        
    Returns:
        DataFrame of aggregated D-scores.
    """
    if "participant_id" not in raw_df.columns or "session_id" not in raw_df.columns:
        raise ValueError("DataFrame must contain 'participant_id' and 'session_id' columns.")
    
    # Filter trials
    valid_trials = filter_trials(raw_df)
    
    results = []
    grouped = valid_trials.groupby(["participant_id", "session_id"])
    
    for (p_id, s_id), group in grouped:
        n_valid = len(group)
        if n_valid < min_valid_trials:
            d_score = float('nan')
            status = "insufficient_trials"
        else:
            d_score = calculate_d_score(group)
            status = "valid" if not np.isnan(d_score) else "calculation_failed"
        
        results.append({
            "participant_id": p_id,
            "session_id": s_id,
            "d_score": d_score,
            "n_trials_valid": n_valid,
            "status": status
        })
    
    return pd.DataFrame(results)

def load_raw_logs_to_dict(
    logs_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load raw logs and return as DataFrame.
    
    Args:
        logs_path: Path to raw logs.
        
    Returns:
        Loaded DataFrame.
    """
    from .load import load_response_logs
    return load_response_logs(logs_path)

def save_aggregated_scores(
    df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> None:
    """
    Save aggregated D-scores to CSV.
    
    Args:
        df: DataFrame of aggregated scores.
        output_path: Output path. If None, uses default path.
    """
    if output_path is None:
        data_path = get_data_path()
        output_path = data_path / "processed" / "aggregated_d_scores.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved aggregated scores to {output_path}")

def main() -> int:
    """Main entry point for data processing script."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting data aggregation...")
    
    try:
        raw_df = load_raw_logs_to_dict()
        aggregated_df = aggregate_d_scores(raw_df, min_valid_trials=10)
        save_aggregated_scores(aggregated_df)
        logger.info("Aggregation complete.")
        return 0
    except Exception as e:
        logger.error(f"Aggregation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    from typing import Optional
    sys.exit(main())
