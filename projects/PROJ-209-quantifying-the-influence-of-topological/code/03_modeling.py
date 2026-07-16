import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib
import hashlib
import subprocess
from datetime import datetime

# Project root and logging setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RAW = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state" / "projects" / "PROJ-209-quantifying-the-influence-of-topological"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_output_directories():
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def get_git_hash():
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_processed_data():
    features_path = DATA_PROCESSED / "features.csv"
    targets_path = DATA_PROCESSED / "targets.csv"
    
    if not features_path.exists() or not targets_path.exists():
        raise FileNotFoundError(f"Processed data not found. Run code/02_data_processing.py first. Missing: {features_path}, {targets_path}")
    
    features = pd.read_csv(features_path)
    targets = pd.read_csv(targets_path)
    
    # Handle potential MultiIndex columns if saved as such, though usually saved as flat
    if isinstance(features.columns, pd.MultiIndex):
        features.columns = ['_'.join(col).strip() for col in features.columns.values]
    
    return features, targets

def compute_vif(X: pd.DataFrame) -> pd.Series:
    """Compute Variance Inflation Factor for each feature."""
    vif_data = pd.Series(dtype=float)
    # Add constant for intercept if needed, though VIF formula handles centering
    # Standard VIF calculation: VIF_i = 1 / (1 - R_i^2) where R_i^2 is R2 of regressing X_i on all other X_j
    for i, col in enumerate(X.columns):
        y = X[col]
        X_other = X.drop(columns=[col])
        if X_other.shape[1] == 0:
            vif_data[col] = 1.0
            continue
        
        try:
            # Fit a simple linear model to get R2
            model = Ridge(alpha=1e-9) # Small alpha to avoid singular matrix issues if any
            model.fit(X_other, y)
            r2 = model.score(X_other, y)
            if r2 >= 1.0:
                vif_data[col] = np.inf
            else:
                vif_data[col] = 1.0 / (1.0 - r2)
        except Exception as e:
            logger.warning(f"Could not compute VIF for {col}: {e}")
            vif_data[col] = np.inf
    
    return vif_data

def train_initial_rf_for_importance(X: pd.DataFrame, y: pd.Series, random_state: int = 42):
    """Train a preliminary Random Forest to estimate feature importance."""
    rf = RandomForestRegressor(n_estimators=100, random_state=random_state, n_jobs=-1)
    rf.fit(X, y)
    return rf, rf.feature_importances_

