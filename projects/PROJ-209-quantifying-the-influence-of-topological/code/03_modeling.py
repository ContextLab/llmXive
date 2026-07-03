"""
Modeling Module
- Train Random Forest models
- Cross-validation
- Baseline comparison
- Hold-out evaluation
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

from infrastructure.path_utils import (
    DIR_DATA_PROCESSED,
    FILE_FEATURES,
    FILE_TARGETS,
    FILE_MODELS_DIR,
    FILE_METRICS,
    ensure_dir
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_output_directories():
    """Ensure output directories exist."""
    ensure_dir(DIR_DATA_PROCESSED)
    ensure_dir(FILE_MODELS_DIR)
    return True

def get_git_hash() -> str:
    """Get git hash for versioning."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return "no-git"

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load processed features and targets."""
    try:
        features = pd.read_csv(FILE_FEATURES)
        targets = pd.read_csv(FILE_TARGETS)
        return features, targets
    except FileNotFoundError as e:
        logger.error(f"Processed data not found: {e}")
        return pd.DataFrame(), pd.DataFrame()

def compute_vif(X: pd.DataFrame) -> Dict[str, float]:
    """Compute VIF for features."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return {}
    
    X_values = X[numeric_cols].values
    vif_data = {}
    
    for i, col in enumerate(numeric_cols):
        try:
            vif = variance_inflation_factor(X_values, i)
            vif_data[col] = vif
        except Exception:
            vif_data[col] = float('inf')
    
    return vif_data

