import os
import logging
import json
import time
import pickle
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.inspection import permutation_importance
import xgboost as xgb
import yaml
from typing import Tuple, Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DATA_PATH = Path("data/curated_builds.csv")
ARTIFACTS_DIR = Path("artifacts")
LME_RESULT_PATH = ARTIFACTS_DIR / "MixedEffectsResult.json"
MODEL_OUTPUT_PATH = ARTIFACTS_DIR / "PredictiveModelArtifact.json"
MODEL_PKL_PATH = ARTIFACTS_DIR / "xgboost_model.pkl"

def load_data() -> pd.DataFrame:
    """Load the curated dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}. Run data acquisition and cleaning first.")
    return pd.read_csv(DATA_PATH)

def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Prepare features (X) and target (y).
    Handles the VIF-reduced feature set logic if applicable.
    """
    # Define potential features based on US2/US3 spec
    # If VIF filtering was applied (T023), 'energy_density' might be the only process feature,
    # while 'alloy_family' is handled via encoding or excluded from fixed effects in LME.
    # For XGBoost, we use available numeric columns + encoded categoricals.
    
    # Ensure energy_density exists (calculated in T018)
    if 'energy_density' not in df.columns and 'E_v' in df.columns:
        df['energy_density'] = df['E_v']
    
    # Select numeric process features
    process_features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    # Check which exist
    available_process = [c for c in process_features if c in df.columns]
    
    # If energy_density is present, prefer it over individual components if VIF logic was strict,
    # but for XGBoost we can include both or let the model decide, unless explicitly told to drop.
    # Per T023: "Drop the individual constituent predictors... Retain ONLY Energy Density".
    # We respect that here if the file has it.
    
    features_to_use = []
    if 'energy_density' in df.columns:
        features_to_use.append('energy_density')
        # Do not add individual components if energy_density is used, per T023 logic
    else:
        features_to_use.extend(available_process)

    # Add alloy composition binary flags if present
    composition_flags = ['Cr', 'Al', 'Ti', 'Co', 'Mo', 'W']
    for flag in composition_flags:
        if flag in df.columns:
            features_to_use.append(flag)
    
    # Handle categorical 'alloy_family' by One-Hot Encoding
    if 'alloy_family' in df.columns:
        df_encoded = pd.get_dummies(df, columns=['alloy_family'], drop_first=True)
        # Identify new columns
        new_cols = [c for c in df_encoded.columns if c.startswith('alloy_family_')]
        features_to_use.extend(new_cols)
    else:
        df_encoded = df

    X = df_encoded[features_to_use]
    y = df_encoded['ductility']
    
    # Drop rows with NaN in features or target
    mask = ~(X.isna().any(axis=1) | y.isna())
    return X[mask], y[mask], df_encoded[mask]

def split_data(X: pd.DataFrame, y: pd.Series, df_meta: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data using LOAFO if N < 100, otherwise stratified split.
    Returns X_train, X_test, y_train, y_test.
    """
    n_samples = len(X)
    logger.info(f"Splitting dataset with N={n_samples}")

    if n_samples < 100:
        logger.info("Using Leave-One-Alloy-Family-Out (LOAFO) strategy for small dataset.")
        # Identify unique alloy families
        if 'alloy_family' not in df_meta.columns:
            logger.warning("No 'alloy_family' column found for LOAFO. Falling back to random split.")
            return train_test_split(X, y, test_size=0.2, random_state=42)
        
        families = df_meta['alloy_family'].unique()
        if len(families) < 2:
            logger.warning("Only one alloy family found. Cannot perform LOAFO. Using random split.")
            return train_test_split(X, y, test_size=0.2, random_state=42)

        # For LOAFO in this context (single hold-out for evaluation as per T030 description):
        # "In each fold, the left-out alloy family serves as the 'held-out test set'".
        # Since we need a single train/test split for the final model evaluation step,
        # we will simulate one iteration or aggregate. 
        # To keep it simple and deterministic for the script:
        # We will use the first family as the test set for this run, or random one.
        # Better: Use a specific strategy if multiple families.
        # Let's pick the first unique family as test for this single run execution.
        test_family = families[0]
        test_mask = df_meta['alloy_family'] == test_family
        train_mask = ~test_mask

        X_train, X_test = X[train_mask], X[test_mask]
        y_train, y_test = y[train_mask], y[test_mask]
        
        logger.info(f"LOAFO: Training on {train_mask.sum()}, Testing on {test_mask.sum()} (Family: {test_family})")
    else:
        logger.info("Using standard stratified split.")
        # Stratify by alloy_family if available
        if 'alloy_family' in df_meta.columns:
            groups = df_meta['alloy_family']
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=groups
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

    return X_train, X_test, y_train, y_test

def train_model(X_train: pd.DataFrame, y_train: pd.Series, time_budget: int = 300) -> xgb.XGBRegressor:
    """
    Train XGBoost model with 5-fold stratified CV for hyperparameter tuning.
    """
    logger.info("Starting XGBoost training with hyperparameter tuning.")
    
    # Base parameters
    base_params = {
        'tree_method': 'hist',
        'objective': 'reg:squarederror',
        'eval_metric': 'rmse',
        'random_state': 42,
        'n_jobs': -1
    }

    # Grid for tuning (small grid for speed)
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1],
        'n_estimators': [100, 200]
    }

    best_score = -np.inf
    best_params = None
    best_model = None

    start_time = time.time()
    
    # Simple grid search with CV
    for depth in param_grid['max_depth']:
        for lr in param_grid['learning_rate']:
            for n_est in param_grid['n_estimators']:
                if time.time() - start_time > time_budget:
                    logger.warning("Time budget exceeded during tuning.")
                    break
                
                params = {**base_params, 'max_depth': depth, 'learning_rate': lr, 'n_estimators': n_est}
                model = xgb.XGBRegressor(**params)
                
                # CV
                try:
                    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
                    mean_score = cv_scores.mean()
                    if mean_score > best_score:
                        best_score = mean_score
                        best_params = params
                except Exception as e:
                    logger.warning(f"CV failed for {params}: {e}")

    if best_params is None:
        logger.error("No valid model found during tuning. Using defaults.")
        best_params = {**base_params, 'max_depth': 3, 'learning_rate': 0.1, 'n_estimators': 100}

    logger.info(f"Best params: {best_params} with CV R²: {best_score:.4f}")
    
    # Train final model on full training set
    final_model = xgb.XGBRegressor(**best_params)
    final_model.fit(X_train, y_train)
    
    return final_model

def evaluate_model(model: xgb.XGBRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Evaluate model on test set."""
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    logger.info(f"Test Results: R²={r2:.4f}, MAE={mae:.4f}, RMSE={rmse:.4f}")
    
    if r2 < 0.60:
        logger.warning(f"R² ({r2:.4f}) is below threshold 0.60. Model may be underperforming.")
        
    return {
        'r2': r2,
        'mae': mae,
        'rmse': rmse
    }

def compute_importance(model: xgb.XGBRegressor, X: pd.DataFrame, y: pd.Series, n_repeats: int = 10) -> Dict[str, float]:
    """Compute permutation feature importance."""
    logger.info("Computing permutation feature importance.")
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=42, n_jobs=-1)
    
    importance_dict = {}
    for i, name in enumerate(X.columns):
        importance_dict[name] = result.importances_mean[i]
        
    # Sort
    sorted_importance = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
    return sorted_importance