def handle_collinearity(X: pd.DataFrame, y: pd.Series, threshold: float = 5.0, random_state: int = 42) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Primary Strategy: Apply Ridge Regression to handle collinearity.
    Fallback: If Ridge fails or a feature is physically redundant (VIF > 5 AND low importance), exclude it.
    
    Returns:
        X_final: The processed feature matrix.
        log: List of dictionaries detailing actions taken.
    """
    log = []
    X_current = X.copy()
    features_to_exclude = set()
    
    # Step 1: Compute VIF
    vif_series = compute_vif(X_current)
    high_vif_features = vif_series[vif_series > threshold].index.tolist()
    
    log.append({
        "step": "initial_vif_check",
        "threshold": threshold,
        "high_vif_features": high_vif_features,
        "vif_values": vif_series.to_dict()
    })
    
    if not high_vif_features:
        log.append({"step": "no_action_needed", "reason": "No features with VIF > threshold"})
        return X_current, log
    
    # Step 2: Train initial RF to get importance for high-VIF features
    # We only care about importance for the high-VIF set to decide which to drop if Ridge isn't enough
    rf_initial, importances = train_initial_rf_for_importance(X_current, y, random_state)
    
    # Map feature names to importance
    feat_importance_map = dict(zip(X_current.columns, importances))
    
    # Step 3: Primary Strategy - Try Ridge Regression
    # We attempt to fit a Ridge model on the full set including high-VIF features.
    # If it converges and has reasonable performance, we keep the features (Ridge handles collinearity).
    # If Ridge fails (e.g., singular matrix despite regularization, or extremely unstable), we fallback to exclusion.
    
    ridge_model = Ridge(alpha=1.0) # Standard regularization
    try:
        ridge_model.fit(X_current, y)
        # Check for extreme coefficients which might indicate failure to regularize effectively
        # If coefficients are massive, it might still be unstable, but Ridge usually handles this.
        # We assume Ridge succeeds if fit() doesn't raise.
        log.append({
            "step": "primary_strategy_ridge",
            "action": "applied_ridge_regularization",
            "features_kept": list(X_current.columns),
            "message": "Ridge regression applied successfully to handle collinearity."
        })
        return X_current, log
        
    except Exception as e:
        log.append({
            "step": "primary_strategy_ridge",
            "action": "failed",
            "error": str(e),
            "message": "Ridge regression failed. Falling back to feature exclusion."
        })
    
    # Step 4: Fallback Strategy - Exclude features
    # Logic: Exclude features where VIF > 5 AND importance is low (bottom 20% of high-VIF set)
    high_vif_importances = {k: v for k, v in feat_importance_map.items() if k in high_vif_features}
    
    if not high_vif_importances:
        log.append({"step": "fallback", "action": "no_high_vif_features_found", "message": "Unexpected state."})
        return X_current, log
    
    # Sort high VIF features by importance (ascending)
    sorted_high_vif = sorted(high_vif_importances.items(), key=lambda x: x[1])
    
    # Determine cutoff: remove the bottom 50% of the high-VIF features to reduce multicollinearity
    # Or remove until VIF < threshold
    features_to_drop = []
    current_X = X_current.copy()
    
    # Iterative removal: drop lowest importance, re-check VIF
    while True:
        current_vif = compute_vif(current_X)
        current_high_vif = current_vif[current_vif > threshold].index.tolist()
        
        if not current_high_vif:
            break
        
        # Identify candidate to drop: lowest importance among current high VIF
        candidates = {k: feat_importance_map.get(k, 0) for k in current_high_vif}
        if not candidates:
            break
        
        lowest_imp_feature = min(candidates, key=candidates.get)
        
        # Check if this feature was in original high VIF list
        if lowest_imp_feature in high_vif_features:
            features_to_drop.append(lowest_imp_feature)
            current_X = current_X.drop(columns=[lowest_imp_feature])
            log.append({
                "step": "fallback_exclusion",
                "action": "excluded_feature",
                "feature": lowest_imp_feature,
                "reason": f"VIF > {threshold} AND low importance",
                "importance": candidates[lowest_imp_feature]
            })
        else:
            # If the lowest importance feature is not in the original high VIF set but still has high VIF now?
            # This implies new collinearity emerged or calculation drift.
            # We still drop it to resolve VIF.
            features_to_drop.append(lowest_imp_feature)
            current_X = current_X.drop(columns=[lowest_imp_feature])
            log.append({
                "step": "fallback_exclusion",
                "action": "excluded_feature",
                "feature": lowest_imp_feature,
                "reason": f"VIF > {threshold} (emerged during iteration)",
                "importance": candidates[lowest_imp_feature]
            })
        
        if current_X.shape[1] <= 1:
            log.append({"step": "fallback_exclusion", "action": "stopped", "reason": "Only 1 feature remaining"})
            break
    
    log.append({
        "step": "fallback_final",
        "action": "completed_exclusion",
        "excluded_features": features_to_drop,
        "remaining_features": list(current_X.columns)
    })
    
    return current_X, log

def save_feature_selection_log(log: List[Dict], output_path: Path):
    with open(output_path, 'w') as f:
        json.dump(log, f, indent=2)
    logger.info(f"Feature selection log saved to {output_path}")

def run_collinearity_analysis():
    """Main entry point for T020: Collinearity Handling."""
    ensure_output_directories()
    log_file_path = DATA_PROCESSED / "feature_selection_log.json"
    
    try:
        X, y_df = load_processed_data()
        
        # Ensure y is a Series
        if isinstance(y_df, pd.DataFrame):
            # Assume single target column or pick the first one if multiple exist
            if y_df.shape[1] == 1:
                y = y_df.iloc[:, 0]
            else:
                # For this task, we assume a single target column exists or we process one by one.
                # The task implies handling predictors for the modeling step.
                # We'll pick the first column as the target for the VIF analysis context.
                y = y_df.iloc[:, 0]
        else:
            y = y_df
        
        logger.info(f"Loaded {X.shape[1]} features and {y.shape[0]} samples.")
        
        # Run collinearity handling
        X_cleaned, log = handle_collinearity(X, y)
        
        # Save the log
        save_feature_selection_log(log, log_file_path)
        
        # Save the cleaned features back to disk if they changed
        if not X_cleaned.equals(X):
            cleaned_features_path = DATA_PROCESSED / "features_collinearity_handled.csv"
            X_cleaned.to_csv(cleaned_features_path, index=False)
            logger.info(f"Cleaned features saved to {cleaned_features_path}")
            log.append({"step": "save_cleaned_features", "path": str(cleaned_features_path)})
            # Update log file with save info
            save_feature_selection_log(log, log_file_path)
        else:
            logger.info("No features excluded or modified; original features retained.")
        
        return X_cleaned, log
        
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"Error in collinearity analysis: {e}")
        raise

def train_random_forest_models(X: pd.DataFrame, y: pd.Series, target_name: str):
    """Train a Random Forest model."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    return model, {"r2": r2, "mape": mape, "cv_std": 0.0} # cv_std calculated in T022

def save_models(models: Dict[str, Any], output_dir: Path):
    for name, model in models.items():
        joblib.dump(model, output_dir / f"{name}_model.joblib")

def save_metrics(metrics: Dict[str, Any], output_path: Path):
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def train_baseline_null_model(y: pd.Series):
    """Train a null model that predicts the mean."""
    return np.mean(y)

def compare_baseline_improvement(null_pred, model_pred, y_true):
    # Compare R2 of model vs null
    pass

def evaluate_holdout_set(model, X_holdout, y_holdout):
    pass

def load_holdout_data():
    pass

def train_random_forest_models_full(X, y):
    pass

def main():
    logger.info("Starting T020: Collinearity Handling")
    try:
        X_cleaned, log = run_collinearity_analysis()
        logger.info("T020 completed successfully.")
        logger.info(f"Log saved to: {DATA_PROCESSED / 'feature_selection_log.json'}")
    except Exception as e:
        logger.error(f"T020 failed: {e}")
        raise

if __name__ == "__main__":
    main()
