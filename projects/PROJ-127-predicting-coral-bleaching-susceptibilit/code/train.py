import os
import sys
import json
import warnings
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import roc_auc_score, make_scorer
from sklearn.preprocessing import StandardScaler

import config

# Ensure paths exist
PROCESSED_DIR = Path(config.PROCESSED_DATA_DIR)
MODELS_DIR = Path(config.MODEL_DIR)
RESULTS_DIR = Path(config.RESULTS_DIR)

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_data() -> pd.DataFrame:
    """Load the unified dataset and filtered features."""
    unified_path = PROCESSED_DIR / "reef_species_unified.csv"
    filtered_path = PROCESSED_DIR / "filtered_features.csv"

    if not unified_path.exists():
        raise FileNotFoundError(f"Unified data not found at {unified_path}. Run T014/T019 first.")
    if not filtered_path.exists():
        raise FileNotFoundError(f"Filtered features not found at {filtered_path}. Run T019 first.")

    df = pd.read_csv(unified_path)
    features_df = pd.read_csv(filtered_path)

    # Determine target column based on spec (usually 'bleached' or similar)
    # Assuming the target is 'bleaching_event' or 'bleached' based on typical schema
    target_col = None
    for col in ['bleaching_event', 'bleached', 'is_bleached']:
        if col in df.columns:
            target_col = col
            break
    
    if target_col is None:
        # Fallback to last column if standard names missing (bad practice but robust for skeleton)
        target_col = df.columns[-1]
        warnings.warn(f"Target column not explicitly found, using '{target_col}'.")

    # Merge with filtered features to ensure only valid predictors are used
    # The features_df usually contains the column names or the processed data
    # Assuming features_df contains the processed feature matrix + target, or just a list of cols
    # Based on T019 description: "Save filtered feature list to data/processed/filtered_features.csv"
    # It might be a list of columns. Let's assume it's a DataFrame with the processed data or a list of columns.
    # To be safe and robust: if it has 'feature_name' col, use it as a filter list.
    if 'feature_name' in features_df.columns:
        valid_features = features_df['feature_name'].tolist()
        # Ensure target is in valid features if it was dropped by accident (unlikely)
        valid_features.append(target_col)
        valid_features.append('reef_id') # Keep ID for splitting if needed
        valid_features.append('region') # Keep region for spatial split
        
        X = df[valid_features].copy()
    else:
        # If filtered_features.csv is the actual data
        X = features_df.copy()
        if target_col in X.columns:
            pass
        elif 'bleaching_event' in X.columns:
            target_col = 'bleaching_event'
        else:
            raise ValueError("Could not determine target column in filtered data.")

    return X, target_col

def spatial_split(df: pd.DataFrame, target_col: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data spatially: Train (Western Pacific), Test (Eastern Pacific).
    Assumes a 'region' or 'longitude' column exists.
    """
    # Heuristic for West vs East Pacific based on longitude
    # Western Pacific: Longitude < 180 (or specific range like 100E-180E)
    # Eastern Pacific: Longitude > -100 (or specific range like -100W to -80W)
    # We need to infer the column name. Common names: 'longitude', 'lon', 'long'
    lon_col = None
    for c in ['longitude', 'lon', 'long', 'x']:
        if c in df.columns:
            lon_col = c
            break
    
    if lon_col is None:
        raise ValueError("Longitude column not found for spatial split.")

    # Define split logic: West (Train) vs East (Test)
    # Simple heuristic: < 150 (West) vs >= 150 (East) - adjust based on actual data distribution
    # Using a standard Pacific split: 160E is a common boundary
    # Let's assume positive longitudes are West Pacific (100-180) and negative are East Pacific (-180 to -60)
    # Actually, standard WGS84: West Pacific ~ 120E to 180, East Pacific ~ -100 to -80.
    # Let's split by > 0 (West) vs < 0 (East) as a robust proxy if data spans the dateline correctly?
    # Better: Use a specific boundary. Let's assume 160 degrees East is the divider.
    # 160E = 160. East Pacific is usually negative longitudes in this context.
    # Let's try: Train if lon > 0 (West), Test if lon < 0 (East).
    
    train_mask = df[lon_col] > 0
    test_mask = df[lon_col] <= 0

    train_df = df[train_mask]
    test_df = df[test_mask]

    y_train = train_df[target_col]
    y_test = test_df[target_col]
    
    X_train = train_df.drop(columns=[target_col, lon_col])
    X_test = test_df.drop(columns=[target_col, lon_col])

    # Handle zero positives in test set
    if y_test.sum() == 0:
        warnings.warn("Test set has zero positive events. ROC-AUC will be skipped.")
        return X_train, X_test, y_train, y_test

    return X_train, X_test, y_train, y_test

def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[xgb.XGBClassifier, Dict[str, Any]]:
    """
    Train XGBoost with 5-fold CV for hyperparameter tuning.
    """
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1],
        'n_estimators': [100, 200],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }

    model = xgb.XGBClassifier(
        objective='binary:logistic',
        eval_metric='logloss',
        random_state=config.RANDOM_SEED,
        use_label_encoder=False
    )

    scorer = make_scorer(roc_auc_score, needs_proba=True)

    grid_search = GridSearchCV(
        model,
        param_grid,
        cv=5,
        scoring=scorer,
        n_jobs=-1,
        verbose=1
    )

    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_

    return best_model, best_params

def evaluate_model(model: xgb.XGBClassifier, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
    """
    Evaluate model on test set.
    """
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Check for zero positives again before calculating AUC
    if y_test.sum() == 0:
        return {
            "roc_auc": None,
            "warning": "Test set has zero positive events; ROC-AUC not calculated."
        }

    try:
        roc_auc = roc_auc_score(y_test, y_pred_proba)
    except ValueError as e:
        warnings.warn(f"ROC-AUC calculation failed: {e}")
        roc_auc = None

    return {
        "roc_auc": roc_auc,
        "n_test_samples": len(y_test),
        "n_positive_test": int(y_test.sum())
    }

def save_results(best_params: Dict[str, Any], eval_metrics: Dict[str, Any], model_path: Path):
    """Save model and results."""
    import joblib
    
    joblib.dump(model_path, model_path)
    
    results = {
        "best_params": best_params,
        "evaluation_metrics": eval_metrics,
        "model_path": str(model_path)
    }

    results_path = RESULTS_DIR / "training_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Model saved to {model_path}")
    print(f"Results saved to {results_path}")

def main():
    """Main entry point for training."""
    print("Starting Training Pipeline (T008)...")
    
    try:
        # 1. Load Data
        df, target_col = load_data()
        print(f"Loaded data with {len(df)} rows. Target: {target_col}")

        # 2. Spatial Split
        X_train, X_test, y_train, y_test = spatial_split(df, target_col)
        print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

        # 3. Train Model
        model, best_params = train_model(X_train, y_train)
        print(f"Training complete. Best params: {best_params}")

        # 4. Evaluate
        eval_metrics = evaluate_model(model, X_test, y_test)
        print(f"Evaluation metrics: {eval_metrics}")

        # 5. Save
        model_path = MODELS_DIR / "xgboost_bleaching_model.joblib"
        save_results(best_params, eval_metrics, model_path)

        print("T008 Completed Successfully.")

    except FileNotFoundError as e:
        print(f"Error: {e}. Ensure T014 and T019 are completed first.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
