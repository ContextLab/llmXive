"""
Random Forest Modeling with GridSearchCV and Hard Timeout Enforcement.

Implements T030:
- Trains a Random Forest model on residuals (from T022) and interaction features.
- Uses GridSearchCV with n_estimators in [50, 100, 200] and max_depth in [5, 10, 20].
- Enforces a hard timeout (default 4 hours). If timeout occurs, it interrupts
  the grid search and re-runs with a reduced configuration (n_estimators=100, max_depth=10).
- Consumes collinearity report (from T023) to log warnings about flagged pairs.
"""
import os
import sys
import json
import logging
import argparse
import signal
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.exceptions import ConvergenceWarning

# Import from local project modules (per API surface)
# Note: Using relative imports assumes this file is run via python -m or sys.path setup
# For robustness in this script, we add the parent 'code' directory to sys.path if needed
if 'code' not in sys.path:
    code_root = Path(__file__).resolve().parent.parent
    if code_root.name == 'code':
        sys.path.insert(0, str(code_root))
    else:
        # Fallback if structure is different
        sys.path.insert(0, str(code_root.parent))

from config import get_config
from data.preprocessing import load_processed_data

# Suppress sklearn convergence warnings for cleaner logs
logging.getLogger('sklearn').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# --- Timeout Handling ---

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("GridSearchCV execution timed out.")

def run_with_timeout(func, args=(), kwargs=None, timeout_seconds=14400):
    """
    Runs a function with a hard timeout using signal alarm.
    If timeout occurs, returns None and sets a flag.
    """
    if kwargs is None:
        kwargs = {}

    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        result = func(*args, **kwargs)
        return result, False  # Result, timed_out
    except TimeoutError:
        logger.warning("Timeout occurred during GridSearchCV.")
        return None, True
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

# --- Core Logic ---

