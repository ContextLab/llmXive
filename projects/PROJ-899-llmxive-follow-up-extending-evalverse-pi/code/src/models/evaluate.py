import os
import sys
import json
import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
from scipy import stats

from src.utils import get_logger, write_csv, read_csv, write_json, read_json
from src.config import get_processed_data_dir, get_data_root

def load_model_results():
    """Loads model results (predictions) from T015 output."""
    # Assuming T015 saved predictions in a specific format.
    # For now, we'll assume a file 'predictions.csv' exists with columns: clip_id, dimension, prediction
    pred_file = get_processed_data_dir() / "predictions.csv"
    if not pred_file.exists():
        get_logger().error(f"Model predictions not found at {pred_file}.")
        return pd.DataFrame()
    return read_csv(pred_file)

def load_sensitivity_sweep_data():
    """Loads sensitivity sweep data from T033 output."""
    sweep_file = get_processed_data_dir() / "sensitivity_sweep_raw.csv"
    if not sweep_file.exists():
        get_logger().error(f"Sensitivity sweep data not found at {sweep_file}.")
        return pd.DataFrame()
    return read_csv(sweep_file)

def calculate_mean_predictor_error(predictions: np.ndarray, actuals: np.ndarray) -> float:
    """Calculates RMSE for a mean predictor."""
    mean_actual = np.mean(actuals)
    mean_predictions = np.full_like(actuals, mean_actual)
    mse = mean_squared_error(actuals, mean_predictions)
    return np.sqrt(mse)

def calculate_shuffled_features_error(predictions: np.ndarray, actuals: np.ndarray) -> float:
    """Calculates RMSE for shuffled features (random predictor)."""
    # Shuffle predictions randomly
    shuffled = np.random.permutation(predictions)
    mse = mean_squared_error(actuals, shuffled)
    return np.sqrt(mse)

def run_baseline_comparisons(predictions: pd.DataFrame, actuals: pd.DataFrame):
    """
    Runs baseline comparisons (Mean Predictor, Shuffled Features) and validates against best model.
    Outputs: data/baseline_results.csv with columns [dimension, predictor_type, rmse, r2]
    """
    logger = get_logger()
    logger.info("Running baseline comparisons (T019)")
    
    results = []
    dimensions = predictions['dimension'].unique()
    
    for dim in dimensions:
        pred_dim = predictions[predictions['dimension'] == dim]['prediction'].values
        actual_dim = actuals[actuals['dimension'] == dim]['human_score'].values
        
        if len(pred_dim) != len(actual_dim) or len(pred_dim) < 2:
            logger.warning(f"Skipping dimension {dim}: insufficient data")
            continue
        
        # Remove NaNs
        mask = ~(np.isnan(pred_dim) | np.isnan(actual_dim))
        pred_clean = pred_dim[mask]
        actual_clean = actual_dim[mask]
        
        if len(pred_clean) < 2:
            continue
        
        # 1. Best Model (Current predictions)
        mse_best = mean_squared_error(actual_clean, pred_clean)
        rmse_best = np.sqrt(mse_best)
        r2_best = r2_score(actual_clean, pred_clean)
        
        results.append({
            'dimension': dim,
            'predictor_type': 'best_model',
            'rmse': rmse_best,
            'r2': r2_best
        })
        
        # 2. Mean Predictor
        rmse_mean = calculate_mean_predictor_error(pred_clean, actual_clean)
        # R2 for mean predictor is 0 by definition, but we calculate it
        r2_mean = r2_score(actual_clean, np.full_like(actual_clean, np.mean(actual_clean)))
        
        results.append({
            'dimension': dim,
            'predictor_type': 'mean_predictor',
            'rmse': rmse_mean,
            'r2': r2_mean
        })
        
        # 3. Shuffled Features
        rmse_shuffled = calculate_shuffled_features_error(pred_clean, actual_clean)
        r2_shuffled = r2_score(actual_clean, np.random.permutation(actual_clean))
        
        results.append({
            'dimension': dim,
            'predictor_type': 'shuffled_features',
            'rmse': rmse_shuffled,
            'r2': r2_shuffled
        })
    
    df_results = pd.DataFrame(results)
    output_file = get_processed_data_dir() / "baseline_results.csv"
    write_csv(df_results, output_file)
    logger.info(f"Saved baseline results to {output_file}")
    
    # Validation: Check if mean_predictor_error > best_model_error for majority of dimensions
    best_model_errors = df_results[df_results['predictor_type'] == 'best_model'][['dimension', 'rmse']].copy()
    best_model_errors.columns = ['dimension', 'best_rmse']
    
    mean_errors = df_results[df_results['predictor_type'] == 'mean_predictor'][['dimension', 'rmse']].copy()
    mean_errors.columns = ['dimension', 'mean_rmse']
    
    merged = pd.merge(best_model_errors, mean_errors, on='dimension')
    if len(merged) > 0:
        majority_passed = (merged['mean_rmse'] > merged['best_rmse']).sum() > len(merged) / 2
        if not majority_passed:
            logger.warning("Validation FAILED: Mean predictor error is not greater than best model error for majority of dimensions.")
        else:
            logger.info("Validation PASSED: Mean predictor error > best model error for majority of dimensions.")
    else:
        logger.warning("No dimensions to validate.")
    
    return df_results

