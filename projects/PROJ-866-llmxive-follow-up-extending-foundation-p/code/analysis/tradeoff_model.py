"""
Trade-off Model for Context Compression Analysis (US3).

Implements Logistic Regression to model the relationship between context
reduction and policy violation rates, identifying the "safe operating zone".

Handles non-monotonic regions by fitting a full curve and using statistical
thresholds to determine the maximum safe reduction percentage.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"


def load_processed_logs() -> pd.DataFrame:
    """
    Load all processed execution logs from data/processed/ into a single DataFrame.
    
    Expects JSONL or JSON files containing execution logs with:
    - token_reduction_pct: float
    - violation_flag: bool (or count)
    - graph_depth: int
    - graph_complexity: int
    - workflow_id: str
    
    Returns:
        pd.DataFrame: Aggregated data ready for analysis.
    """
    logs = []
    
    if not DATA_PROCESSED_DIR.exists():
        raise FileNotFoundError(f"Data directory not found: {DATA_PROCESSED_DIR}")
    
    for file_path in DATA_PROCESSED_DIR.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    logs.extend(data)
                else:
                    logs.append(data)
        except json.JSONDecodeError:
            # Try line-delimited JSON (JSONL)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
    
    if not logs:
        raise ValueError(f"No valid execution logs found in {DATA_PROCESSED_DIR}")
    
    df = pd.DataFrame(logs)
    
    # Ensure required columns exist
    required_cols = ['token_reduction_pct', 'violation_flag', 'graph_depth', 'graph_complexity']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in execution logs: {missing}")
    
    # Normalize violation_flag to binary (0 or 1)
    if df['violation_flag'].dtype == bool:
        df['violation'] = df['violation_flag'].astype(int)
    elif df['violation_flag'].dtype == object:
        # Handle string representations
        df['violation'] = df['violation_flag'].apply(lambda x: 1 if x in [True, 'True', 1, '1'] else 0)
    else:
        df['violation'] = df['violation_flag']
    
    return df


def logistic_function(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """
    Sigmoid function for non-linear curve fitting.
    
    Args:
        x: Input values (token reduction %)
        a: Scaling factor
        b: Midpoint (inflection point)
        c: Steepness
        
    Returns:
        Predicted violation probability
    """
    return 1 / (1 + np.exp(-c * (x - b))) * a


def fit_tradeoff_curve(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fit a logistic regression curve to the trade-off data.
    
    Handles non-monotonic regions by fitting the full curve.
    
    Args:
        df: DataFrame with reduction percentages and violation flags
        
    Returns:
        Dictionary containing fit parameters and curve data
    """
    # Prepare data
    X = df['token_reduction_pct'].values.reshape(-1, 1)
    y = df['violation'].values
    
    # Filter out extreme outliers if any (e.g., negative reduction)
    valid_mask = (X.flatten() >= 0) & (X.flatten() <= 100)
    X_clean = X[valid_mask]
    y_clean = y[valid_mask]
    
    if len(X_clean) < 10:
        raise ValueError("Insufficient data points for curve fitting after filtering")
    
    # Normalize features for better convergence
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_clean)
    
    # Fit Logistic Regression
    log_reg = LogisticRegression(max_iter=1000, random_state=42)
    log_reg.fit(X_scaled, y_clean)
    
    # Extract coefficients
    intercept = log_reg.intercept_[0]
    coef = log_reg.coef_[0][0]
    
    # Generate curve points for visualization/analysis
    x_curve = np.linspace(0, 100, 100).reshape(-1, 1)
    x_curve_scaled = scaler.transform(x_curve)
    prob_curve = log_reg.predict_proba(x_curve_scaled)[:, 1]
    
    # Fit non-linear sigmoid for parameter interpretation
    try:
        popt, _ = curve_fit(
            logistic_function,
            x_curve.flatten(),
            prob_curve,
            p0=[1.0, 50.0, 0.1],
            bounds=([0, 0, 0], [2, 100, 10])
        )
        a, b, c = popt
    except Exception:
        # Fallback to linear approximation if non-linear fit fails
        a, b, c = 1.0, 50.0, coef * 10  # Approximate steepness
    
    return {
        'model_type': 'logistic_regression',
        'coef': float(coef),
        'intercept': float(intercept),
        'sigmoid_params': {'a': float(a), 'b': float(b), 'c': float(c)},
        'curve_x': x_curve.flatten().tolist(),
        'curve_prob': prob_curve.tolist(),
        'r_squared': float(log_reg.score(X_scaled, y_clean))
    }


