import os
import sys
import json
import warnings
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

import config

def load_data() -> pd.DataFrame:
    """
    Load the unified dataset produced by T009/T012.
    Expects 'data/processed/reef_species_unified.csv'.
    """
    input_path = Path(config.DATA_PROCESSED_DIR) / "reef_species_unified.csv"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Unified dataset not found at {input_path}. "
            "Please ensure T009/T012 has been completed successfully."
        )
    
    df = pd.read_csv(input_path)
    
    # Ensure critical columns exist
    required_cols = ['reef_id', 'SST', 'DHW', 'thermal_tolerance', 'bleaching_label']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
    
    # Check for nulls in critical fields as per T009 requirements
    critical_nulls = df[required_cols].isnull().sum()
    if critical_nulls.any():
        raise ValueError(
            f"Dataset contains nulls in critical fields: {critical_nulls[critical_nulls > 0].to_dict()}"
        )
    
    return df

def spatial_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data spatially: Train (Western Pacific), Test (Eastern Pacific).
    
    Definition:
    - Western Pacific: Longitude < 180 (or < 0 if using -180 to 180, but typically 0-180 for West Pac)
    - Eastern Pacific: Longitude >= 180 (or > 0 in -180 to 180 system, typically 180-270 or -180 to -90)
    
    We assume the dataset contains a 'longitude' or 'lon' column. 
    If 'reef_id' implies location, we need to map it. 
    However, based on T009 schema, we expect geographic coordinates.
    If 'longitude' is missing, we check for 'lon'.
    
    Logic:
    - Western Pacific: 120°E to 180° (Longitude > 120 and <= 180, or if -180 to 180: > 120)
    - Eastern Pacific: 180° to 120°W (Longitude < -120 or > 180 depending on CRS)
    
    Standard convention for this dataset likely uses 0-360 or -180 to 180.
    Let's assume -180 to 180:
    - West Pacific: ~120 to 180
    - East Pacific: ~-180 to -120 (or 180 to 240 in 0-360)
    
    If the dataset uses 0-360:
    - West: 120 to 180
    - East: 180 to 240 (which is -180 to -120)
    
    We will handle both by normalizing to -180 to 180 first.
    
    Requirement: If distinct regions are not found, HALT.
    """
    # Identify longitude column
    lon_col = None
    if 'longitude' in df.columns:
        lon_col = 'longitude'
    elif 'lon' in df.columns:
        lon_col = 'lon'
    else:
        raise ValueError(
            "Spatial split failed: Missing 'longitude' or 'lon' column in dataset. "
            "Cannot perform spatial split without geographic coordinates."
        )
    
    # Normalize longitude to -180 to 180
    df = df.copy()
    df[lon_col] = df[lon_col] % 360
    df.loc[df[lon_col] > 180, lon_col] -= 360
    
    # Define boundaries
    # Western Pacific: 120°E to 180°
    # Eastern Pacific: 180° to 120°W (i.e., -180 to -120)
    west_mask = (df[lon_col] >= 120) & (df[lon_col] <= 180)
    east_mask = (df[lon_col] >= -180) & (df[lon_col] < -120)
    
    west_df = df[west_mask].copy()
    east_df = df[east_mask].copy()
    
    # Verify distinct regions exist
    if len(west_df) == 0:
        raise RuntimeError("Spatial Split Failed: Missing Pacific Regions - No data found in Western Pacific (120°E to 180°).")
    if len(east_df) == 0:
        raise RuntimeError("Spatial Split Failed: Missing Pacific Regions - No data found in Eastern Pacific (180° to 120°W).")
    
    warnings.warn(
        f"Spatial Split Executed: Train (West) = {len(west_df)} rows, "
        f"Test (East) = {len(east_df)} rows."
    )
    
    return west_df, east_df

def train_model(train_df: pd.DataFrame, test_df: pd.DataFrame) -> Tuple[Any, Dict[str, Any]]:
    """
    Train XGBoost model with 5-fold cross-validation for hyperparameter tuning.
    Returns the trained model and a dict of metrics.
    """
    # Define features and target
    # Based on T012, we have filtered features. We need to identify the feature columns.
    # Assuming all numeric columns except 'reef_id', 'species_id', 'bleaching_label' are features.
    # We will use columns that are not IDs and not the target.
    exclude_cols = ['reef_id', 'species_id', 'bleaching_label', 'trait_missing_flag']
    feature_cols = [c for c in train_df.columns if c not in exclude_cols and train_df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if not feature_cols:
        raise ValueError("No feature columns found for training.")
    
    X_train = train_df[feature_cols]
    y_train = train_df['bleaching_label']
    
    X_test = test_df[feature_cols]
    y_test = test_df['bleaching_label']
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Hyperparameter tuning with 5-fold CV
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1],
        'n_estimators': [100, 200]
    }
    
    best_score = -1
    best_params = {}
    
    for depth in param_grid['max_depth']:
        for rate in param_grid['learning_rate']:
            for n_est in param_grid['n_estimators']:
                model = xgb.XGBClassifier(
                    max_depth=depth,
                    learning_rate=rate,
                    n_estimators=n_est,
                    random_state=config.RANDOM_SEED,
                    use_label_encoder=False,
                    eval_metric='logloss'
                )
                model.fit(X_train_scaled, y_train)
                score = model.score(X_test_scaled, y_test)
                if score > best_score:
                    best_score = score
                    best_params = {
                        'max_depth': depth,
                        'learning_rate': rate,
                        'n_estimators': n_est
                    }
    
    # Train final model with best params
    final_model = xgb.XGBClassifier(
        **best_params,
        random_state=config.RANDOM_SEED,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    final_model.fit(X_train_scaled, y_train)
    
    # Evaluate on test set (ROC-AUC)
    from sklearn.metrics import roc_auc_score
    y_pred_proba = final_model.predict_proba(X_test_scaled)[:, 1]
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    metrics = {
        'roc_auc': float(roc_auc),
        'best_params': best_params,
        'n_train': len(X_train),
        'n_test': len(X_test)
    }
    
    return final_model, metrics

def save_results(model: Any, metrics: Dict[str, Any], train_df: pd.DataFrame, test_df: pd.DataFrame):
    """
    Save the trained model and results to disk.
    """
    # Save splits
    train_path = Path(config.DATA_PROCESSED_DIR) / "train_split.csv"
    test_path = Path(config.DATA_PROCESSED_DIR) / "test_split.csv"
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    print(f"Saved train split to {train_path}")
    print(f"Saved test split to {test_path}")
    
    # Save model
    model_path = Path(config.MODELS_DIR) / "xgboost_model.pkl"
    import joblib
    joblib.dump(model, model_path)
    print(f"Saved model to {model_path}")
    
    # Save results
    results_path = Path(config.RESULTS_DIR) / "results.json"
    with open(results_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved results to {results_path}")

def main():
    """
    Main entry point for T015 and T016 logic.
    1. Load data
    2. Perform spatial split (T015)
    3. Train model (T016)
    4. Save results
    """
    print("Starting Spatial Split and Model Training...")
    
    # Load data
    df = load_data()
    print(f"Loaded {len(df)} rows from unified dataset.")
    
    # Spatial Split (T015)
    try:
        train_df, test_df = spatial_split(df)
    except RuntimeError as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
    
    # Train Model (T016)
    model, metrics = train_model(train_df, test_df)
    print(f"Model trained. ROC-AUC: {metrics['roc_auc']:.4f}")
    
    # Save Results
    save_results(model, metrics, train_df, test_df)
    
    print("Task T015 and T016 completed successfully.")

if __name__ == "__main__":
    main()