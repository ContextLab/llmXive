"""
Conformal Prediction logic for generating prediction intervals.

Implements the Jackknife+ method using a calibration set strategy to generate
lower and upper bounds for test set predictions.
"""
import os
import sys
import json
import logging
import pickle
from typing import Dict, Any, Optional, List, Tuple, Union
import numpy as np
import pandas as pd

from src.utils.logging import get_logger
from src.utils.seeding import set_seed
from src.utils.metrics import calculate_all_metrics

# Configure logger
logger = get_logger(__name__)

def load_model_and_data(
    model_path: str,
    data_path: str
) -> Tuple[Any, pd.DataFrame]:
    """
    Load the trained model and the preprocessed data.
    
    Args:
        model_path: Path to the saved model checkpoint.
        data_path: Path to the preprocessed data CSV.
        
    Returns:
        Tuple of (model, data_frame)
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model checkpoint not found at {model_path}")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found at {data_path}")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    data = pd.read_csv(data_path)
    return model, data

def calculate_conformal_scores(
    model: Any,
    calibration_data: pd.DataFrame,
    features_col: str = 'features',
    target_col: str = 'yield'
) -> np.ndarray:
    """
    Calculate non-conformity scores on the calibration set.
    
    For regression with Jackknife+, the score is typically |y - f(x)|.
    
    Args:
        model: The trained model.
        calibration_data: DataFrame containing calibration split.
        features_col: Column name containing feature vectors.
        target_col: Column name containing true yield values.
        
    Returns:
        Array of non-conformity scores.
    """
    logger.info(f"Calculating conformal scores on {len(calibration_data)} calibration samples...")
    
    X_cal = np.array(calibration_data[features_col].tolist())
    y_cal = calibration_data[target_col].values
    
    # Get predictions
    # Assuming model.predict returns an array of shape (n_samples,) or (n_samples, 1)
    y_pred_cal = model.predict(X_cal)
    if y_pred_cal.ndim > 1:
        y_pred_cal = y_pred_cal.flatten()
    
    # Non-conformity score: absolute residual
    scores = np.abs(y_cal - y_pred_cal)
    
    logger.info(f"Calculated scores: min={scores.min():.4f}, max={scores.max():.4f}, mean={scores.mean():.4f}")
    return scores

def generate_prediction_intervals(
    model: Any,
    test_data: pd.DataFrame,
    calibration_scores: np.ndarray,
    alpha: float = 0.1,
    features_col: str = 'features',
    target_col: str = 'yield'
) -> pd.DataFrame:
    """
    Generate prediction intervals for the test set using Jackknife+ logic.
    
    Jackknife+ interval for a new point x:
    [Q_{1-alpha}(|y_i - f_{-i}(x)|) - R_new, Q_{1-alpha}(...) + R_new]
    
    Simplified implementation using the calibration set scores as the quantile estimate:
    Lower = y_pred - quantile(scores, 1-alpha)
    Upper = y_pred + quantile(scores, 1-alpha)
    
    Args:
        model: The trained model.
        test_data: DataFrame containing test split.
        calibration_scores: Array of non-conformity scores from calibration set.
        alpha: Significance level (e.g., 0.1 for 90% coverage).
        features_col: Column name containing feature vectors.
        target_col: Column name containing true yield values.
        
    Returns:
        DataFrame with original data plus 'pred_lower' and 'pred_upper'.
    """
    logger.info(f"Generating prediction intervals for {len(test_data)} test samples...")
    
    X_test = np.array(test_data[features_col].tolist())
    y_test = test_data[target_col].values
    
    # Get point predictions
    y_pred_test = model.predict(X_test)
    if y_pred_test.ndim > 1:
        y_pred_test = y_pred_test.flatten()
    
    # Calculate the quantile of the scores
    # We use (1 - alpha) quantile. For 90% coverage, alpha=0.1, we take 90th percentile.
    # Jackknife+ usually adjusts for finite sample size, but for large N, standard quantile is sufficient.
    # Adding a small finite-sample correction: use (n+1)(1-alpha) / n
    n = len(calibration_scores)
    q_level = np.ceil((n + 1) * (1 - alpha)) / n
    q_level = min(q_level, 1.0)
    
    score_quantile = np.quantile(calibration_scores, q_level)
    logger.info(f"Using score quantile ({q_level:.2f}): {score_quantile:.4f}")
    
    lower_bounds = y_pred_test - score_quantile
    upper_bounds = y_pred_test + score_quantile
    
    result = test_data.copy()
    result['pred_lower'] = lower_bounds
    result['pred_upper'] = upper_bounds
    result['pred_point'] = y_pred_test
    result['true_yield'] = y_test
    
    return result

def calculate_coverage_rate(
    results_df: pd.DataFrame,
    true_col: str = 'true_yield',
    lower_col: str = 'pred_lower',
    upper_col: str = 'pred_upper'
) -> float:
    """
    Calculate the empirical coverage rate.
    
    Args:
        results_df: DataFrame with predictions and bounds.
        true_col: Column name for true values.
        lower_col: Column name for lower bounds.
        upper_col: Column name for upper bounds.
        
    Returns:
        Coverage rate (0.0 to 1.0).
    """
    in_interval = (results_df[true_col] >= results_df[lower_col]) & \
                  (results_df[true_col] <= results_df[upper_col])
    return float(in_interval.mean())

def save_uncertainty_results(
    results_df: pd.DataFrame,
    metrics: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save the uncertainty analysis results to a JSON file and CSV.
    
    Args:
        results_df: DataFrame with intervals and true values.
        metrics: Dictionary with coverage metrics.
        output_path: Path to save the JSON summary.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save JSON summary
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved uncertainty metrics to {output_path}")
    
    # Save CSV for detailed intervals
    csv_path = output_path.replace('.json', '_intervals.csv')
    results_df.to_csv(csv_path, index=False)
    logger.info(f"Saved interval details to {csv_path}")

def run_conformal_prediction(
    model_path: str,
    data_path: str,
    output_dir: str,
    calibration_split: float = 0.2,
    alpha: float = 0.1,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Main orchestration function for Conformal Prediction analysis.
    
    Splits data into calibration and test, calculates scores, generates intervals,
    and saves results.
    
    Args:
        model_path: Path to trained model.
        data_path: Path to preprocessed data.
        output_dir: Directory to save results.
        calibration_split: Fraction of data to use for calibration (relative to test set logic, 
                           usually we split the test set or use a held-out validation set. 
                           Here we assume data_path is the 'test' set and we split it).
        alpha: Significance level.
        seed: Random seed.
        
    Returns:
        Dictionary containing coverage metrics.
    """
    set_seed(seed)
    
    logger.info(f"Starting Conformal Prediction analysis with alpha={alpha}")
    
    # Load data and model
    model, data = load_model_and_data(model_path, data_path)
    
    # Split data into calibration and test sets
    # We assume the input data is the set we want to predict on, so we split it
    # to get calibration scores.
    n = len(data)
    n_cal = int(n * calibration_split)
    
    indices = np.random.permutation(n)
    cal_indices = indices[:n_cal]
    test_indices = indices[n_cal:]
    
    calibration_data = data.iloc[cal_indices].reset_index(drop=True)
    test_data = data.iloc[test_indices].reset_index(drop=True)
    
    logger.info(f"Split data: {n_cal} calibration, {len(test_data)} test")
    
    # Calculate conformal scores on calibration set
    scores = calculate_conformal_scores(model, calibration_data)
    
    # Generate intervals for test set
    results_df = generate_prediction_intervals(
        model, test_data, scores, alpha=alpha
    )
    
    # Calculate coverage
    coverage = calculate_coverage_rate(results_df)
    
    # Calculate point prediction metrics on test set
    y_true = results_df['true_yield'].values
    y_pred = results_df['pred_point'].values
    point_metrics = calculate_all_metrics(y_true, y_pred)
    
    # Compile results
    final_metrics = {
        "alpha": alpha,
        "target_coverage": 1.0 - alpha,
        "empirical_coverage": coverage,
        "coverage_gap": float(coverage - (1.0 - alpha)),
        "calibration_set_size": len(calibration_data),
        "test_set_size": len(test_data),
        "point_prediction_metrics": point_metrics,
        "score_statistics": {
            "min": float(scores.min()),
            "max": float(scores.max()),
            "mean": float(scores.mean()),
            "std": float(scores.std())
        }
    }
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    summary_path = os.path.join(output_dir, "uncertainty_metrics.json")
    save_uncertainty_results(results_df, final_metrics, summary_path)
    
    logger.info(f"Conformal Prediction analysis complete. Coverage: {coverage:.2%}")
    return final_metrics

def main():
    """
    Entry point for the uncertainty analysis script.
    Reads configuration from environment or defaults, then runs the analysis.
    """
    # Default paths
    model_path = os.getenv("MODEL_PATH", "data/models/mpnn_best.pt")
    data_path = os.getenv("DATA_PATH", "data/preprocessed/test_set.csv")
    output_dir = os.getenv("OUTPUT_DIR", "results/uncertainty")
    
    # Parameters
    calibration_split = float(os.getenv("CALIBRATION_SPLIT", "0.2"))
    alpha = float(os.getenv("ALPHA", "0.1"))
    seed = int(os.getenv("SEED", "42"))
    
    try:
        metrics = run_conformal_prediction(
            model_path=model_path,
            data_path=data_path,
            output_dir=output_dir,
            calibration_split=calibration_split,
            alpha=alpha,
            seed=seed
        )
        print(json.dumps(metrics, indent=2))
    except Exception as e:
        logger.error(f"Conformal Prediction analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
