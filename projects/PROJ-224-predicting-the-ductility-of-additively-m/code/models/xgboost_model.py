import os
import sys
import logging
import json
import time
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from typing import Dict, Any, Tuple, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
ARTIFACTS_DIR = Path("artifacts")
CURATED_DATA_PATH = DATA_DIR / "curated_builds.csv"
SPLIT_DATA_PATH = DATA_DIR / "split_data"
LME_ARTIFACT_PATH = ARTIFACTS_DIR / "lme_results.json"
XGB_MODEL_PATH = ARTIFACTS_DIR / "xgboost_model.pkl"
XGB_IMPORTANCE_PATH = ARTIFACTS_DIR / "xgboost_importance.json"
PREDICTIVE_ARTIFACT_PATH = ARTIFACTS_DIR / "predictive_model_artifact.json"

# Ensure directories exist
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
SPLIT_DATA_PATH.mkdir(parents=True, exist_ok=True)

def load_split_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load the train, validation, and test datasets from the split artifacts.
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    train_path = SPLIT_DATA_PATH / "train.csv"
    val_path = SPLIT_DATA_PATH / "val.csv"
    test_path = SPLIT_DATA_PATH / "test.csv"

    if not train_path.exists() or not val_path.exists() or not test_path.exists():
        logger.error("Split data artifacts not found. Run preprocessing.py first.")
        raise FileNotFoundError("Split data artifacts missing.")

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    logger.info(f"Loaded split data: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    return train_df, val_df, test_df

def prepare_features(df: pd.DataFrame, target_col: str = "ductility") -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare features and target from a dataframe.
    Returns:
        Tuple of (X, y, feature_names)
    """
    # Exclude target and non-feature columns if any (like 'alloy_family' if not encoded)
    # Assuming the split data has only numeric features and the target
    feature_cols = [col for col in df.columns if col != target_col]
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y, feature_cols

def tune_and_train(X_train: np.ndarray, y_train: np.ndarray, 
                   X_val: np.ndarray, y_val: np.ndarray,
                   time_budget: int = 600) -> XGBRegressor:
    """
    Perform hyperparameter tuning and train the XGBoost model.
    Uses a simple grid search within the time budget.
    """
    logger.info("Starting XGBoost hyperparameter tuning and training...")
    start_time = time.time()

    # Define a simple grid for tuning (can be expanded)
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1],
        'n_estimators': [100, 200]
    }

    best_model = None
    best_score = -np.inf
    best_params = None

    # Simple grid search (for demonstration, could use Optuna/Scikit-Optimize)
    # In a real scenario, use cross-validation
    for depth in param_grid['max_depth']:
        for lr in param_grid['learning_rate']:
            for n_est in param_grid['n_estimators']:
                if time.time() - start_time > time_budget:
                    logger.warning("Time budget exceeded during tuning.")
                    break

                model = XGBRegressor(
                    max_depth=depth,
                    learning_rate=lr,
                    n_estimators=n_est,
                    tree_method="hist",
                    random_state=42,
                    n_jobs=-1
                )
                model.fit(X_train, y_train)
                
                # Evaluate on validation set
                val_pred = model.predict(X_val)
                # Simple R2 calculation
                ss_res = np.sum((y_val - val_pred) ** 2)
                ss_tot = np.sum((y_val - np.mean(y_val)) ** 2)
                r2 = 1 - (ss_res / ss_tot)

                if r2 > best_score:
                    best_score = r2
                    best_model = model
                    best_params = {'max_depth': depth, 'learning_rate': lr, 'n_estimators': n_est}

            if time.time() - start_time > time_budget:
                break
        if time.time() - start_time > time_budget:
            break

    if best_model is None:
        # Fallback to default if tuning fails or times out immediately
        logger.warning("No model selected during tuning. Using default parameters.")
        best_model = XGBRegressor(tree_method="hist", random_state=42, n_jobs=-1)
        best_model.fit(X_train, y_train)
        best_params = {'max_depth': 3, 'learning_rate': 0.1, 'n_estimators': 100}

    logger.info(f"Best parameters: {best_params}, Best Val R2: {best_score:.4f}")
    return best_model

def evaluate_model(model: XGBRegressor, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """
    Evaluate the model on the test set.
    Returns:
        Dictionary with R2, MAE, RMSE
    """
    y_pred = model.predict(X_test)
    
    # R2
    ss_res = np.sum((y_test - y_pred) ** 2)
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    r2 = 1 - (ss_res / ss_tot)

    # MAE
    mae = np.mean(np.abs(y_test - y_pred))

    # RMSE
    rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))

    logger.info(f"Test R2: {r2:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    return {"r2": r2, "mae": mae, "rmse": rmse}

def compute_permutation_importance(model: XGBRegressor, X_test: np.ndarray, 
                                   y_test: np.ndarray, feature_names: List[str], 
                                   n_repeats: int = 10, random_state: int = 42) -> Dict[str, float]:
    """
    Compute permutation feature importance.
    Returns:
        Dictionary mapping feature names to their importance scores (mean decrease in R2)
    """
    logger.info("Computing permutation feature importance...")
    result = permutation_importance(
        model, X_test, y_test, 
        n_repeats=n_repeats, 
        random_state=random_state, 
        n_jobs=-1, 
        scoring='r2'
    )
    
    importance_dict = {}
    for i, name in enumerate(feature_names):
        importance_dict[name] = float(result.importances_mean[i])
    
    # Sort by importance
    sorted_importance = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
    logger.info(f"Top 3 features by permutation importance: {list(sorted_importance.keys())[:3]}")
    return sorted_importance

def load_lme_artifact() -> Optional[Dict[str, Any]]:
    """
    Load the LME results artifact.
    Returns:
        Dictionary of LME results or None if not found
    """
    if not LME_ARTIFACT_PATH.exists():
        logger.warning(f"LME artifact not found at {LME_ARTIFACT_PATH}. Skipping comparison.")
        return None
    
    with open(LME_ARTIFACT_PATH, 'r') as f:
        return json.load(f)

def compare_with_lme(xgb_importance: Dict[str, float], lme_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare XGBoost feature importance with LME coefficients.
    Returns:
        Dictionary with comparison results
    """
    comparison = {
        "xgb_top_3": list(xgb_importance.keys())[:3],
        "lme_top_3": [],
        "shared_features": [],
        "disjoint_warning": False
    }

    # Extract LME coefficients (assuming structure from T024/T027)
    # LME results should contain fixed effects coefficients
    lme_fixed_effects = lme_results.get("fixed_effects", {})
    
    # Sort LME coefficients by absolute value
    lme_sorted = sorted(lme_fixed_effects.items(), key=lambda x: abs(x[1]), reverse=True)
    comparison["lme_top_3"] = [item[0] for item in lme_sorted[:3]]

    # Find intersection
    xgb_features = set(xgb_importance.keys())
    lme_features = set(lme_fixed_effects.keys())
    intersection = xgb_features.intersection(lme_features)
    
    comparison["shared_features"] = list(intersection)

    if not intersection:
        comparison["disjoint_warning"] = True
        logger.warning("No shared features between XGBoost and LME models. Comparison limited.")
    
    return comparison

def save_artifacts(model: XGBRegressor, metrics: Dict[str, float], 
                   importance: Dict[str, float], comparison: Dict[str, Any]) -> None:
    """
    Save the model, metrics, importance, and comparison results.
    """
    # Save model
    with open(XGB_MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {XGB_MODEL_PATH}")

    # Save importance
    with open(XGB_IMPORTANCE_PATH, 'w') as f:
        json.dump(importance, f, indent=2)
    logger.info(f"Feature importance saved to {XGB_IMPORTANCE_PATH}")

    # Save predictive artifact (combining metrics and comparison)
    predictive_artifact = {
        "metrics": metrics,
        "feature_importance": importance,
        "lme_comparison": comparison,
        "model_type": "XGBRegressor",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(PREDICTIVE_ARTIFACT_PATH, 'w') as f:
        json.dump(predictive_artifact, f, indent=2)
    logger.info(f"Predictive model artifact saved to {PREDICTIVE_ARTIFACT_PATH}")

def main():
    """
    Main execution function for T033.
    """
    try:
        # 1. Load split data
        train_df, val_df, test_df = load_split_data()
        
        # 2. Prepare features
        X_train, y_train, train_features = prepare_features(train_df)
        X_val, y_val, _ = prepare_features(val_df)
        X_test, y_test, test_features = prepare_features(test_df)
        
        # Ensure feature names are consistent (use train features as reference)
        feature_names = train_features

        # 3. Tune and train model
        model = tune_and_train(X_train, y_train, X_val, y_val)

        # 4. Evaluate model
        metrics = evaluate_model(model, X_test, y_test)

        # 5. Compute permutation importance
        importance = compute_permutation_importance(model, X_test, y_test, feature_names)

        # 6. Load LME artifact and compare
        lme_results = load_lme_artifact()
        comparison = {"xgb_top_3": [], "lme_top_3": [], "shared_features": [], "disjoint_warning": False}
        if lme_results:
            comparison = compare_with_lme(importance, lme_results)

        # 7. Save all artifacts
        save_artifacts(model, metrics, importance, comparison)

        logger.info("T033 Feature Importance implementation completed successfully.")

    except Exception as e:
        logger.error(f"Error during T033 execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()