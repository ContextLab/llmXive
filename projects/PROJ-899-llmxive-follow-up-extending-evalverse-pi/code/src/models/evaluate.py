import os
import sys
import json
import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score

from src.config import get_processed_data_dir, get_data_root
from src.utils import write_csv, read_csv, get_logger

logger = get_logger(__name__)

def load_model_results() -> Dict[str, Any]:
    """Load correlation results and model performance metrics."""
    processed_dir = get_processed_data_dir()
    correlations_file = processed_dir / "correlations.csv"
    
    if not correlations_file.exists():
        raise FileNotFoundError(f"Correlation results file not found: {correlations_file}")
    
    df = pd.read_csv(correlations_file)
    return df.to_dict(orient='records')

def load_baseline_data() -> pd.DataFrame:
    """Load the processed correlation data used for baseline comparison."""
    processed_dir = get_processed_data_dir()
    # Load the point estimates file which contains the dimensions and their scores
    # We need the actual human scores to compute baselines against
    scores_file = processed_dir.parent / "scores.csv"
    
    if not scores_file.exists():
        raise FileNotFoundError(f"Scores file not found: {scores_file}")
    
    return pd.read_csv(scores_file)

def compute_mean_predictor_metrics(human_scores: pd.Series) -> Tuple[float, float]:
    """
    Compute RMSE and R2 for a mean predictor.
    The mean predictor predicts the mean of human_scores for every sample.
    """
    if human_scores.empty:
        raise ValueError("Human scores series is empty")
    
    mean_val = human_scores.mean()
    predictions = pd.Series([mean_val] * len(human_scores), index=human_scores.index)
    
    rmse = np.sqrt(mean_squared_error(human_scores, predictions))
    r2 = r2_score(human_scores, predictions)
    
    return rmse, r2

def compute_shuffled_feature_metrics(human_scores: pd.Series, n_permutations: int = 1000) -> Tuple[float, float]:
    """
    Compute average RMSE and R2 for a shuffled predictor.
    The shuffled predictor randomly permutes the human scores and uses that as prediction.
    """
    if human_scores.empty:
        raise ValueError("Human scores series is empty")
    
    rmse_values = []
    r2_values = []
    
    for _ in range(n_permutations):
        shuffled = human_scores.sample(frac=1, replace=False).reset_index(drop=True)
        # Align indices if necessary, but sample resets index so we compare by position
        # However, to be safe with pandas alignment, we re-index
        shuffled.index = human_scores.index
        
        rmse = np.sqrt(mean_squared_error(human_scores, shuffled))
        r2 = r2_score(human_scores, shuffled)
        
        rmse_values.append(rmse)
        r2_values.append(r2)
    
    avg_rmse = np.mean(rmse_values)
    avg_r2 = np.mean(r2_values)
    
    return avg_rmse, avg_r2

def run_baseline_comparisons() -> pd.DataFrame:
    """
    Run baseline comparisons for all dimensions.
    Outputs a DataFrame with columns: [dimension, predictor_type, rmse, r2]
    """
    scores_df = load_baseline_data()
    results = []
    
    dimensions = scores_df['dimension'].unique()
    
    logger.info(f"Running baseline comparisons for {len(dimensions)} dimensions")
    
    for dim in dimensions:
        dim_data = scores_df[scores_df['dimension'] == dim]
        
        if dim_data.empty:
            logger.warning(f"No data found for dimension: {dim}")
            continue
        
        human_scores = dim_data['human_score']
        
        if human_scores.isna().all():
            logger.warning(f"All human scores are NaN for dimension: {dim}")
            continue
        
        # Filter out NaN scores for calculation
        valid_mask = human_scores.notna()
        valid_scores = human_scores[valid_mask]
        
        if len(valid_scores) < 2:
            logger.warning(f"Not enough valid samples for dimension: {dim}")
            continue
        
        # Mean Predictor
        mean_rmse, mean_r2 = compute_mean_predictor_metrics(valid_scores)
        results.append({
            'dimension': dim,
            'predictor_type': 'mean',
            'rmse': mean_rmse,
            'r2': mean_r2
        })
        
        # Shuffled Predictor
        shuffled_rmse, shuffled_r2 = compute_shuffled_feature_metrics(valid_scores)
        results.append({
            'dimension': dim,
            'predictor_type': 'shuffled',
            'rmse': shuffled_rmse,
            'r2': shuffled_r2
        })
    
    return pd.DataFrame(results)

def load_sensitivity_sweep_data() -> pd.DataFrame:
    """Load sensitivity sweep raw data."""
    processed_dir = get_processed_data_dir()
    file_path = processed_dir / "sensitivity_sweep_raw.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Sensitivity sweep data not found: {file_path}")
    
    return pd.read_csv(file_path)

