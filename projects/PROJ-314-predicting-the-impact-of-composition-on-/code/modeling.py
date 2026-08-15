import pandas as pd
import numpy as np
import logging
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.base import BaseEstimator, RegressorMixin

from config import get_config_value, get_int_config
from logger import logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the constrained hyperparameter search space
# This is a list of dictionaries, where each dictionary represents a specific combination
# of hyperparameters to evaluate for a given model type.
hyperparameter_search_space: Dict[str, List[Dict[str, Any]]] = {
    "RandomForest": [
        {
            "n_estimators": [100, 200],
            "max_depth": [10, 20, None],
            "min_samples_split": [2, 5],
            "min_samples_leaf": [1, 2],
            "random_state": [42]
        },
        {
            "n_estimators": [100],
            "max_depth": [15],
            "min_samples_split": [3],
            "min_samples_leaf": [1],
            "random_state": [42]
        }
    ],
    "GradientBoosting": [
        {
            "n_estimators": [100, 200],
            "learning_rate": [0.05, 0.1],
            "max_depth": [3, 5],
            "min_samples_split": [2, 5],
            "min_samples_leaf": [1, 2],
            "random_state": [42]
        },
        {
            "n_estimators": [100],
            "learning_rate": [0.1],
            "max_depth": [4],
            "min_samples_split": [3],
            "min_samples_leaf": [1],
            "random_state": [42]
        }
    ]
}

def load_processed_data(filepath: str = "data/processed/step_final_cleaned.csv") -> pd.DataFrame:
    """Load the cleaned and processed dataset."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found at {filepath}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {filepath}")
    
    # Ensure target column exists
    if 'weibull_modulus' not in df.columns:
        raise ValueError("Target column 'weibull_modulus' not found in processed data")
    
    return df

def prepare_splits(df: pd.DataFrame, target: str = 'weibull_modulus', 
                   stratify_col: str = 'primary_anion_cation_group') -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Prepare stratified train/test splits.
    
    Logic:
    - If N >= 50, use Stratified 5-fold CV (handled in train_models loop).
    - If 30 <= N < 50, use Stratified 80/20 Hold-out.
    
    This function returns the split data for the Hold-out case or the full data for CV.
    """
    n_samples = len(df)
    
    if n_samples < 30:
        raise ValueError(f"Dataset size ({n_samples}) is below the minimum threshold of 30.")
    
    X = df.drop(columns=[target])
    y = df[target]
    
    # Check if stratification column exists and has enough unique classes
    if stratify_col in df.columns:
        unique_classes = df[stratify_col].nunique()
        min_samples_per_class = df.groupby(stratify_col).size().min()
        
        if unique_classes > 1 and min_samples_per_class >= 2:
            stratify = df[stratify_col]
            logger.info(f"Stratifying split by '{stratify_col}' with {unique_classes} classes.")
        else:
            logger.warning(f"Stratification column '{stratify_col}' has insufficient classes/samples. Falling back to non-stratified split.")
            stratify = None
    else:
        logger.warning(f"Stratification column '{stratify_col}' not found. Falling back to non-stratified split.")
        stratify = None

    if n_samples >= 50:
        # For >= 50, we use CV logic in train_models, so we return full data here
        # but the caller (train_models) will handle the CV loop.
        logger.info(f"Dataset size ({n_samples}) >= 50. Using 5-fold CV.")
        return X, y, None, None
    else:
        # For 30 <= N < 50, use 80/20 Hold-out
        logger.info(f"Dataset size ({n_samples}) < 50. Using 80/20 Hold-out.")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify if stratify is not None else None
        )
        return X_train, X_test, y_train, y_test

def validate_search_space() -> bool:
    """Validate that the hyperparameter search space is correctly defined."""
    if not isinstance(hyperparameter_search_space, dict):
        logger.error("Search space is not a dictionary.")
        return False
    
    for model_type, params_list in hyperparameter_search_space.items():
        if not isinstance(params_list, list):
            logger.error(f"Search space for {model_type} is not a list.")
            return False
        for params in params_list:
            if not isinstance(params, dict):
                logger.error(f"Parameter set for {model_type} is not a dictionary.")
                return False
    logger.info("Hyperparameter search space validation passed.")
    return True

