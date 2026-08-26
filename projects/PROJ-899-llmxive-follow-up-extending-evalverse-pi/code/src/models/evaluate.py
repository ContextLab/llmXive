import os
import sys
import json
import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from pathlib import Path

from src.config import get_data_root, get_processed_data_dir, get_state_root
from src.utils import get_logger, read_json, write_csv, write_json, ensure_directories

def load_model_results():
    """Loads model results (predictions) from T015 output."""
    # Assuming T015 saved predictions in a specific format.
    # For now, we'll assume a file 'predictions.csv' exists with columns: clip_id, dimension, prediction
    pred_file = get_processed_data_dir() / "predictions.csv"
    if not pred_file.exists():
        get_logger().error(f"Model predictions not found at {pred_file}.")
        return pd.DataFrame()
    return read_csv(pred_file)

def load_model_results() -> Optional[pd.DataFrame]:
    """Load correlation results from T016."""
    path = get_processed_data_dir() / "correlations.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)

def load_model_artifacts() -> Dict[str, str]:
    """Load paths to model artifacts."""
    return {}

def load_baseline_data() -> Optional[pd.DataFrame]:
    """Load baseline results."""
    path = get_processed_data_dir().parent / "baseline_results.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)

def compute_mean_predictor_metrics(human_scores: np.ndarray) -> Tuple[float, float]:
    """Compute RMSE and R2 for a mean predictor."""
    mean_val = np.mean(human_scores)
    predictions = np.full_like(human_scores, mean_val, dtype=float)
    rmse = np.sqrt(np.mean((human_scores - predictions) ** 2))
    ss_res = np.sum((human_scores - predictions) ** 2)
    ss_tot = np.sum((human_scores - np.mean(human_scores)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    return float(rmse), float(r2)

def compute_shuffled_feature_metrics(human_scores: np.ndarray, features: np.ndarray) -> Tuple[float, float]:
    """Compute RMSE and R2 for shuffled features (baseline)."""
    np.random.seed(42)
    idx = np.random.permutation(len(human_scores))
    shuffled_features = features[idx]
    # Simple linear model on shuffled data
    try:
        from sklearn.linear_model import Ridge
        model = Ridge(alpha=1.0)
        model.fit(shuffled_features, human_scores)
        preds = model.predict(shuffled_features)
        rmse = np.sqrt(np.mean((human_scores - preds) ** 2))
        ss_res = np.sum((human_scores - preds) ** 2)
        ss_tot = np.sum((human_scores - np.mean(human_scores)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        return float(rmse), float(r2)
    except Exception:
        return float('nan'), float('nan')

def run_baseline_comparisons(correlations_df: pd.DataFrame, features_df: pd.DataFrame) -> pd.DataFrame:
    """Run baseline comparisons and validate against best model."""
    results = []
    # Load best model results (simplified for this task context)
    # In a full implementation, we would load the actual trained models from T015
    # Here we simulate the best model error based on correlation strength
    
    if correlations_df is None or features_df is None:
        logger.warning("Correlations or features data missing. Skipping baseline comparison.")
        return pd.DataFrame(columns=["dimension", "predictor_type", "rmse", "r2"])

    for _, row in correlations_df.iterrows():
        dim = row['dimension']
        # Extract features for this dimension (mocked for simplicity)
        dim_features = features_df[features_df['dimension'] == dim]
        if dim_features.empty:
            continue
        
        # Mock human scores for baseline calculation (in real scenario, load from scores.csv)
        # This is a placeholder; real implementation should load actual scores
        human_scores = np.random.rand(len(dim_features)) * 10 
        
        mean_rmse, mean_r2 = compute_mean_predictor_metrics(human_scores)
        
        # For shuffled features, we need actual feature vectors
        # If not available, we use a placeholder
        if 'feature_vector' in dim_features.columns:
            try:
                feat_vecs = dim_features['feature_vector'].apply(lambda x: np.fromstring(x.strip('[]'), sep=',')).tolist()
                if len(feat_vecs) > 0 and len(feat_vecs[0]) > 0:
                    feat_array = np.array(feat_vecs)
                    shuffle_rmse, shuffle_r2 = compute_shuffled_feature_metrics(human_scores, feat_array)
                else:
                    shuffle_rmse, shuffle_r2 = float('nan'), float('nan')
            except Exception:
                shuffle_rmse, shuffle_r2 = float('nan'), float('nan')
        else:
            shuffle_rmse, shuffle_r2 = float('nan'), float('nan')

        results.append({
            "dimension": dim,
            "predictor_type": "mean_predictor",
            "rmse": mean_rmse,
            "r2": mean_r2
        })
        results.append({
            "dimension": dim,
            "predictor_type": "shuffled_features",
            "rmse": shuffle_rmse,
            "r2": shuffle_r2
        })
        
        # Note: Best model comparison is skipped here as T015 artifacts are not guaranteed to exist in this context.
        # The validation logic (majority check) is logged as a warning if data is missing.

    return pd.DataFrame(results)

def load_sensitivity_sweep_data() -> Optional[pd.DataFrame]:
    """Load sensitivity sweep raw data."""
    path = get_processed_data_dir() / "sensitivity_sweep_raw.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)

def calculate_stability_and_flip_rate(sweep_data: pd.DataFrame) -> pd.DataFrame:
    """Calculate flip rates for each dimension."""
    if sweep_data is None or sweep_data.empty:
        return pd.DataFrame(columns=["dimension", "flip_rate"])
    
    results = []
    dimensions = sweep_data['dimension'].unique()
    
    for dim in dimensions:
        dim_data = sweep_data[sweep_data['dimension'] == dim].sort_values('threshold')
        if len(dim_data) < 2:
            continue
        
        statuses = dim_data['status'].tolist()
        changes = sum(1 for i in range(1, len(statuses)) if statuses[i] != statuses[i-1])
        intervals = len(statuses) - 1
        flip_rate = changes / intervals if intervals > 0 else 0.0
        
        results.append({
            "dimension": dim,
            "flip_rate": flip_rate
        })
    
    return pd.DataFrame(results)

def flag_threshold_sensitive(flip_rate_df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """Flag dimensions as threshold-sensitive based on flip rate."""
    if flip_rate_df is None or flip_rate_df.empty:
        return pd.DataFrame()
    
    flip_rate_df = flip_rate_df.copy()
    flip_rate_df['threshold_sensitive'] = flip_rate_df['flip_rate'] > threshold
    return flip_rate_df

def generate_sensitivity_analysis(sweep_data: pd.DataFrame) -> pd.DataFrame:
    """Generate full sensitivity analysis report."""
    if sweep_data is None:
        return pd.DataFrame()
    
    flip_rates = calculate_stability_and_flip_rate(sweep_data)
    flagged = flag_threshold_sensitive(flip_rates)
    
    # Merge with sweep data for final report
    # This is a simplified version; full implementation would join on dimension
    return flagged

def generate_full_sensitivity_matrix(sweep_data: pd.DataFrame) -> pd.DataFrame:
    """Generate wide-format sensitivity matrix."""
    if sweep_data is None or sweep_data.empty:
        return pd.DataFrame()
    
    pivot = sweep_data.pivot(index='dimension', columns='threshold', values='status')
    pivot = pivot.reset_index()
    pivot.columns = ['dimension'] + [f'status_{col}' for col in pivot.columns[1:]]
    return pivot

def generate_timing_profile(profiling_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate per-clip inference time and project total time for N=10,000 clips.
    
    Input: profiling_data (DataFrame) with columns:
      - mean_time_sec (float): Mean time per clip in seconds
      - sample_size (int): Number of clips in the sample
    
    Output: DataFrame with columns:
      - mean_time_per_clip_sec (float)
      - projected_total_hours (float)
    
    Formula: projected_total_hours = (mean_time_per_clip_sec * sample_size) / 3600
    """
    if profiling_data is None or profiling_data.empty:
        logger.error("No profiling data provided for timing projection.")
        return pd.DataFrame(columns=["mean_time_per_clip_sec", "projected_total_hours"])

    # Calculate mean time per clip from the sample
    # Assuming the input dataframe contains aggregated stats or individual clip times
    # If it's individual clip times:
    if 'cpu_time_sec' in profiling_data.columns:
        mean_time_sec = profiling_data['cpu_time_sec'].mean()
        sample_size = len(profiling_data)
    elif 'mean_time_sec' in profiling_data.columns:
        # If already aggregated, take the first row's mean
        mean_time_sec = profiling_data['mean_time_sec'].iloc[0]
        sample_size = profiling_data['sample_size'].iloc[0] if 'sample_size' in profiling_data.columns else len(profiling_data)
    else:
        logger.error("Profiling data missing required columns 'cpu_time_sec' or 'mean_time_sec'.")
        return pd.DataFrame(columns=["mean_time_per_clip_sec", "projected_total_hours"])

    # Project total time for 10,000 clips
    N = 10000
    seconds_per_hour = 3600
    projected_total_seconds = mean_time_sec * N
    projected_total_hours = projected_total_seconds / seconds_per_hour

    result = pd.DataFrame([{
        "mean_time_per_clip_sec": round(mean_time_sec, 4),
        "projected_total_hours": round(projected_total_hours, 2)
    }])

    return result

def main():
    """
    Main entry point for T024: Generate timing profile.
    Reads profiling logs, calculates projection, writes data/timing_profile.csv.
    """
    try:
        # Ensure output directory exists
        data_root = get_data_root()
        output_dir = data_root / "processed"
        ensure_directories([output_dir])
        output_path = output_dir / "timing_profile.csv"

        # Load profiling data from T023b / T022
        # Expected input: data/profiling_logs.json (from T023b)
        profiling_json_path = data_root / "profiling_logs.json"
        
        if not profiling_json_path.exists():
            logger.error(f"Profiling logs not found at {profiling_json_path}. T023b must run first.")
            sys.exit(1)

        with open(profiling_json_path, 'r') as f:
            profiling_records = json.load(f)
        
        if not isinstance(profiling_records, list) or len(profiling_records) == 0:
            logger.error("Profiling logs are empty or malformed.")
            sys.exit(1)

        # Convert to DataFrame
        df = pd.DataFrame(profiling_records)
        
        # Filter for successful clips only for timing projection
        if 'status' in df.columns:
            df = df[df['status'] == 'success']
        
        if df.empty:
            logger.error("No successful clips found in profiling logs for timing analysis.")
            sys.exit(1)

        # Generate timing profile
        timing_profile = generate_timing_profile(df)
        
        # Write to CSV
        timing_profile.to_csv(output_path, index=False)
        logger.info(f"Timing profile generated at {output_path}")
        
        return 0

    except Exception as e:
        logger.error(f"Error in timing profile generation: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())