def train_initial_rf_for_importance(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Train initial RF to get feature importances."""
    from sklearn.ensemble import RandomForestRegressor
    
    rf = RandomForestRegressor(n_estimators=10, random_state=42)
    rf.fit(X, y)
    return rf.feature_importances_

def handle_collinearity(X: pd.DataFrame, y: np.ndarray, vif_threshold: float = 5.0) -> Tuple[pd.DataFrame, List[str]]:
    """Handle collinearity by excluding high-VIF features."""
    excluded_features = []
    X_clean = X.copy()
    
    vif_data = compute_vif(X_clean)
    high_vif = [col for col, vif in vif_data.items() if vif > vif_threshold]
    
    if high_vif:
        # Get feature importances to decide which to exclude
        X_values = X_clean.select_dtypes(include=[np.number]).values
        if X_values.shape[1] > 0:
            importances = train_initial_rf_for_importance(X_values, y)
            feature_cols = X_clean.select_dtypes(include=[np.number]).columns
            
            # Sort high VIF features by importance (ascending)
            high_vif_with_importance = [
                (col, importances[feature_cols.get_loc(col)]) 
                for col in high_vif if col in feature_cols
            ]
            high_vif_with_importance.sort(key=lambda x: x[1])
            
            # Exclude the least important high-VIF feature
            if high_vif_with_importance:
                to_exclude = high_vif_with_importance[0][0]
                excluded_features.append(to_exclude)
                X_clean = X_clean.drop(columns=[to_exclude])
                logger.info(f"Excluded {to_exclude} (VIF={vif_data[to_exclude]:.2f}) due to collinearity.")
    
    return X_clean, excluded_features

def save_feature_selection_log(excluded_features: List[str], method: str):
    """Save feature selection log."""
    log_path = DIR_DATA_PROCESSED / "feature_selection_log.json"
    log_entry = {
        "git_hash": get_git_hash(),
        "method": method,
        "excluded_features": excluded_features,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    with open(log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)

def run_collinearity_analysis(X: pd.DataFrame, y: np.ndarray):
    """Run collinearity analysis and handle it."""
    X_clean, excluded = handle_collinearity(X, y)
    if excluded:
        save_feature_selection_log(excluded, "vif_ridge")
    return X_clean

def train_random_forest_models(X: np.ndarray, y: np.ndarray, target_name: str) -> Any:
    """Train a Random Forest model for a specific target."""
    from sklearn.ensemble import RandomForestRegressor
    
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X, y)
    return rf

def save_models(models: Dict[str, Any]):
    """Save trained models to disk."""
    import joblib
    for name, model in models.items():
        path = FILE_MODELS_DIR / f"{name}.pkl"
        joblib.dump(model, path)
        logger.info(f"Saved model: {path}")

def save_metrics(metrics: Dict[str, Any]):
    """Save metrics to JSON."""
    metrics_path = FILE_METRICS
    metrics["git_hash"] = get_git_hash()
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {metrics_path}")

def train_baseline_null_model(y: np.ndarray) -> float:
    """Train a null model (predict mean) and return R²."""
    from sklearn.dummy import DummyRegressor
    
    dummy = DummyRegressor(strategy='mean')
    dummy.fit(np.zeros((len(y), 1)), y)
    r2 = dummy.score(np.zeros((len(y), 1)), y)
    return r2

def compare_baseline_improvement(rf_r2: float, null_r2: float, target_name: str):
    """Compare RF performance against null model."""
    improvement = rf_r2 - null_r2
    logger.info(f"{target_name}: RF R²={rf_r2:.4f}, Null R²={null_r2:.4f}, Improvement={improvement:.4f}")

def evaluate_holdout_set(model: Any, X_holdout: np.ndarray, y_holdout: np.ndarray, target_name: str) -> Dict[str, float]:
    """Evaluate model on hold-out set."""
    r2 = model.score(X_holdout, y_holdout)
    y_pred = model.predict(X_holdout)
    mape = np.mean(np.abs((y_holdout - y_pred) / (y_holdout + 1e-8)))
    
    return {"r2": r2, "mape": mape}

def load_holdout_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load hold-out data if available."""
    holdout_path = DIR_DATA_PROCESSED / "holdout_features.csv"
    if holdout_path.exists():
        return pd.read_csv(holdout_path), pd.read_csv(DIR_DATA_PROCESSED / "holdout_targets.csv")
    return pd.DataFrame(), pd.DataFrame()

def train_random_forest_models_full():
    """Main training pipeline."""
    ensure_output_directories()
    
    features, targets = load_processed_data()
    if features.empty or targets.empty:
        logger.error("No data to train on.")
        return False
    
    # Prepare data
    X = features.select_dtypes(include=[np.number]).values
    y_conductivity = targets["conductivity_normalized"].values if "conductivity_normalized" in targets.columns else None
    y_youngs = targets["youngs_modulus_normalized"].values if "youngs_modulus_normalized" in targets.columns else None
    y_fracture = targets["fracture_energy_normalized"].values if "fracture_energy_normalized" in targets.columns else None
    
    models = {}
    metrics = {}
    
    # Handle collinearity
    X_clean = run_collinearity_analysis(features, X[:, 0])
    X_clean_values = X_clean.select_dtypes(include=[np.number]).values
    
    # Train models
    targets_to_train = [
        ("conductivity", y_conductivity),
        ("youngs_modulus", y_youngs),
        ("fracture_energy", y_fracture)
    ]
    
    for name, y in targets_to_train:
        if y is None:
            continue
        
        # Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X_clean_values, y, test_size=0.2, random_state=42
        )
        
        # Train model
        model = train_random_forest_models(X_train, y_train, name)
        models[name] = model
        
        # Evaluate
        r2 = model.score(X_test, y_test)
        y_pred = model.predict(X_test)
        mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-8)))
        
        # Cross-validation
        from sklearn.model_selection import cross_val_score
        cv_scores = cross_val_score(model, X_clean_values, y, cv=5)
        cv_std = np.std(cv_scores)
        
        # Null model
        null_r2 = train_baseline_null_model(y)
        compare_baseline_improvement(r2, null_r2, name)
        
        metrics[name] = {
            "r2": r2,
            "mape": mape,
            "cv_mean": np.mean(cv_scores),
            "cv_std": cv_std,
            "null_r2": null_r2
        }
        
        if cv_std > 0.1:
            logger.warning(f"High variance in {name} model (cv_std={cv_std:.4f}). Trigger sensitivity analysis.")
    
    # Save models and metrics
    save_models(models)
    save_metrics(metrics)
    
    logger.info("Model training completed.")
    return True

def main():
    """Entry point."""
    success = train_random_forest_models_full()
    if success:
        logger.info("Modeling completed successfully.")
    else:
        logger.error("Modeling failed.")
        exit(1)

if __name__ == "__main__":
    main()
