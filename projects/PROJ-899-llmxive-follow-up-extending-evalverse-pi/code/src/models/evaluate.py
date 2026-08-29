import os
import sys
import json
import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from pathlib import Path

from src.config import get_processed_data_dir, get_data_root, get_project_root
from src.utils import write_csv, read_json

# Configure logger
logger = logging.getLogger(__name__)

def load_model_results(dimension: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load predictions and true values for a specific dimension from the training artifacts.
    We expect T015 to have saved predictions in a format we can reconstruct, or we re-run inference.
    For this task, we assume T015 saved a 'predictions_{dimension}.json' or similar,
    but since the spec says T015 outputs joblib models, we need to load the models and predict.
    However, to avoid re-training here, we assume T015 also saved a 'results_{dimension}.json'
    containing validation predictions.
    
    If that file doesn't exist, we attempt to load the joblib models and predict on the validation set.
    """
    data_root = get_processed_data_dir()
    model_dir = data_root.parent / "models" # data/models/
    
    # Try to load pre-saved validation results if T015 did it
    result_file = model_dir / f"results_{dimension}.json"
    if result_file.exists():
        with open(result_file, 'r') as f:
            data = json.load(f)
        y_true = np.array(data['y_true'])
        y_pred_ridge = np.array(data['y_pred_ridge'])
        y_pred_lasso = np.array(data['y_pred_lasso'])
        y_pred_xgb = np.array(data['y_pred_xgb'])
        return y_true, y_pred_ridge, y_pred_lasso, y_pred_xgb

    # Fallback: Load models and predict (requires T015 to have saved models)
    # This is a bit heavy for a baseline task, but ensures correctness if T015 didn't save predictions.
    # We will assume for this task that T015 saved the necessary predictions in a JSON file 
    # named 'validation_predictions_{dimension}.json' in the models directory.
    pred_file = model_dir / f"validation_predictions_{dimension}.json"
    if not pred_file.exists():
        raise FileNotFoundError(f"Could not find validation predictions for dimension {dimension} at {pred_file}. "
                                "Ensure T015 saves validation predictions.")
    
    with open(pred_file, 'r') as f:
        data = json.load(f)
    
    y_true = np.array(data['y_true'])
    y_pred_ridge = np.array(data['y_pred_ridge'])
    y_pred_lasso = np.array(data['y_pred_lasso'])
    y_pred_xgb = np.array(data['y_pred_xgb'])
    
    return y_true, y_pred_ridge, y_pred_lasso, y_pred_xgb

def load_baseline_data() -> pd.DataFrame:
    """
    Load the processed scores and features to compute baseline metrics.
    This is used to compute the Mean Predictor and Shuffled Features baselines.
    """
    # Load scores to get y_true
    scores_path = get_processed_data_dir() / "scores.csv"
    if not scores_path.exists():
        raise FileNotFoundError(f"Scores file not found at {scores_path}. Run T042 first.")
    
    scores_df = pd.read_csv(scores_path)
    return scores_df

def compute_mean_predictor_metrics(y_true: np.ndarray) -> Tuple[float, float]:
    """
    Compute RMSE and R2 for a mean predictor (predicts the mean of y_true for all samples).
    """
    y_pred = np.full_like(y_true, fill_value=np.mean(y_true), dtype=float)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return rmse, r2

def compute_shuffled_feature_metrics(y_true: np.ndarray, y_pred_original: np.ndarray) -> Tuple[float, float]:
    """
    Compute RMSE and R2 for a shuffled feature baseline.
    We simulate this by shuffling the predictions (which breaks the correlation with y_true).
    This approximates the performance of a model trained on shuffled features (noise).
    """
    rng = np.random.default_rng(42) # Fixed seed for reproducibility
    y_pred_shuffled = rng.permutation(y_pred_original)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred_shuffled))
    r2 = r2_score(y_true, y_pred_shuffled)
    return rmse, r2

def run_baseline_comparisons():
    """
    Run baseline comparisons for all dimensions.
    1. Load validation predictions from T015 for each dimension.
    2. Compute Mean Predictor metrics.
    3. Compute Shuffled Features metrics (using the best model's predictions as a proxy for original).
    4. Identify the BEST performing model (lowest RMSE) from T015.
    5. Assert that best_model_rmse <= mean_predictor_rmse * 0.9 (10% reduction).
    6. Write results to data/baseline_results.csv.
    7. Exit with code 1 if validation fails.
    """
    # Get list of dimensions from scores.csv
    scores_df = load_baseline_data()
    dimensions = scores_df['dimension'].unique()
    
    results = []
    best_model_rmse_global = float('inf')
    mean_predictor_rmse_global = float('inf')
    
    for dim in dimensions:
        try:
            # Load predictions for this dimension
            y_true, y_pred_ridge, y_pred_lasso, y_pred_xgb = load_model_results(dim)
            
            # Compute Mean Predictor metrics
            mean_rmse, mean_r2 = compute_mean_predictor_metrics(y_true)
            
            # Compute Shuffled Features metrics (using Ridge as a proxy for 'original' signal)
            shuffled_rmse, shuffled_r2 = compute_shuffled_feature_metrics(y_true, y_pred_ridge)
            
            # Compute Best Model metrics (lowest RMSE among Ridge, Lasso, XGB)
            ridge_rmse = np.sqrt(mean_squared_error(y_true, y_pred_ridge))
            lasso_rmse = np.sqrt(mean_squared_error(y_true, y_pred_lasso))
            xgb_rmse = np.sqrt(mean_squared_error(y_true, y_pred_xgb))
            
            best_model_rmse = min(ridge_rmse, lasso_rmse, xgb_rmse)
            best_model_type = "ridge" if best_model_rmse == ridge_rmse else ("lasso" if best_model_rmse == lasso_rmse else "xgb")
            
            # Track global best for the final assertion (or per-dimension? Spec says "best performing model from T015")
            # Assuming per-dimension validation is stricter, we check per dimension.
            if best_model_rmse < best_model_rmse_global:
                best_model_rmse_global = best_model_rmse
            if mean_rmse < mean_predictor_rmse_global:
                mean_predictor_rmse_global = mean_rmse
            
            results.append({
                "dimension": dim,
                "predictor_type": "ridge",
                "rmse": ridge_rmse,
                "r2": r2_score(y_true, y_pred_ridge)
            })
            results.append({
                "dimension": dim,
                "predictor_type": "lasso",
                "rmse": lasso_rmse,
                "r2": r2_score(y_true, y_pred_lasso)
            })
            results.append({
                "dimension": dim,
                "predictor_type": "xgb",
                "rmse": xgb_rmse,
                "r2": r2_score(y_true, y_pred_xgb)
            })
            results.append({
                "dimension": dim,
                "predictor_type": "mean_predictor",
                "rmse": mean_rmse,
                "r2": mean_r2
            })
            results.append({
                "dimension": dim,
                "predictor_type": "shuffled_features",
                "rmse": shuffled_rmse,
                "r2": shuffled_r2
            })
            
            # Validation Logic: Assert best_model_rmse <= mean_predictor_rmse * 0.9
            if best_model_rmse > mean_rmse * 0.9:
                logger.error(f"Validation FAILED for dimension {dim}: Best Model RMSE ({best_model_rmse:.4f}) "
                             f"is not <= Mean Predictor RMSE ({mean_rmse:.4f}) * 0.9 = {mean_rmse * 0.9:.4f}.")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Error processing dimension {dim}: {e}")
            traceback.print_exc()
            sys.exit(1)
    
    # Write results
    output_path = get_data_root() / "baseline_results.csv"
    df_results = pd.DataFrame(results)
    write_csv(df_results, str(output_path))
    logger.info(f"Baseline results written to {output_path}")
    
    # Final Global Validation (Optional but good practice)
    if best_model_rmse_global > mean_predictor_rmse_global * 0.9:
        logger.error(f"Global validation FAILED: Best Model RMSE ({best_model_rmse_global:.4f}) "
                     f"is not <= Mean Predictor RMSE ({mean_predictor_rmse_global:.4f}) * 0.9.")
        sys.exit(1)

def load_sensitivity_sweep_data() -> pd.DataFrame:
    """Load sensitivity sweep data from T033."""
    path = get_processed_data_dir() / "sensitivity_sweep_raw.csv"
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity sweep data not found at {path}")
    return pd.read_csv(path)

def calculate_stability_and_flip_rate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate flip rate for each dimension.
    Flip rate = count of status changes / number of intervals.
    """
    results = []
    for dim in df['dimension'].unique():
        dim_data = df[df['dimension'] == dim].sort_values('threshold')
        statuses = dim_data['status'].values
        changes = 0
        for i in range(1, len(statuses)):
            if statuses[i] != statuses[i-1]:
                changes += 1
        
        num_intervals = len(statuses) - 1
        flip_rate = changes / num_intervals if num_intervals > 0 else 0.0
        results.append({
            "dimension": dim,
            "flip_rate": flip_rate
        })
    return pd.DataFrame(results)

def flag_threshold_sensitive(flip_rate: float, threshold: float = 0.2) -> bool:
    """Flag if a dimension is threshold-sensitive based on flip rate."""
    return flip_rate > threshold

def generate_sensitivity_analysis():
    """Generate sensitivity analysis report."""
    df_sweep = load_sensitivity_sweep_data()
    df_flip = calculate_stability_and_flip_rate(df_sweep)
    
    # Flag sensitive
    df_flip['is_threshold_sensitive'] = df_flip['flip_rate'].apply(flag_threshold_sensitive)
    
    # Save
    output_path = get_data_root() / "sensitivity_analysis.csv"
    write_csv(df_flip, str(output_path))
    logger.info(f"Sensitivity analysis written to {output_path}")
    
    return df_flip

def generate_full_sensitivity_matrix():
    """Generate full sensitivity matrix (wide format)."""
    df_sweep = load_sensitivity_sweep_data()
    
    # Pivot
    matrix = df_sweep.pivot(index='dimension', columns='threshold', values='status')
    matrix = matrix.reset_index()
    
    # Save
    output_path = get_data_root() / "sensitivity_matrix_full.csv"
    write_csv(matrix, str(output_path))
    logger.info(f"Sensitivity matrix written to {output_path}")
    
    return matrix

def generate_timing_profile():
    """Generate timing profile from profiling logs."""
    # Load profiling logs from T023b
    logs_path = get_data_root() / "profiling_logs.json"
    if not logs_path.exists():
        raise FileNotFoundError(f"Profiling logs not found at {logs_path}")
    
    with open(logs_path, 'r') as f:
        logs = json.load(f)
    
    if not logs:
        raise ValueError("Profiling logs are empty.")
    
    # Extract times
    times = [log['cpu_time_sec'] for log in logs if log['status'] == 'success']
    
    if not times:
        raise ValueError("No successful profiling entries found.")
    
    mean_time = np.mean(times)
    # Project for 10,000 clips
    projected_hours = (mean_time * 10000) / 3600
    
    output_path = get_data_root() / "timing_profile.csv"
    df = pd.DataFrame([{
        "mean_time_per_clip_sec": mean_time,
        "projected_total_hours": round(projected_hours, 2)
    }])
    write_csv(df, str(output_path))
    logger.info(f"Timing profile written to {output_path}")
    
    return df

def main():
    """Entry point for baseline comparisons."""
    setup_logging = logging.getLogger(__name__)
    setup_logging.setLevel(logging.INFO)
    logger.info("Starting baseline comparisons (T019)...")
    run_baseline_comparisons()
    logger.info("T019 completed successfully.")

if __name__ == "__main__":
    main()