def calculate_stability_and_flip_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate flip rates for each dimension across thresholds."""
    if 'dimension' not in df.columns or 'threshold' not in df.columns or 'status' not in df.columns:
        raise ValueError("DataFrame missing required columns: dimension, threshold, status")
    
    results = []
    dimensions = df['dimension'].unique()
    
    for dim in dimensions:
        dim_data = df[df['dimension'] == dim].sort_values('threshold')
        
        if len(dim_data) < 2:
            continue
        
        statuses = dim_data['status'].values
        changes = 0
        for i in range(1, len(statuses)):
            if statuses[i] != statuses[i-1]:
                changes += 1
        
        # Number of intervals = number of thresholds - 1
        n_intervals = len(dim_data) - 1
        flip_rate = changes / n_intervals if n_intervals > 0 else 0.0
        
        results.append({
            'dimension': dim,
            'flip_rate': flip_rate
        })
    
    return pd.DataFrame(results)

def flag_threshold_sensitive(df: pd.DataFrame, threshold: float = 0.1) -> pd.DataFrame:
    """Flag dimensions as threshold-sensitive if flip_rate > threshold."""
    df = df.copy()
    df['is_sensitive'] = df['flip_rate'] > threshold
    return df

def generate_sensitivity_analysis() -> None:
    """Generate sensitivity analysis report."""
    try:
        sweep_data = load_sensitivity_sweep_data()
        flip_rates = calculate_stability_and_flip_rate(sweep_data)
        flagged = flag_threshold_sensitive(flip_rates)
        
        output_path = get_processed_data_dir() / "sensitivity_analysis.csv"
        write_csv(output_path, flagged.to_dict(orient='records'))
        logger.info(f"Sensitivity analysis written to {output_path}")
    except Exception as e:
        logger.error(f"Error generating sensitivity analysis: {e}")
        raise

def generate_full_sensitivity_matrix() -> None:
    """Generate full sensitivity matrix (wide format)."""
    try:
        sweep_data = load_sensitivity_sweep_data()
        
        pivot = sweep_data.pivot(index='dimension', columns='threshold', values='status')
        pivot = pivot.reset_index()
        
        # Rename columns to match schema requirement
        pivot.columns = ['dimension'] + [f'status_{col}' for col in pivot.columns[1:]]
        
        output_path = get_processed_data_dir() / "sensitivity_matrix_full.csv"
        write_csv(output_path, pivot.to_dict(orient='records'))
        logger.info(f"Sensitivity matrix written to {output_path}")
    except Exception as e:
        logger.error(f"Error generating sensitivity matrix: {e}")
        raise

def generate_timing_profile() -> None:
    """Generate timing profile from profiling logs."""
    try:
        processed_dir = get_processed_data_dir()
        profiling_file = processed_dir.parent / "profiling_logs.json"
        
        if not profiling_file.exists():
            raise FileNotFoundError(f"Profiling logs not found: {profiling_file}")
        
        with open(profiling_file, 'r') as f:
            logs = json.load(f)
        
        if not logs:
            raise ValueError("Profiling logs are empty")
        
        times = [log['cpu_time_sec'] for log in logs if log.get('status') == 'success']
        
        if not times:
            raise ValueError("No successful profiling entries found")
        
        mean_time = np.mean(times)
        sample_size = len(times)
        
        # Project for 10,000 clips
        projected_hours = (mean_time * 10000) / 3600
        
        result = {
            'mean_time_per_clip_sec': round(mean_time, 4),
            'projected_total_hours': round(projected_hours, 2)
        }
        
        output_path = processed_dir / "timing_profile.csv"
        df = pd.DataFrame([result])
        write_csv(output_path, df.to_dict(orient='records'))
        logger.info(f"Timing profile written to {output_path}")
    except Exception as e:
        logger.error(f"Error generating timing profile: {e}")
        raise

def main() -> None:
    """Main entry point for T019a: Baseline Predictors."""
    logger.info("Starting T019a: Implementing baseline predictors...")
    
    try:
        # Run baseline comparisons
        baseline_results = run_baseline_comparisons()
        
        if baseline_results.empty:
            logger.warning("No baseline results generated. Check input data.")
            return
        
        # Save to data/processed/baseline_predictions.csv as per task spec
        output_path = get_processed_data_dir() / "baseline_predictions.csv"
        write_csv(output_path, baseline_results.to_dict(orient='records'))
        
        logger.info(f"Baseline predictions written to {output_path}")
        logger.info("T019a completed successfully.")
        
    except Exception as e:
        logger.error(f"T019a failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