def load_and_prepare_data(config: Dict[str, Any]) -> Tuple[pd.DataFrame, list, list]:
    """
    Loads preprocessed data (residuals) and feature sets.
    Consumes output from T022 (residuals) and T020 (interactions).
    """
    data_path = Path(config['paths']['processed_data'])
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. "
                                "Ensure T022 (preprocessing) has run successfully.")

    df = load_processed_data(data_path)
    
    # Identify target and features based on config or standard naming
    target_col = config.get('target_column', 'residual_grain_size')
    if target_col not in df.columns:
        # Fallback if residual column name differs
        target_candidates = [c for c in df.columns if 'residual' in c.lower()]
        if target_candidates:
            target_col = target_candidates[0]
            logger.warning(f"Target column '{target_col}' not found, using '{target_candidates[0]}'")
        else:
            raise ValueError(f"Could not find target column (expected '{target_col}' or 'residual_*') in {df.columns}")

    # Feature columns: exclude target and non-numeric metadata
    feature_cols = [c for c in df.columns if c != target_col and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if not feature_cols:
        raise ValueError("No numeric feature columns found for modeling.")

    X = df[feature_cols]
    y = df[target_col]

    logger.info(f"Loaded data: {X.shape[0]} samples, {len(feature_cols)} features.")
    logger.info(f"Target column: {target_col}")
    return X, y, feature_cols

def load_collinearity_report(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Loads the collinearity report generated in T023."""
    report_path = Path(config['paths']['collinearity_report'])
    if report_path.exists():
        with open(report_path, 'r') as f:
            return json.load(f)
    else:
        logger.warning(f"Collinearity report not found at {report_path}. Skipping collinearity checks.")
        return None

def train_rf_model(X: pd.DataFrame, y: pd.Series, config: Dict[str, Any], 
                   grid_params: Dict[str, Any], timeout_seconds: int) -> Tuple[Any, Dict[str, Any], bool]:
    """
    Trains Random Forest with GridSearchCV.
    Returns: (best_model, metrics_dict, timed_out)
    """
    logger.info(f"Starting GridSearchCV with params: {grid_params}")
    
    # Define the estimator
    rf = RandomForestRegressor(random_state=config.get('seed', 42), n_jobs=-1)
    
    # Use StratifiedKFold if target is discrete, otherwise KFold. 
    # Since target is residual (continuous), we use KFold or just default.
    # However, T022b mentions StratifiedGroupKFold. Here we stick to standard CV for RF unless grouped.
    # For simplicity and robustness with continuous targets in RF, we use standard KFold.
    from sklearn.model_selection import KFold
    cv = KFold(n_splits=5, shuffle=True, random_state=config.get('seed', 42))

    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=grid_params,
        cv=cv,
        scoring='r2',
        n_jobs=-1,
        verbose=2
    )

    # Run with timeout
    result, timed_out = run_with_timeout(
        grid_search.fit, 
        args=(X, y), 
        timeout_seconds=timeout_seconds
    )

    if timed_out or result is None:
        return None, {}, True

    best_model = result.best_estimator_
    metrics = {
        'best_params': result.best_params_,
        'best_score': float(result.best_score_),
        'cv_results': result.cv_results_
    }
    
    logger.info(f"GridSearchCV completed. Best R²: {metrics['best_score']:.4f}")
    return best_model, metrics, False

def run_rf_pipeline(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main pipeline for T030:
    1. Load data (residuals).
    2. Check collinearity report.
    3. Run GridSearchCV with timeout.
    4. If timeout, fallback to reduced grid.
    5. Save model and report.
    """
    if config is None:
        config = get_config()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(config['paths']['log_file'])
        ]
    )

    logger.info("Starting Random Forest Modeling Pipeline (T030)...")

    # 1. Load Data
    try:
        X, y, feature_cols = load_and_prepare_data(config)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

    # 2. Check Collinearity Report
    collinearity_report = load_collinearity_report(config)
    if collinearity_report and 'flagged_pairs' in collinearity_report:
        logger.warning("Collinearity detected in features. Interpreting interaction effects with caution.")
        for pair in collinearity_report['flagged_pairs']:
            logger.warning(f"  Flagged pair: {pair}")

    # 3. Define Grid
    # Task: n_estimators: [-200], max_depth: [-20] -> interpreted as ranges up to these values
    # We use a reasonable range including the max values specified.
    grid_params = {
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 10, 20],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }

    timeout_seconds = config.get('GITHUB_ACTIONS_TIMEOUT', 5 * 3600)
    # We allocate a portion of the total time for this step, e.g., 3 hours
    step_timeout = min(timeout_seconds, 3 * 3600) 

    # 4. Train with Timeout
    model, metrics, timed_out = train_rf_model(X, y, config, grid_params, step_timeout)

    if timed_out or model is None:
        logger.warning("First GridSearchCV timed out. Re-running with reduced parameters...")
        # Fallback: Reduced grid
        fallback_params = {
            'n_estimators': [100],
            'max_depth': [10],
            'min_samples_split': [2],
            'min_samples_leaf': [1]
        }
        model, metrics, timed_out = train_rf_model(X, y, config, fallback_params, step_timeout)
        
        if timed_out or model is None:
            logger.error("Fallback GridSearchCV also timed out. Pipeline failed.")
            # We still try to save what we have or exit
            raise TimeoutError("Model training failed due to repeated timeouts.")

    # 5. Evaluate on Holdout (Optional but good practice)
    # For this task, we rely on CV score, but let's compute a simple train/test split if needed.
    # We'll just use the CV best score as the primary metric.
    
    # 6. Save Artifacts
    output_dir = Path(config['paths']['model_artifacts'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = output_dir / 'rf_model.pkl'
    report_path = output_dir / 'rf_report.json'

    import joblib
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")

    # Prepare report
    final_report = {
        'task_id': 'T030',
        'model_type': 'RandomForestRegressor',
        'metrics': {
            'best_cv_r2': metrics['best_score'],
            'best_params': metrics['best_params']
        },
        'timeout_fallback_used': timed_out, # Actually, this logic is slightly off in variable naming, fixed below
        'feature_count': len(feature_cols),
        'collinearity_warnings': collinearity_report['flagged_pairs'] if collinearity_report else []
    }
    
    # Correct the fallback flag logic
    # We need to know if we actually used the fallback.
    # Since we re-ran, we can't easily know the first run's params from the result unless we stored them.
    # Let's assume if best_params == fallback_params, we used it.
    if metrics['best_params'] == {k: v[0] if isinstance(v, list) else v for k, v in fallback_params.items()}:
        final_report['timeout_fallback_used'] = True
    else:
        final_report['timeout_fallback_used'] = False

    with open(report_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    logger.info(f"Report saved to {report_path}")

    return final_report

def main():
    parser = argparse.ArgumentParser(description="Run Random Forest Modeling Pipeline (T030)")
    parser.add_argument('--config', type=str, default=None, help="Path to config file")
    args = parser.parse_args()

    config = get_config()
    
    try:
        result = run_rf_pipeline(config)
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
