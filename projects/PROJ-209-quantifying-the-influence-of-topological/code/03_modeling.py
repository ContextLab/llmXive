"""
code/03_modeling.py
Implements Random Forest modeling pipeline for 2D material properties.
Handles feature selection, model training, and cross-validation.
"""
import os
import json
import logging
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_validate
from sklearn.metrics import r2_score, mean_absolute_percentage_error
from sklearn.inspection import permutation_importance
from scipy.stats import variance_inflation_factor
from pathlib import Path

# Project root and logging setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    return PROJECT_ROOT

def get_git_hash() -> str:
    try:
        import subprocess
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def compute_sha256(filepath: Path) -> str:
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_output_directories():
    dirs = [
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "state",
        PROJECT_ROOT / "figures"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load features and targets from processed data."""
    features_path = PROJECT_ROOT / "data" / "processed" / "final_features.csv"
    targets_path = PROJECT_ROOT / "data" / "processed" / "targets.csv"
    
    if not features_path.exists() or not targets_path.exists():
        raise FileNotFoundError(f"Processed data not found. Run T020 first. Expected: {features_path}")
    
    X = pd.read_csv(features_path)
    y = pd.read_csv(targets_path)
    return X, y

def load_preliminary_model() -> RandomForestRegressor:
    """Load the preliminary model trained in T021a."""
    model_path = PROJECT_ROOT / "data" / "processed" / "preliminary_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Preliminary model not found. Run T021a first. Expected: {model_path}")
    
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def compute_vif(X: pd.DataFrame) -> Dict[str, float]:
    """Compute Variance Inflation Factor for all features."""
    vif_data = {}
    X_const = sm.add_constant(X)
    for i, col in enumerate(X.columns):
        try:
            vif = variance_inflation_factor(X_const.values, i+1) # +1 because of constant
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not compute VIF for {col}: {e}")
            vif_data[col] = float('inf')
    return vif_data

def compute_permutation_importance(model: RandomForestRegressor, X: pd.DataFrame, y: pd.DataFrame) -> Dict[str, float]:
    """Compute permutation importance for all features."""
    result = permutation_importance(model, X, y, n_repeats=10, random_state=42, scoring='r2')
    return dict(zip(X.columns, result.importances_mean))

def run_feature_selection_loop(X: pd.DataFrame, y: pd.DataFrame, model: RandomForestRegressor) -> Tuple[pd.DataFrame, Dict]:
    """Iteratively remove lowest importance features until VIF <= 5."""
    log = {"iterations": [], "final_vif": {}, "excluded_features": []}
    current_X = X.copy()
    
    max_iter = 10
    for i in range(max_iter):
        vif = compute_vif(current_X)
        max_vif = max(vif.values()) if vif else 0
        
        if max_vif <= 5:
            logger.info(f"VIF condition met after {i} iterations. Max VIF: {max_vif:.2f}")
            break
        
        logger.info(f"Iteration {i}: Max VIF = {max_vif:.2f}. Selecting features...")
        importances = compute_permutation_importance(model, current_X, y)
        min_feat = min(importances, key=importances.get)
        
        log["iterations"].append({
            "iteration": i,
            "max_vif": max_vif,
            "removed_feature": min_feat,
            "importance": importances[min_feat]
        })
        log["excluded_features"].append(min_feat)
        
        current_X = current_X.drop(columns=[min_feat])
        
        # Re-train model on reduced features for next iteration's importance calculation
        model.fit(current_X, y)
    
    log["final_vif"] = compute_vif(current_X)
    return current_X, log

def save_feature_selection_log(log: Dict):
    """Save feature selection log to JSON."""
    path = PROJECT_ROOT / "data" / "processed" / "feature_selection_log.json"
    with open(path, 'w') as f:
        json.dump(log, f, indent=2)
    logger.info(f"Feature selection log saved to {path}")

def load_confounding_config() -> Dict:
    """Load confounding configuration from T027a."""
    path = PROJECT_ROOT / "data" / "processed" / "confounding_config.json"
    if not path.exists():
        logger.warning("Confounding config not found. Proceeding without stratification/covariates.")
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def train_models(X: pd.DataFrame, y: pd.DataFrame) -> Dict[str, RandomForestRegressor]:
    """Train final Random Forest models for each target property."""
    models = {}
    for col in y.columns:
        logger.info(f"Training model for {col}...")
        rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        rf.fit(X, y[col])
        models[col] = rf
        logger.info(f"Model for {col} trained.")
    return models

def check_vif_after_training(X: pd.DataFrame):
    """Check VIF after training to ensure no collinearity issues were introduced."""
    vif = compute_vif(X)
    max_vif = max(vif.values()) if vif else 0
    if max_vif > 5:
        logger.warning(f"VIF > 5 after training (Max: {max_vif}). Consider re-running feature selection.")
        return False
    return True

def run_cross_validation(models: Dict[str, RandomForestRegressor], X: pd.DataFrame, y: pd.DataFrame) -> Dict[str, Dict]:
    """
    Perform 5-fold cross-validation on all models.
    Computes mean R², MAPE, and standard deviation of R².
    Flags HIGH_VARIANCE if cv_std > 0.1.
    """
    results = {}
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    for target_name, model in models.items():
        logger.info(f"Performing 5-fold CV for {target_name}...")
        y_target = y[target_name]
        
        # Use cross_validate for R²
        cv_results_r2 = cross_validate(model, X, y_target, cv=kf, scoring='r2', n_jobs=-1)
        r2_scores = cv_results_r2['test_score']
        
        # Manual MAPE calculation because sklearn's mean_absolute_percentage_error doesn't have CV wrapper
        mape_scores = []
        for train_idx, test_idx in kf.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y_target.iloc[train_idx], y_target.iloc[test_idx]
            y_pred = model.fit(X_train, y_train).predict(X_test)
            # Handle zero values in y_test to avoid division by zero
            mask = y_test != 0
            if mask.sum() > 0:
                mape = mean_absolute_percentage_error(y_test[mask], y_pred[mask])
            else:
                mape = 0.0
            mape_scores.append(mape)
        
        mean_r2 = np.mean(r2_scores)
        std_r2 = np.std(r2_scores)
        mean_mape = np.mean(mape_scores)
        
        variance_flag = "HIGH_VARIANCE" if std_r2 > 0.1 else "OK"
        
        results[target_name] = {
            "mean_r2": float(mean_r2),
            "std_r2": float(std_r2),
            "mean_mape": float(mean_mape),
            "variance_flag": variance_flag,
            "r2_scores": r2_scores.tolist(),
            "mape_scores": mape_scores
        }
        
        logger.info(f"CV Results for {target_name}: R²={mean_r2:.4f} (±{std_r2:.4f}), MAPE={mean_mape:.4f} [{variance_flag}]")
    
    return results

def save_cv_results(results: Dict):
    """Save cross-validation results to JSON."""
    path = PROJECT_ROOT / "data" / "processed" / "cv_results.json"
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"CV results saved to {path}")

def main():
    """Main entry point for T022: Cross-Validation Step."""
    logger.info("Starting T022: Cross-Validation Step")
    ensure_output_directories()
    
    try:
        # Load data
        X, y = load_processed_data()
        logger.info(f"Loaded data: {X.shape} features, {y.shape} targets")
        
        # Load models (trained in T021)
        # Note: T021 trains models. We assume they are saved or we re-train the final ones here if not saved.
        # The task description says "Perform k-fold cross-validation on the models trained in T021".
        # We need to ensure the models from T021 are available. 
        # If T021 saved them, we load. If not, we re-train the final models based on the final features.
        # Given the flow, T021 should have saved models. Let's try to load or re-train if missing.
        
        models_path = PROJECT_ROOT / "data" / "processed" / "final_models.pkl"
        if models_path.exists():
            with open(models_path, 'rb') as f:
                models = pickle.load(f)
            logger.info("Loaded final models from T021.")
        else:
            logger.warning("Final models not found. Re-training on final features for CV.")
            models = train_models(X, y)
            # Save for future steps
            with open(models_path, 'wb') as f:
                pickle.dump(models, f)
        
        # Run Cross-Validation
        cv_results = run_cross_validation(models, X, y)
        
        # Save results
        save_cv_results(cv_results)
        
        logger.info("T022 Cross-Validation completed successfully.")
        
    except Exception as e:
        logger.error(f"T022 failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()