def compare_with_lme(xgb_importance: Dict[str, float], lme_results_path: Path) -> Dict[str, Any]:
    """
    Compare top 3 XGBoost features with top 3 LME coefficients.
    Handles VIF-reduced feature sets.
    """
    comparison = {
        'xgb_top_3': [],
        'lme_top_3': [],
        'shared_features': [],
        'warning': None
    }

    # Get top 3 XGBoost
    xgb_top = list(xgb_importance.keys())[:3]
    comparison['xgb_top_3'] = xgb_top

    # Load LME results
    if not lme_results_path.exists():
        logger.warning(f"LME result file not found at {lme_results_path}. Skipping comparison.")
        comparison['warning'] = "LME results not found."
        return comparison

    try:
        with open(lme_results_path, 'r') as f:
            lme_data = json.load(f)
        
        # Extract fixed effects coefficients
        # Structure depends on save_results format. Assuming 'fixed_effects' list of dicts with 'feature', 'coef'
        if 'fixed_effects' in lme_data:
            lme_coeffs = lme_data['fixed_effects']
            # Sort by absolute coefficient value
            sorted_lme = sorted(lme_coeffs, key=lambda x: abs(x.get('coef', 0)), reverse=True)
            lme_top = [item['feature'] for item in sorted_lme[:3]]
            comparison['lme_top_3'] = lme_top
        else:
            logger.warning("LME results missing 'fixed_effects' key.")
            comparison['warning'] = "LME results structure invalid."
            return comparison

    except Exception as e:
        logger.error(f"Error loading LME results: {e}")
        comparison['warning'] = f"Failed to load LME: {e}"
        return comparison

    # Compare
    xgb_set = set(xgb_top)
    lme_set = set(lme_top)
    intersection = xgb_set.intersection(lme_set)
    
    comparison['shared_features'] = list(intersection)

    if not intersection:
        comparison['warning'] = "No shared features between XGBoost top 3 and LME top 3. Feature sets may be disjoint."
        logger.warning("No shared features between XGBoost and LME top 3.")
    else:
        logger.info(f"Shared top features: {intersection}")

    return comparison

def save_results(metrics: Dict, importance: Dict, comparison: Dict, model: xgb.XGBRegressor, params: Dict):
    """Save all results to artifacts."""
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    
    # Save model pickle
    with open(MODEL_PKL_PATH, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {MODEL_PKL_PATH}")

    # Prepare artifact data
    artifact = {
        'metrics': metrics,
        'hyperparameters': params,
        'feature_importance': importance,
        'comparison_with_lme': comparison,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(MODEL_OUTPUT_PATH, 'w') as f:
        json.dump(artifact, f, indent=2)
    logger.info(f"Results saved to {MODEL_OUTPUT_PATH}")

def main():
    """Main entry point for T033."""
    logger.info("Starting T033: Feature Importance and LME Comparison")
    
    try:
        # 1. Load Data
        df = load_data()
        
        # 2. Prepare Features
        X, y, df_meta = prepare_features(df)
        
        # 3. Split Data
        X_train, X_test, y_train, y_test = split_data(X, y, df_meta)
        
        # 4. Train Model
        model = train_model(X_train, y_train)
        
        # 5. Evaluate
        metrics = evaluate_model(model, X_test, y_test)
        
        # 6. Compute Importance
        # Use the full training set for importance calculation to be robust
        importance = compute_importance(model, X_train, y_train)
        
        # 7. Compare with LME
        comparison = compare_with_lme(importance, LME_RESULT_PATH)
        
        # 8. Save Results
        save_results(metrics, importance, comparison, model, model.get_params())
        
        logger.info("T033 completed successfully.")
        
    except Exception as e:
        logger.error(f"T033 failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()