def train_models(df: pd.DataFrame, target: str = 'weibull_modulus') -> Dict[str, Any]:
    """
    Train RF and GBM models using the defined search space.
    
    Returns a dictionary containing model metrics, best parameters, and feature importances.
    """
    if not validate_search_space():
        raise RuntimeError("Invalid hyperparameter search space.")
    
    X, y, X_test, y_test = prepare_splits(df, target)
    
    results = {
        "RandomForest": {},
        "GradientBoosting": {},
        "best_model_type": None,
        "best_score": -np.inf,
        "best_params": None,
        "best_model": None,
        "fold_importances": []
    }
    
    # Determine split strategy
    n_samples = len(df)
    use_cv = n_samples >= 50
    
    models_to_train = {
        "RandomForest": RandomForestRegressor(random_state=42),
        "GradientBoosting": GradientBoostingRegressor(random_state=42)
    }
    
    for model_name, model_class in models_to_train.items():
        logger.info(f"Training {model_name}...")
        best_score = -np.inf
        best_params = None
        best_model = None
        
        param_grid_list = hyperparameter_search_space[model_name]
        
        for param_set in param_grid_list:
            # Create a model instance with the current parameter set
            current_model = model_class(**param_set)
            
            if use_cv:
                # 5-fold Cross Validation
                cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
                # Note: StratifiedKFold requires a target for stratification.
                # We assume the target 'y' has discrete enough bins or we use a stratification column if available.
                # For regression CV, we often bin the target.
                try:
                    # Create bins for stratification if needed
                    y_bins = pd.qcut(y, q=5, duplicates='drop')
                    cv_results = cross_validate(
                        current_model, X, y, cv=cv, scoring='neg_mean_absolute_error', return_train_score=True
                    )
                    mean_mae = -np.mean(cv_results['test_score'])
                    
                    # Store feature importances for this fold if model supports it
                    if hasattr(current_model, 'feature_importances_'):
                        # We need to fit on each fold to get importances
                        fold_importances = []
                        for train_idx, val_idx in cv.split(X, y):
                            X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
                            y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
                            temp_model = model_class(**param_set)
                            temp_model.fit(X_tr, y_tr)
                            fold_importances.append(temp_model.feature_importances_)
                        
                        results["fold_importances"].append({
                            "model": model_name,
                            "params": param_set,
                            "importances": fold_importances
                        })
                        
                    logger.info(f"{model_name} with params {param_set}: Mean MAE (CV) = {mean_mae:.4f}")
                    
                except Exception as e:
                    logger.warning(f"CV failed for {model_name} with params {param_set}: {e}. Skipping.")
                    continue
            else:
                # Hold-out evaluation
                current_model.fit(X_train, y_train)
                y_pred = current_model.predict(X_test)
                mae = mean_absolute_error(y_test, y_pred)
                logger.info(f"{model_name} with params {param_set}: MAE (Hold-out) = {mae:.4f}")
                mean_mae = mae
            
            if mean_mae < best_score: # Lower MAE is better
                best_score = mean_mae
                best_params = param_set
                best_model = current_model
        
        results[model_name] = {
            "best_mae": best_score,
            "best_params": best_params,
            "best_model": best_model
        }
        
        if best_score < results["best_score"]:
            results["best_score"] = best_score
            results["best_model_type"] = model_name
            results["best_params"] = best_params
            results["best_model"] = best_model
    
    logger.info(f"Best model: {results['best_model_type']} with MAE: {results['best_score']:.4f}")
    return results

def run_baseline_predictor(df: pd.DataFrame, target: str = 'weibull_modulus') -> Dict[str, Any]:
    """
    Create a simple model that predicts the global mean Weibull modulus.
    """
    X, y, X_test, y_test = prepare_splits(df, target)
    
    global_mean = y.mean()
    
    if X_test is not None:
        y_pred = np.full_like(y_test, global_mean, dtype=float)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
    else:
        # If using CV, we can't calculate a single hold-out MAE easily here without re-running CV logic.
        # For simplicity in this context, we'll assume the baseline is evaluated on the same split logic.
        # If use_cv, we might need to do a simple CV for baseline too.
        # Let's assume for now we just return the mean and placeholder metrics if CV is used, 
        # or we re-run the split logic inside this function to ensure consistency.
        # Re-running split logic:
        if len(df) >= 50:
            # For CV, baseline is just the mean of the target. The "prediction" is constant.
            # MAE in CV would be mean(|y - mean(y)|).
            mae = np.mean(np.abs(y - global_mean))
            r2 = 0.0 # R2 of a constant predictor is 0
        else:
            # Hold out
            X_train, X_test, y_train, y_test = train_test_split(
                df.drop(columns=[target]), df[target], test_size=0.2, random_state=42
            )
            y_pred = np.full_like(y_test, global_mean, dtype=float)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
    
    return {
        "type": "GlobalMean",
        "predicted_value": global_mean,
        "mae": mae,
        "r_squared": r2
    }

def evaluate_models(baseline_metrics: Dict[str, Any], model_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate MAE, R², and compare against global mean baseline.
    """
    evaluation = {
        "baseline": baseline_metrics,
        "models": {},
        "improvement_over_baseline": {}
    }
    
    baseline_mae = baseline_metrics['mae']
    
    for model_name, res in model_results.items():
        if model_name in ["best_model_type", "best_score", "best_params", "best_model", "fold_importances"]:
            continue
        
        model_mae = res['best_mae']
        improvement = ((baseline_mae - model_mae) / baseline_mae) * 100
        
        evaluation["models"][model_name] = {
            "mae": model_mae,
            "params": res['best_params']
        }
        evaluation["improvement_over_baseline"][model_name] = {
            "mae_reduction_percent": improvement,
            "is_significant": improvement >= 10.0 # Threshold from T029
        }
    
    return evaluation

def main():
    """Main entry point for modeling tasks."""
    try:
        # Load data
        df = load_processed_data()
        
        # Run training
        model_results = train_models(df)
        
        # Run baseline
        baseline_metrics = run_baseline_predictor(df)
        
        # Evaluate
        evaluation = evaluate_models(baseline_metrics, model_results)
        
        # Save results
        output_dir = Path("data/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save baseline metrics
        baseline_path = output_dir / "baseline_metrics.json"
        with open(baseline_path, 'w') as f:
            json.dump(baseline_metrics, f, indent=2, default=str)
        logger.info(f"Baseline metrics saved to {baseline_path}")
        
        # Save model results (excluding model objects)
        serializable_results = {}
        for k, v in model_results.items():
            if k == "best_model":
                continue
            if isinstance(v, dict) and "best_model" in v:
                v_copy = v.copy()
                v_copy.pop("best_model", None)
                serializable_results[k] = v_copy
            else:
                serializable_results[k] = v
        
        results_path = output_dir / "model_training_results.json"
        with open(results_path, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        logger.info(f"Model training results saved to {results_path}")
        
        # Save evaluation
        eval_path = output_dir / "model_evaluation.json"
        with open(eval_path, 'w') as f:
            json.dump(evaluation, f, indent=2, default=str)
        logger.info(f"Evaluation results saved to {eval_path}")
        
        logger.info("Modeling pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Modeling pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()