def generate_full_sensitivity_matrix(df_sweep: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a wide-format sensitivity matrix.
    Input: T033 output (long format: dimension, threshold, status)
    Output: Wide format (dimension, status_0.80, status_0.85, status_0.90)
    """
    if df_sweep.empty:
        return pd.DataFrame()
    
    pivot = df_sweep.pivot(index='dimension', columns='threshold', values='status')
    pivot.columns = [f'status_{col}' for col in pivot.columns]
    pivot = pivot.reset_index()
    
    output_file = get_processed_data_dir() / "sensitivity_matrix_full.csv"
    write_csv(pivot, output_file)
    return pivot

def load_sensitivity_sweep_data():
    """Loads sensitivity sweep data from T033 output."""
    sweep_file = get_processed_data_dir() / "sensitivity_sweep_raw.csv"
    if not sweep_file.exists():
        get_logger().error(f"Sensitivity sweep data not found at {sweep_file}.")
        return pd.DataFrame()
    return read_csv(sweep_file)

def calculate_stability_and_flip_rate(df_sweep: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates flip rate for each dimension.
    Flip rate = count of status changes / number of intervals (thresholds - 1)
    """
    if df_sweep.empty:
        return pd.DataFrame()
    
    results = []
    for dim in df_sweep['dimension'].unique():
        dim_data = df_sweep[df_sweep['dimension'] == dim].sort_values('threshold')
        statuses = dim_data['status'].values
        flips = 0
        for i in range(len(statuses) - 1):
            if statuses[i] != statuses[i+1]:
                flips += 1
        
        n_intervals = len(statuses) - 1
        flip_rate = flips / n_intervals if n_intervals > 0 else 0.0
        results.append({'dimension': dim, 'flip_rate': flip_rate})
    
    return pd.DataFrame(results)

def flag_threshold_sensitive(df_flip: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """Flags dimensions as 'threshold-sensitive' if flip_rate > threshold."""
    df_flip['threshold_sensitive'] = df_flip['flip_rate'] > threshold
    return df_flip

def generate_sensitivity_analysis(df_sweep: pd.DataFrame, df_flip: pd.DataFrame):
    """Generates sensitivity analysis report."""
    # Merge sweep and flip rate
    df_analysis = pd.merge(df_sweep, df_flip, on='dimension', how='left')
    output_file = get_processed_data_dir() / "sensitivity_analysis.csv"
    write_csv(df_analysis, output_file)
    return df_analysis

def generate_timing_profile(profiling_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Generates timing profile from profiling data.
    Calculates mean_time_per_clip_sec and projected_total_hours for N=10,000.
    """
    if not profiling_data:
        return pd.DataFrame()
    
    successful_times = [r['cpu_time_sec'] for r in profiling_data if r['status'] == 'success']
    if not successful_times:
        return pd.DataFrame()
    
    mean_time = sum(successful_times) / len(successful_times)
    total_clips = 10000
    projected_hours = (mean_time * total_clips) / 3600
    
    data = [{
        'mean_time_per_clip_sec': mean_time,
        'projected_total_hours': round(projected_hours, 2)
    }]
    
    df = pd.DataFrame(data)
    output_file = get_processed_data_dir() / "timing_profile.csv"
    write_csv(df, output_file)
    return df

def main():
    """Entry point for evaluate module."""
    try:
        get_logger().info("Evaluate module loaded.")
        return 0
    except Exception as e:
        get_logger().error(f"Evaluate module error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())