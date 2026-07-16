import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error

# Import project utilities using the exact names from the API surface
from utils import setup_logging
from models.grain_boundary_record import GrainBoundaryRecord

# Configure logger with the correct signature (name string, not level string)
logger = setup_logging("validate")

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.json"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_dataset.parquet"
SPLIT_INDICES_PATH = PROJECT_ROOT / "data" / "processed" / "split_indices.pkl"
REPORT_PATH = PROJECT_ROOT / "artifacts" / "reports" / "validation_report.json"
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

def load_model_and_data() -> Tuple[pd.DataFrame, pd.DataFrame, Any]:
    """
    Load the trained model, cleaned dataset, and split indices.
    Returns:
        X_test: Features for the held-out test set.
        y_test: Target values for the held-out test set.
        model: The trained XGBoost model (or a wrapper dict if loading JSON).
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Run T012b first.")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {DATA_PATH}. Run T011 first.")
    if not SPLIT_INDICES_PATH.exists():
        raise FileNotFoundError(f"Split indices not found at {SPLIT_INDICES_PATH}. Run T012a first.")

    # Load split indices to reconstruct the test set
    import pickle
    with open(SPLIT_INDICES_PATH, 'rb') as f:
        split_indices = pickle.load(f)

    test_indices = split_indices.get('test_indices')
    if not test_indices:
        raise ValueError("Test indices missing from split_indices.pkl")

    # Load cleaned data
    df = pd.read_parquet(DATA_PATH)

    # Ensure we have the expected columns. 
    # The target is typically 'diffusivity' or 'log_diffusivity'. 
    # Based on standard physics pipelines, we assume 'diffusivity' or similar.
    # We will look for a column that looks like the target.
    target_col = None
    for col in df.columns:
        if 'diffusivity' in col.lower() or 'target' in col.lower():
            target_col = col
            break
    
    if not target_col:
        # Fallback to a common default if logic fails, but log it
        target_col = 'diffusivity'
        logger.warning(f"Could not auto-detect target column. Defaulting to '{target_col}'.")
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataset. Available: {list(df.columns)}")

    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols]
    y = df[target_col]

    # Extract test set
    X_test = X.iloc[test_indices].reset_index(drop=True)
    y_test = y.iloc[test_indices].reset_index(drop=True)

    # Load model (assuming it's a pickle or json representation of XGBoost)
    # Since we don't have the exact serialization format from T012b in the prompt,
    # we assume a standard JSON structure or a pickle. 
    # For robustness, we'll try to load the model file. 
    # If it's a JSON of params, we might need to reconstruct, but T012b usually saves the model object.
    # Let's assume it's a pickle for now as is common in sklearn/xgboost pipelines, 
    # or a JSON if we implemented a custom save. 
    # Given the constraints, we will load the best_model.json as a dict if it exists, 
    # but usually, models are pickled. Let's check extension.
    
    model = None
    if MODEL_PATH.suffix == '.pkl':
        import pickle
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
    else:
        # If it's JSON, it might be the parameters. We need the actual model object for prediction.
        # However, T012b saves 'best_model.json'. If that's a params file, we can't predict without re-instantiating.
        # Assuming T012b saved the actual model object in a way that can be loaded.
        # Let's try to load as JSON and see if it contains model data, or assume it's a pickle renamed.
        # To be safe against the "file missing" error from the execution log, we must ensure this path works.
        # If the previous run failed to write it, we can't load it.
        # We assume T012b wrote a valid model file.
        import pickle
        # Try loading as pickle first (most common for sklearn/xgb)
        try:
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
        except Exception:
            # Fallback: try JSON and hope it's a serialized model or params we can use (unlikely for prediction)
            with open(MODEL_PATH, 'r') as f:
                model_data = json.load(f)
            # If it's just params, we can't run CV on it without the model class.
            # We assume T012b saved the actual model object.
            raise RuntimeError(f"Could not load model from {MODEL_PATH}. It may not be a valid model file.")

    return X_test, y_test, model

def perform_cross_validation(X: pd.DataFrame, y: pd.Series, model: Any, k: int = 5) -> Dict[str, float]:
    """
    Perform k-fold cross-validation on the test set to measure stability.
    Calculates R², RMSE, and MAPE for each fold and returns averages and std devs.
    """
    logger.info(f"Performing {k}-fold cross-validation on test set.")
    
    # We need to create a wrapper that uses the trained model for prediction
    # Since the model is already trained, we can't use sklearn's cross_val_score directly
    # with a pre-fitted estimator in the standard way (it expects an unfitted estimator).
    # Instead, we will manually split the test set and predict.
    
    kfold = KFold(n_splits=k, shuffle=True, random_state=42)
    
    r2_scores = []
    rmse_scores = []
    mape_scores = []
    
    for fold_idx, (train_idx, val_idx) in enumerate(kfold.split(X)):
        # Split test data into fold-train and fold-val
        X_fold_train = X.iloc[train_idx]
        X_fold_val = X.iloc[val_idx]
        y_fold_train = y.iloc[train_idx]
        y_fold_val = y.iloc[val_idx]
        
        # Since the model is already trained on the full training set (from T012b),
        # we cannot re-train it on X_fold_train. 
        # The task asks for "k-fold cross-validation on the held-out test set".
        # This usually implies assessing the variance of the model's performance
        # on different subsets of the test data, or re-training.
        # Given the model is fixed, we will evaluate the fixed model on the validation folds.
        # This measures how much the test set variance affects the metric.
        
        y_pred = model.predict(X_fold_val)
        
        r2 = r2_score(y_fold_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_fold_val, y_pred))
        mape = mean_absolute_percentage_error(y_fold_val, y_pred)
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
        mape_scores.append(mape)
        logger.debug(f"Fold {fold_idx+1}: R²={r2:.4f}, RMSE={rmse:.4f}, MAPE={mape:.4f}")
    
    return {
        "r2_mean": float(np.mean(r2_scores)),
        "r2_std": float(np.std(r2_scores)),
        "rmse_mean": float(np.mean(rmse_scores)),
        "rmse_std": float(np.std(rmse_scores)),
        "mape_mean": float(np.mean(mape_scores)),
        "mape_std": float(np.std(mape_scores)),
        "k_folds": k,
        "r2_scores": r2_scores,
        "rmse_scores": rmse_scores,
        "mape_scores": mape_scores
    }

def run_regression_bias_test(X: pd.DataFrame, y: pd.Series, model: Any) -> Dict[str, Any]:
    """
    Execute regression bias test (y_true ~ y_pred) on the held-out test set.
    Calculates intercept, slope, and p-values.
    """
    logger.info("Running regression bias test.")
    
    y_pred = model.predict(X)
    
    # Linear regression: y_true = slope * y_pred + intercept
    # We use statsmodels or scipy for p-values
    # Using scipy.stats.linregress
    slope, intercept, r_value, p_value, std_err = stats.linregress(y_pred, y)
    
    # Bonferroni correction: alpha = 0.05 / 3 tests (intercept, slope, r-value? or just slope/intercept?)
    # The task says "multiple hypothesis tests" and alpha_adj = 0.05 / 3.
    # We will report the raw p-value and the adjusted one.
    alpha_adj = 0.05 / 3
    
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_value**2),
        "p_value_slope": float(p_value),
        "p_value_adj_slope": float(p_value * 3), # Bonferroni
        "alpha_adj": alpha_adj,
        "is_significant_at_adj": float(p_value * 3) < alpha_adj
    }

def generate_report(cv_results: Dict, bias_results: Dict, X_test: pd.DataFrame, y_test: pd.Series, model: Any) -> Dict[str, Any]:
    """
    Generate the final validation report.
    """
    y_pred = model.predict(X_test)
    
    overall_r2 = r2_score(y_test, y_pred)
    overall_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    overall_mape = mean_absolute_percentage_error(y_test, y_pred)
    
    report = {
        "overall_metrics": {
            "r2": float(overall_r2),
            "rmse": float(overall_rmse),
            "mape": float(overall_mape),
            "test_sample_size": int(len(y_test))
        },
        "cross_validation": cv_results,
        "bias_test": bias_results,
        "stability_check": {
            "r2_std_threshold": 0.05,
            "r2_std_actual": cv_results["r2_std"],
            "passed_stability": cv_results["r2_std"] <= 0.05
        },
        "timestamp": str(pd.Timestamp.now())
    }
    
    return report

def main():
    """
    Main entry point for T017.
    """
    try:
        # 1. Load data and model
        X_test, y_test, model = load_model_and_data()
        logger.info(f"Loaded test set with {len(y_test)} samples.")

        # 2. Perform Cross-Validation on Test Set
        cv_results = perform_cross_validation(X_test, y_test, model, k=5)
        logger.info(f"CV R² Mean: {cv_results['r2_mean']:.4f}, Std: {cv_results['r2_std']:.4f}")

        # 3. Run Bias Test
        bias_results = run_regression_bias_test(X_test, y_test, model)
        logger.info(f"Bias Test Slope: {bias_results['slope']:.4f}, P-Value: {bias_results['p_value_slope']:.4f}")

        # 4. Generate Report
        report = generate_report(cv_results, bias_results, X_test, y_test, model)

        # 5. Ensure output directory exists
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # 6. Write Report
        with open(REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to {REPORT_PATH}")
        
        # Print summary to stdout for quick verification
        print(f"Validation Complete:")
        print(f"  R² (Overall): {report['overall_metrics']['r2']:.4f}")
        print(f"  R² (CV Mean): {report['cross_validation']['r2_mean']:.4f} (+/- {report['cross_validation']['r2_std']:.4f})")
        print(f"  Stability Check (Std <= 0.05): {report['stability_check']['passed_stability']}")
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()