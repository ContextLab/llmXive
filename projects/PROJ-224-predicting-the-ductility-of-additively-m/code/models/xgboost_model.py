"""
XGBoost model implementation for the ductility prediction pipeline.
"""
import os
import sys
import logging
import json
import time
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def load_split_data() -> tuple:
    """Load train, val, test splits."""
    train_path = DATA_DIR / "splits" / "train.csv"
    val_path = DATA_DIR / "splits" / "val.csv"
    test_path = DATA_DIR / "splits" / "test.csv"
    
    if not all(p.exists() for p in [train_path, val_path, test_path]):
        logger.error("Split files not found")
        sys.exit(1)
    
    return pd.read_csv(train_path), pd.read_csv(val_path), pd.read_csv(test_path)

def prepare_features(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
    """Prepare features and targets."""
    target_col = 'ductility'
    feature_cols = [col for col in train_df.columns if col != target_col and col != 'alloy_family']
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_val = val_df[feature_cols]
    y_val = val_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]
    
    return X_train, y_train, X_val, y_val, X_test, y_test, feature_cols

def tune_and_train(X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series, feature_cols: list) -> tuple:
    """Tune hyperparameters and train XGBoost model."""
    logger.info("Tuning and training XGBoost model")
    
    try:
        import xgboost as xgb
    except ImportError:
        logger.error("xgboost not installed. Please run: pip install xgboost")
        sys.exit(1)
    
    # Parameter grid
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1],
        'n_estimators': [50, 100]
    }
    
    # Use grid search with validation set
    best_score = -np.inf
    best_params = None
    best_model = None
    
    for max_depth in param_grid['max_depth']:
        for learning_rate in param_grid['learning_rate']:
            for n_estimators in param_grid['n_estimators']:
                model = xgb.XGBRegressor(
                    max_depth=max_depth,
                    learning_rate=learning_rate,
                    n_estimators=n_estimators,
                    tree_method='hist',
                    random_state=42,
                    verbosity=0
                )
                model.fit(X_train, y_train)
                val_pred = model.predict(X_val)
                score = r2_score(y_val, val_pred)
                
                if score > best_score:
                    best_score = score
                    best_params = {
                        'max_depth': max_depth,
                        'learning_rate': learning_rate,
                        'n_estimators': n_estimators
                    }
                    best_model = model
    
    logger.info(f"Best validation R²: {best_score:.4f} with params: {best_params}")
    return best_model, best_params

def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """Evaluate model on test set."""
    logger.info("Evaluating model on test set")
    
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    metrics = {
        'r2': r2,
        'mae': mae,
        'rmse': rmse,
        'n_test_samples': len(y_test)
    }
    
    logger.info(f"Test R²: {r2:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    
    if r2 < 0.60:
        logger.warning(f"Test R² ({r2:.4f}) < 0.60. Model performance may be limited.")
    
    return metrics

def compute_permutation_importance(model, X_test: pd.DataFrame, y_test: pd.Series, feature_cols: list) -> dict:
    """Compute permutation feature importance."""
    logger.info("Computing permutation feature importance")
    
    try:
        from sklearn.inspection import permutation_importance
    except ImportError:
        logger.error("scikit-learn not installed properly")
        return {}
    
    result = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42)
    
    importance = {}
    for i, col in enumerate(feature_cols):
        importance[col] = float(result.importances_mean[i])
    
    return importance

def load_lme_artifact() -> dict:
    """Load LME results for comparison."""
    lme_path = ARTIFACTS_DIR / "lme_model_results.json"
    if not lme_path.exists():
        logger.warning(f"LME results not found: {lme_path}")
        return {}
    with open(lme_path, 'r') as f:
        return json.load(f)

def compare_with_lme(xgb_importance: dict, lme_results: dict) -> dict:
    """Compare XGBoost importance with LME coefficients."""
    logger.info("Comparing with LME results")
    
    if not lme_results:
        return {"spearman_correlation": None, "top3_differences": [], "sign_observations": []}
    
    # Get significant LME coefficients (p < 0.05)
    significant_features = []
    lme_coefs = {}
    for i, col in enumerate(lme_results.get('fixed_effects', [])):
        if i < len(lme_results.get('p_values', [])) and lme_results['p_values'][i] < 0.05:
            significant_features.append(col)
            lme_coefs[col] = lme_results['standardized_coefficients'].get(col, 0)
    
    # Find common features
    common_features = [f for f in significant_features if f in xgb_importance]
    
    if len(common_features) < 2:
        return {"spearman_correlation": None, "top3_differences": [], "sign_observations": []}
    
    # Compute Spearman correlation
    from scipy.stats import spearmanr
    xgb_vals = [xgb_importance[f] for f in common_features]
    lme_vals = [abs(lme_coefs[f]) for f in common_features]
    
    corr, p_val = spearmanr(xgb_vals, lme_vals)
    
    # Top 3 differences
    xgb_ranked = sorted(xgb_importance.items(), key=lambda x: x[1], reverse=True)[:3]
    lme_ranked = sorted(lme_coefs.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
    
    top3_differences = []
    for i, (xgb_feat, _) in enumerate(xgb_ranked):
        if i < len(lme_ranked) and xgb_feat != lme_ranked[i][0]:
            top3_differences.append({
                "feature": xgb_feat,
                "xgb_rank": i+1,
                "lme_rank": next((j+1 for j, (f, _) in enumerate(lme_ranked) if f == xgb_feat), "N/A")
            })
    
    # Sign observations
    sign_observations = []
    for feat in common_features:
        xgb_sign = np.sign(xgb_importance[feat])
        lme_sign = np.sign(lme_coefs[feat])
        if xgb_sign != lme_sign:
            sign_observations.append(f"Sign mismatch for {feat}: XGB={xgb_sign}, LME={lme_sign}")
    
    return {
        "spearman_correlation": float(corr),
        "p_value": float(p_val),
        "top3_differences": top3_differences,
        "sign_observations": sign_observations
    }

def save_artifacts(model, metrics: dict, importance: dict, comparison: dict, params: dict):
    """Save all model artifacts."""
    # Save model
    model_path = ARTIFACTS_DIR / "xgboost_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Saved model to {model_path}")
    
    # Save metrics
    metrics_path = ARTIFACTS_DIR / "xgboost_metrics.json"
    metrics.update({"hyperparameters": params})
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {metrics_path}")
    
    # Save comparison
    comparison_path = ARTIFACTS_DIR / "model_comparison.json"
    with open(comparison_path, 'w') as f:
        json.dump(comparison, f, indent=2)
    logger.info(f"Saved comparison to {comparison_path}")

def main():
    """Main entry point for XGBoost model."""
    logger.info("Starting XGBoost model training")
    
    # Load data
    train_df, val_df, test_df = load_split_data()
    
    # Prepare features
    X_train, y_train, X_val, y_val, X_test, y_test, feature_cols = prepare_features(train_df, val_df, test_df)
    
    # Tune and train
    model, params = tune_and_train(X_train, y_train, X_val, y_val, feature_cols)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)
    
    # Compute importance
    importance = compute_permutation_importance(model, X_test, y_test, feature_cols)
    
    # Compare with LME
    lme_results = load_lme_artifact()
    comparison = compare_with_lme(importance, lme_results)
    
    # Save artifacts
    save_artifacts(model, metrics, importance, comparison, params)
    
    return metrics

if __name__ == "__main__":
    main()
