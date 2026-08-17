"""
Evaluation module for baseline comparisons, timing projections, and sensitivity analysis.
"""
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from sklearn.metrics import mean_squared_error
from src.utils import get_logger, write_csv, read_json, ensure_directories
from src.config import get_data_root, get_state_root

logger = get_logger(__name__)

def calculate_baseline_mean(actuals: List[float]) -> float:
    """Calculate mean predictor baseline."""
    if not actuals:
        return 0.0
    return float(np.mean(actuals))

def calculate_baseline_shuffled(predictions: List[float], actuals: List[float]) -> float:
    """Calculate shuffled features baseline (correlation with permuted data)."""
    if len(predictions) != len(actuals) or len(predictions) < 2:
        return 0.0

    np.random.seed(42)
    shuffled_preds = np.random.permutation(predictions)

    # Calculate correlation
    corr = np.corrcoef(shuffled_preds, actuals)[0, 1]
    return float(corr) if not np.isnan(corr) else 0.0

def calculate_metrics(predictions: List[float], actuals: List[float]) -> Dict[str, float]:
    """Calculate RMSE and correlation metrics."""
    if not predictions or not actuals:
        return {"rmse": 0.0, "mae": 0.0, "r_squared": 0.0}

    predictions = np.array(predictions)
    actuals = np.array(actuals)

    rmse = float(np.sqrt(mean_squared_error(actuals, predictions)))
    mae = float(np.mean(np.abs(actuals - predictions)))

    if np.std(predictions) > 0 and np.std(actuals) > 0:
        r_squared = float(np.corrcoef(predictions, actuals)[0, 1] ** 2)
    else:
        r_squared = 0.0

    return {"rmse": rmse, "mae": mae, "r_squared": r_squared}

def run_baseline_comparisons(
    predictions: Dict[str, List[float]],
    actuals: List[float],
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Run baseline comparisons for all dimensions.

    Args:
        predictions: Dictionary of dimension -> predictions
        actuals: Human expert scores
        output_path: Path to save results

    Returns:
        DataFrame with baseline results
    """
    results = []

    for dim_name, preds in predictions.items():
        mean_baseline = calculate_baseline_mean(actuals)
        shuffled_corr = calculate_baseline_shuffled(preds, actuals)
        metrics = calculate_metrics(preds, actuals)

        results.append({
            "dimension": dim_name,
            "mean_baseline_rmse": mean_baseline,
            "shuffled_baseline_corr": shuffled_corr,
            "model_rmse": metrics["rmse"],
            "model_mae": metrics["mae"],
            "model_r_squared": metrics["r_squared"]
        })

    df = pd.DataFrame(results)

    if output_path is None:
        output_path = os.path.join(get_data_root(), "baseline_results.csv")

    ensure_directories(output_path)
    write_csv(df, output_path)
    logger.info(f"Saved baseline results to: {output_path}")

    return df

def load_scaling_profile(profile_path: Optional[str] = None) -> pd.DataFrame:
    """Load scaling profile data."""
    if profile_path is None:
        profile_path = os.path.join(get_state_root(), "scaling_validation.json")

    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Scaling profile not found: {profile_path}")

    data = read_json(profile_path)
    return pd.DataFrame(data.get("samples", []))

def calculate_inference_time_projection(
    sample_times: List[float],
    n_clips: int = 10000
) -> Dict[str, float]:
    """
    Calculate projected inference time for N clips.

    Args:
        sample_times: List of per-clip inference times in seconds
        n_clips: Number of clips to project for

    Returns:
        Dictionary with projection metrics
    """
    if not sample_times:
        return {"per_clip_seconds": 0.0, "projected_total_hours": 0.0}

    avg_time = float(np.mean(sample_times))
    projected_total_seconds = avg_time * n_clips
    projected_total_hours = projected_total_seconds / 3600

    return {
        "per_clip_seconds": avg_time,
        "projected_total_hours": projected_total_hours,
        "n_clips": n_clips
    }

def generate_timing_profile(
    profiling_data: Dict[str, Any],
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Generate timing profile from profiling data.

    Args:
        profiling_data: Dictionary with timing metrics per clip
        output_path: Path to save timing profile

    Returns:
        DataFrame with timing profile
    """
    samples = profiling_data.get("samples", [])
    if not samples:
        raise ValueError("No profiling samples found")

    times = [s.get("cpu_time_seconds", 0) for s in samples]
    projection = calculate_inference_time_projection(times)

    results = []
    for sample in samples:
        results.append({
            "clip_id": sample.get("clip_id", "unknown"),
            "cpu_time_seconds": sample.get("cpu_time_seconds", 0),
            "memory_peak_mb": sample.get("memory_peak_mb", 0)
        })

    df = pd.DataFrame(results)
    df.loc[len(df)] = {
        "clip_id": "projection",
        "cpu_time_seconds": projection["per_clip_seconds"],
        "memory_peak_mb": 0
    }

    if output_path is None:
        output_path = os.path.join(get_data_root(), "timing_profile.csv")

    ensure_directories(output_path)
    write_csv(df, output_path)
    logger.info(f"Saved timing profile to: {output_path}")

    return df

def calculate_stability_and_flip_rate(
    sweep_data: pd.DataFrame,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate stability metrics and flip rates from threshold sweep data.

    Args:
        sweep_data: DataFrame from run_threshold_sweep
        output_path: Path to save sensitivity analysis results

    Returns:
        DataFrame with stability metrics
    """
    if sweep_data.empty:
        logger.warning("Empty sweep data, returning empty result")
        return pd.DataFrame()

    results = []

    for dim_name in sweep_data["dimension"].unique():
        dim_data = sweep_data[sweep_data["dimension"] == dim_name]
        statuses = dim_data["status"].values

        # Calculate flip rate: proportion of status changes across thresholds
        flips = 0
        for i in range(1, len(statuses)):
            if statuses[i] != statuses[i-1]:
                flips += 1

        flip_rate = flips / (len(statuses) - 1) if len(statuses) > 1 else 0.0

        # Determine if threshold-sensitive
        is_sensitive = flip_rate > 0.3  # More than 30% change rate

        for _, row in dim_data.iterrows():
            results.append({
                "dimension": dim_name,
                "threshold": row["threshold"],
                "status": row["status"],
                "flip_rate": flip_rate,
                "threshold_sensitive": is_sensitive
            })

    df = pd.DataFrame(results)

    if output_path is None:
        output_path = os.path.join(get_data_root(), "sensitivity_analysis.csv")

    ensure_directories(output_path)
    write_csv(df, output_path)
    logger.info(f"Saved sensitivity analysis to: {output_path}")

    return df

def generate_full_sensitivity_matrix(
    sweep_data: pd.DataFrame,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Generate full sensitivity matrix showing all dimension-threshold combinations.

    Args:
        sweep_data: DataFrame from run_threshold_sweep
        output_path: Path to save full matrix

    Returns:
        DataFrame with full sensitivity matrix
    """
    if sweep_data.empty:
        logger.warning("Empty sweep data, returning empty result")
        return pd.DataFrame()

    # Pivot to create matrix
    matrix = sweep_data.pivot_table(
        index="dimension",
        columns="threshold",
        values="status",
        aggfunc="first"
    ).reset_index()

    if output_path is None:
        output_path = os.path.join(get_data_root(), "sensitivity_matrix_full.csv")

    ensure_directories(output_path)
    write_csv(matrix, output_path)
    logger.info(f"Saved sensitivity matrix to: {output_path}")

    return matrix

def main():
    """Main entry point for evaluation module."""
    logger.info("Evaluation module loaded")
