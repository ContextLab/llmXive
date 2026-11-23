import os
import sys
import json
import logging
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import pandas as pd

# Local imports based on project API surface
from config import CONFIG, ensure_dirs
from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)

def load_data_and_model() -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, RandomForestRegressor, List[str]]:
    """
    Loads the preprocessed data and the trained DFT-enhanced Random Forest model.
    Expects data at CONFIG.PROCESSED_DATA_PATH and model at CONFIG.MODEL_PATH.
    """
    data_path = Path(CONFIG.PROCESSED_DATA_PATH)
    model_path = Path(CONFIG.MODEL_PATH)

    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run modeling pipeline first.")
    if not model_path.exists():
        raise FileNotFoundError(f"Trained model not found at {model_path}. Run training pipeline first.")

    # Load data
    # Assuming the processed data CSV has feature columns and a target column 'yield_strength_MPa'
    df = pd.read_csv(data_path)
    
    # Identify target and features
    target_col = 'yield_strength_MPa'
    if target_col not in df.columns:
        # Fallback or error if column name differs, but spec implies this name
        raise ValueError(f"Target column '{target_col}' not found in {data_path}. Columns: {df.columns.tolist()}")
    
    y = df[target_col].values
    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols].values
    feature_names = feature_cols

    # Load model
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    logger.info(f"Loaded data: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Loaded model: {type(model).__name__}")

    return df, X, y, model, feature_names

def run_sample_size_sweep(X: np.ndarray, y: np.ndarray, model_type: RandomForestRegressor, 
                          feature_names: List[str], min_n: int = 10, max_n: int = None, 
                          step: int = 5, n_iterations: int = 5) -> Dict[str, Any]:
    """
    Runs a sample-size sweep to check stability of feature importance as dataset size grows.
    This function is referenced in T037 but implemented here for completeness.
    """
    if max_n is None:
        max_n = len(X)
    
    results = {}
    sizes = list(range(min_n, max_n + 1, step))

    for n in sizes:
        importance_stds = []
        for i in range(n_iterations):
            # Resample
            indices = np.random.choice(len(X), size=n, replace=False)
            X_sub, y_sub = X[indices], y[indices]
            
            # Train model
            clf = model_type(random_state=CONFIG.SEED)
            clf.fit(X_sub, y_sub)
            
            # Get importance
            importances = clf.feature_importances_
            importance_stds.append(importances)
        
        importance_stds = np.array(importance_stds)
        std_dev = np.std(importance_stds, axis=0)
        
        results[n] = {
            'mean_importance': np.mean(importance_stds, axis=0).tolist(),
            'std_dev': std_dev.tolist(),
            'feature_names': feature_names
        }
        
        logger.debug(f"Sample size {n}: mean std_dev = {np.mean(std_dev):.4f}")

    return results

def run_fixed_sample_bootstrap(X: np.ndarray, y: np.ndarray, model: RandomForestRegressor,
                               feature_names: List[str], n_bootstraps: int = 10, 
                               random_state: int = 42) -> Dict[str, Any]:
    """
    T038 Implementation: Calculates standard deviation of feature importance across 
    10 bootstrapped samples of the FULL dataset.
    
    FR-008/SC-005: Calculate std_dev of feature importance across 10 bootstrapped samples.
    """
    logger.info(f"Running fixed-sample bootstrap with {n_bootstraps} iterations on full dataset (n={len(X)})")
    
    rng = np.random.RandomState(random_state)
    importances_list = []

    for i in range(n_bootstraps):
        # Resample with replacement
        indices = rng.choice(len(X), size=len(X), replace=True)
        X_boot, y_boot = X[indices], y[indices]
        
        # Train a fresh model on the bootstrap sample
        # We clone the original model's parameters to ensure consistency
        model_clone = RandomForestRegressor(
            n_estimators=model.n_estimators,
            max_depth=model.max_depth,
            min_samples_split=model.min_samples_split,
            min_samples_leaf=model.min_samples_leaf,
            max_features=model.max_features,
            random_state=CONFIG.SEED + i, # Different seed for each bootstrap to ensure variation in training if needed, though data variation is primary
            n_jobs=model.n_jobs
        )
        model_clone.fit(X_boot, y_boot)
        
        # Extract feature importances
        importances = model_clone.feature_importances_
        importances_list.append(importances)
        
        logger.debug(f"Bootstrap {i+1}/{n_bootstraps} completed. Sum of importances: {np.sum(importances):.4f}")

    importances_array = np.array(importances_list)
    
    # Calculate statistics
    mean_importance = np.mean(importances_array, axis=0)
    std_importance = np.std(importances_array, axis=0)
    
    results = {
        'n_bootstraps': n_bootstraps,
        'sample_size': len(X),
        'feature_names': feature_names,
        'mean_importance': mean_importance.tolist(),
        'std_importance': std_importance.tolist(),
        'raw_importances': importances_array.tolist() # Keep raw for debugging if needed
    }
    
    logger.info(f"Bootstrap complete. Mean std_dev across features: {np.mean(std_importance):.6f}")
    return results