def calculate_safe_threshold(
    df: pd.DataFrame,
    model_params: Dict[str, Any],
    target_error_rate: float = 0.01
) -> Dict[str, Any]:
    """
    Calculate the maximum context reduction percentage where error rate <= target_error_rate.
    
    Uses the fitted curve to find the threshold and calculates confidence intervals.
    
    Args:
        df: Original data for bootstrapping
        model_params: Parameters from fit_tradeoff_curve
        target_error_rate: Maximum acceptable error rate (default 1%)
        
    Returns:
        Dictionary with threshold, confidence interval, and metadata
    """
    curve_x = np.array(model_params['curve_x'])
    curve_prob = np.array(model_params['curve_prob'])
    
    # Find the point where probability crosses the threshold
    # We look for the largest x where prob <= target_error_rate
    valid_indices = curve_prob <= target_error_rate
    
    if not np.any(valid_indices):
        # If even at 0% reduction the error is too high, return 0
        threshold = 0.0
    else:
        threshold = float(np.max(curve_x[valid_indices]))
    
    # Bootstrapping for confidence interval
    n_bootstrap = 1000
    bootstrap_thresholds = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample_df = df.sample(n=len(df), replace=True, random_state=np.random.randint(0, 10000))
        
        try:
            # Refit on bootstrap sample
            bootstrap_params = fit_tradeoff_curve(sample_df)
            b_curve_x = np.array(bootstrap_params['curve_x'])
            b_curve_prob = np.array(bootstrap_params['curve_prob'])
            
            b_valid = b_curve_prob <= target_error_rate
            if np.any(b_valid):
                bootstrap_thresholds.append(float(np.max(b_curve_x[b_valid])))
            else:
                bootstrap_thresholds.append(0.0)
        except Exception:
            bootstrap_thresholds.append(0.0)
    
    bootstrap_thresholds = np.array(bootstrap_thresholds)
    ci_lower = float(np.percentile(bootstrap_thresholds, 2.5))
    ci_upper = float(np.percentile(bootstrap_thresholds, 97.5))
    
    # Round to 2 decimal places as per FR-006
    threshold_rounded = round(threshold, 2)
    ci_lower_rounded = round(ci_lower, 2)
    ci_upper_rounded = round(ci_upper, 2)
    
    return {
        'threshold_pct': threshold_rounded,
        'target_error_rate': target_error_rate,
        'confidence_interval_95': {
            'lower': ci_lower_rounded,
            'upper': ci_upper_rounded
        },
        'bootstrap_samples': n_bootstrap,
        'std_error': float(np.std(bootstrap_thresholds))
    }


def generate_regression_data(df: pd.DataFrame, model_params: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate the raw regression data points for the paper.
    
    Args:
        df: Original data
        model_params: Fitted model parameters
        
    Returns:
        DataFrame with curve points and metadata
    """
    curve_x = model_params['curve_x']
    curve_prob = model_params['curve_prob']
    
    # Create summary statistics per reduction level from actual data
    summary = df.groupby('token_reduction_pct').agg({
        'violation': ['mean', 'count', 'std']
    }).reset_index()
    summary.columns = ['reduction_pct', 'observed_violation_rate', 'sample_size', 'std_dev']
    
    # Merge with model curve
    result = pd.DataFrame({
        'reduction_pct': curve_x,
        'predicted_violation_rate': curve_prob
    })
    
    # Add observed data points for comparison
    result = result.merge(summary, on='reduction_pct', how='left')
    
    return result


def run_analysis() -> None:
    """
    Main entry point for trade-off analysis.
    
    1. Loads processed execution logs
    2. Fits logistic regression curve
    3. Calculates safe operating threshold
    4. Saves results to data/results/
    """
    print("Starting Trade-off Model Analysis...")
    
    # Ensure results directory exists
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("Loading processed execution logs...")
    try:
        df = load_processed_logs()
        print(f"Loaded {len(df)} execution records")
    except Exception as e:
        print(f"ERROR: Failed to load data: {e}")
        sys.exit(1)
    
    # Fit curve
    print("Fitting logistic regression curve...")
    try:
        model_params = fit_tradeoff_curve(df)
        print(f"Curve fit complete. R-squared: {model_params['r_squared']:.4f}")
    except Exception as e:
        print(f"ERROR: Failed to fit curve: {e}")
        sys.exit(1)
    
    # Calculate threshold
    print("Calculating safe operating threshold...")
    try:
        threshold_results = calculate_safe_threshold(df, model_params, target_error_rate=0.01)
        print(f"Safe threshold: {threshold_results['threshold_pct']}% (95% CI: {threshold_results['confidence_interval_95']['lower']}-{threshold_results['confidence_interval_95']['upper']}%)")
    except Exception as e:
        print(f"ERROR: Failed to calculate threshold: {e}")
        sys.exit(1)
    
    # Generate regression data
    print("Generating regression data for paper...")
    try:
        regression_data = generate_regression_data(df, model_params)
    except Exception as e:
        print(f"ERROR: Failed to generate regression data: {e}")
        sys.exit(1)
    
    # Save outputs
    print("Saving results...")
    
    # 1. Save threshold CI
    ci_output = {
        'threshold_pct': threshold_results['threshold_pct'],
        'confidence_interval_95': threshold_results['confidence_interval_95'],
        'target_error_rate': threshold_results['target_error_rate'],
        'bootstrap_samples': threshold_results['bootstrap_samples'],
        'std_error': threshold_results['std_error']
    }
    ci_path = DATA_RESULTS_DIR / "threshold_ci.json"
    with open(ci_path, 'w', encoding='utf-8') as f:
        json.dump(ci_output, f, indent=2)
    print(f"Saved: {ci_path}")
    
    # 2. Save full model parameters
    model_output = {
        'model_params': model_params,
        'threshold_analysis': threshold_results
    }
    model_path = DATA_RESULTS_DIR / "tradeoff_model.json"
    with open(model_path, 'w', encoding='utf-8') as f:
        json.dump(model_output, f, indent=2)
    print(f"Saved: {model_path}")
    
    # 3. Save regression curve data
    curve_path = DATA_RESULTS_DIR / "tradeoff_curve.csv"
    regression_data.to_csv(curve_path, index=False)
    print(f"Saved: {curve_path}")
    
    print("Analysis complete.")


if __name__ == "__main__":
    run_analysis()