def check_stability(std_importance: List[float], feature_names: List[str], 
                    threshold: float = 0.05, key_features: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Checks if the standard deviation of feature importance is below a threshold.
    T039 Logic: Check if std_dev of key DFT descriptors < 0.05.
    """
    if key_features is None:
        # If no specific features defined, check all or those with high mean importance
        # For T039, we assume the task implies checking the top features or all DFT features.
        # We'll check all features here and return per-feature status.
        pass

    stability_results = {}
    is_stable_overall = True

    for i, name in enumerate(feature_names):
        std_val = std_importance[i]
        is_stable = std_val < threshold
        
        stability_results[name] = {
            'std_dev': std_val,
            'is_stable': is_stable
        }
        
        if not is_stable:
            is_stable_overall = False
            logger.debug(f"Feature '{name}' is unstable (std={std_val:.4f} >= {threshold})")

    return {
        'is_stable': is_stable_overall,
        'threshold': threshold,
        'feature_stability': stability_results
    }

def save_results(bootstrap_results: Dict[str, Any], stability_results: Dict[str, Any], 
                 sample_sweep_results: Optional[Dict[str, Any]] = None, 
                 output_path: Optional[Path] = None):
    """
    Saves the bootstrap stability analysis results to the results directory.
    Updates the main output.json if necessary, or saves a dedicated file.
    """
    if output_path is None:
        output_path = Path(CONFIG.RESULTS_DIR) / "bootstrap_stability.json"
    
    ensure_dirs(output_path.parent)
    
    output_data = {
        'bootstrap_analysis': bootstrap_results,
        'stability_check': stability_results,
        'sample_size_sweep': sample_sweep_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Bootstrap stability results saved to {output_path}")
    
    # Also update the main output.json if it exists, merging the stability fields
    main_output_path = Path(CONFIG.RESULTS_DIR) / "output.json"
    if main_output_path.exists():
        try:
            with open(main_output_path, 'r') as f:
                main_data = json.load(f)
            
            # Merge stability info
            main_data['bootstrap_stability'] = {
                'is_stable': stability_results['is_stable'],
                'std_dev_key_features': stability_results['feature_stability'],
                'n_bootstraps': bootstrap_results['n_bootstraps']
            }
            
            with open(main_output_path, 'w') as f:
                json.dump(main_data, f, indent=2)
            logger.info(f"Updated {main_output_path} with stability results")
        except Exception as e:
            logger.warning(f"Could not update main output.json: {e}")

def main():
    """
    Main entry point for T038: Bootstrap Stability Analysis.
    """
    log_provenance_event('start', task='T038', component='bootstrap_stability')
    
    try:
        # 1. Load Data and Model
        df, X, y, model, feature_names = load_data_and_model()
        
        # 2. Run Fixed-Sample Bootstrap (T038)
        # Per spec: 10 bootstrapped samples of the full dataset
        bootstrap_results = run_fixed_sample_bootstrap(
            X, y, model, feature_names, n_bootstraps=10, random_state=CONFIG.SEED
        )
        
        # 3. Check Stability (T039 logic integrated here)
        # Spec: Check if std_dev of key DFT descriptors < 0.05
        # We check all features here; if specific DFT features are needed, they should be identified in config or passed in.
        # Assuming DFT features are those not in the composition set, but for safety we check all.
        stability_results = check_stability(
            bootstrap_results['std_importance'], 
            feature_names, 
            threshold=0.05
        )
        
        # 4. (Optional) Run Sample Size Sweep if requested (T037)
        # Since T037 is already marked complete, we assume that data might exist or we can run it here if needed.
        # For this task, we focus on T038. We can skip the sweep to save time or run it if dependencies allow.
        # Given the instruction "Implement T038", we focus on the bootstrap.
        sample_sweep_results = None 
        
        # 5. Save Results
        save_results(bootstrap_results, stability_results, sample_sweep_results)
        
        log_provenance_event('complete', task='T038', status='success')
        
    except Exception as e:
        logger.error(f"Bootstrap stability analysis failed: {e}", exc_info=True)
        log_provenance_event('error', task='T038', error=str(e))
        raise

if __name__ == '__main__':
    main()