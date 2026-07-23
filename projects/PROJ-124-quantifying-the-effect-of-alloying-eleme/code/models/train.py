"""
Model Training Module for Metallic Glass GFA Prediction.

Implements:
- LOCO (Leave-One-Group-Out) Cross-Validation based on primary metallic element families.
- StandardScaler fitting and persistence.
- Model training (RandomForest, GradientBoosting).
- Saving of transformed training data (X_train, y_train) and scaler.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import mean_absolute_error
import joblib

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger, log_info, log_error, log_warning, log_critical
from config.env import load_config

logger = get_logger(__name__)

# Constants
FEATURE_COLUMNS = [
    'atomic_radius_mean', 'electronegativity_mean', 'VEC_avg', 
    'size_mismatch', 'valence_electron_concentration', 'mixing_entropy',
    'mixing_enthalpy', 'atomic_size_diff_std'
]
# Fallback if specific columns are missing, we will select numeric columns dynamically
TARGET_COLUMN = 'log10_Rc'
COMPOSITION_COLUMN = 'composition'

def load_features_data() -> pd.DataFrame:
    """Load the processed features dataset."""
    data_path = PROJECT_ROOT / 'data' / 'processed' / 'features.csv'
    if not data_path.exists():
        raise FileNotFoundError(f"Features file not found at {data_path}. Run data pipeline first.")
    logger.info(f"Loading features from {data_path}")
    df = pd.read_csv(data_path)
    return df

def extract_primary_element(composition: str) -> str:
    """
    Extract the primary (most abundant) element from a composition string like 'Cu40Zr40Al20'.
    Returns the element symbol of the component with the highest percentage.
    """
    # Simple parser: assumes format ElementPercentage (e.g., Cu40, Zr40)
    # Handles cases where percentage might be float or int
    import re
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*)'
    matches = re.findall(pattern, composition)
    if not matches:
        return "Unknown"
    
    # Find max percentage
    max_val = -1
    primary = "Unknown"
    for elem, val in matches:
        try:
            val_f = float(val)
            if val_f > max_val:
                max_val = val_f
                primary = elem
        except ValueError:
            continue
    return primary

def assign_element_families(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign a 'family' group to each row based on the primary element.
    This is used for Leave-One-Group-Out CV.
    """
    df = df.copy()
    # Extract primary element for each row
    df['primary_element'] = df[COMPOSITION_COLUMN].apply(extract_primary_element)
    
    # Group by primary element to create a numeric group ID for sklearn
    unique_elements = df['primary_element'].unique()
    element_to_group = {elem: i for i, elem in enumerate(unique_elements)}
    df['group_id'] = df['primary_element'].map(element_to_group)
    
    logger.info(f"Assigned {len(unique_elements)} element families for LOCO CV.")
    return df

def perform_loco_cv(X: np.ndarray, y: np.ndarray, groups: np.ndarray, model_class, params: Dict) -> Tuple[float, Dict]:
    """
    Perform Leave-One-Group-Out Cross-Validation.
    
    Args:
        X: Feature matrix
        y: Target vector
        groups: Group labels (primary element families)
        model_class: Sklearn model class
        params: Hyperparameters for the model
        
    Returns:
        mean_mae: Average MAE across folds
        fold_scores: Dict of group_name -> mae
    """
    logo = LeaveOneGroupOut()
    mae_scores = []
    fold_scores = {}
    
    # Map group IDs back to element names for reporting
    # We need to infer the mapping from the groups array and the original data context
    # Since we don't have the original df here, we assume groups are integer IDs 0..N
    # and we will just report by index or try to map if we had the mapping.
    # For now, we report by the unique group ID excluded in that fold.
    
    unique_groups = np.unique(groups)
    group_name_map = {i: f"Group_{i}" for i in unique_groups} # Fallback names
    
    logger.info(f"Starting LOCO CV with {len(unique_groups)} groups using {model_class.__name__}.")
    
    for train_idx, test_idx in logo.split(X, y, groups):
        X_train_fold, X_test_fold = X[train_idx], X[test_idx]
        y_train_fold, y_test_fold = y[train_idx], y[test_idx]
        groups_fold = groups[test_idx]
        
        # Identify the excluded group (should be all same in test set for LOCO)
        excluded_group = groups_fold[0]
        
        # Scale data within the fold? 
        # STRICT LOCO: Fit scaler on train, transform test. 
        # However, for the final model we need a global scaler. 
        # Here we just evaluate performance.
        scaler_fold = StandardScaler()
        X_train_scaled = scaler_fold.fit_transform(X_train_fold)
        X_test_scaled = scaler_fold.transform(X_test_fold)
        
        model = model_class(**params)
        model.fit(X_train_scaled, y_train_fold)
        preds = model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test_fold, preds)
        mae_scores.append(mae)
        fold_scores[group_name_map[excluded_group]] = mae
        
    mean_mae = np.mean(mae_scores)
    logger.info(f"LOCO CV Mean MAE: {mean_mae:.4f}")
    return mean_mae, fold_scores

def train_models(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Main training logic.
    1. Prepare features and target.
    2. Assign groups for LOCO.
    3. Run LOCO CV for RF and GB.
    4. Select best model based on LOCO MAE.
    5. Fit StandardScaler on FULL training data (as per T021 requirement).
    6. Save scaler, X_train, y_train, and best model.
    """
    # 1. Prepare Data
    if not all(col in df.columns for col in FEATURE_COLUMNS):
        # Fallback: Select all numeric columns except composition and target
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [c for c in numeric_cols if c != TARGET_COLUMN]
        logger.warning(f"Specific feature columns not found. Using dynamic numeric columns: {feature_cols}")
    else:
        feature_cols = FEATURE_COLUMNS

    X = df[feature_cols].values
    y = df[TARGET_COLUMN].values
    
    # 2. Assign Groups
    df_with_groups = assign_element_families(df)
    groups = df_with_groups['group_id'].values
    
    # 3. Hyperparameter Grids (Small as per spec)
    rf_params = {
        'n_estimators': [50, 100],
        'max_depth': [5, 10, None],
        'min_samples_split': [2, 5]
    }
    gb_params = {
        'n_estimators': [50, 100],
        'max_depth': [3, 5],
        'learning_rate': [0.05, 0.1]
    }

    # 4. Run LOCO CV
    results = {}
    
    # Try RF
    try:
        # Simple grid search for LOCO performance (picking one config for speed in demo)
        # In a full implementation, we'd loop all params. Here we pick a reasonable default for the CV step
        # to determine which model type is better, then we might re-tune.
        # Per task T021, we need to compare and select.
        best_rf_mae = float('inf')
        best_rf_cfg = None
        
        # Run a small subset of configs for speed
        for n_est in [50, 100]:
            for depth in [5, 10]:
                cfg = {'n_estimators': n_est, 'max_depth': depth, 'min_samples_split': 2}
                mae, scores = perform_loco_cv(X, y, groups, RandomForestRegressor, cfg)
                if mae < best_rf_mae:
                    best_rf_mae = mae
                    best_rf_cfg = cfg
        
        results['RandomForest'] = {'mae': best_rf_mae, 'params': best_rf_cfg}
        log_info(f"RandomForest Best LOCO MAE: {best_rf_mae:.4f} with {best_rf_cfg}")
    except Exception as e:
        log_error(f"RF Training failed: {e}")
        results['RandomForest'] = {'mae': float('inf'), 'params': None}

    # Try GB
    try:
        best_gb_mae = float('inf')
        best_gb_cfg = None
        
        for n_est in [50, 100]:
            for depth in [3, 5]:
                cfg = {'n_estimators': n_est, 'max_depth': depth, 'learning_rate': 0.1}
                mae, scores = perform_loco_cv(X, y, groups, GradientBoostingRegressor, cfg)
                if mae < best_gb_mae:
                    best_gb_mae = mae
                    best_gb_cfg = cfg
        
        results['GradientBoosting'] = {'mae': best_gb_mae, 'params': best_gb_cfg}
        log_info(f"GradientBoosting Best LOCO MAE: {best_gb_mae:.4f} with {best_gb_cfg}")
    except Exception as e:
        log_error(f"GB Training failed: {e}")
        results['GradientBoosting'] = {'mae': float('inf'), 'params': None}

    # 5. Select Best Model
    best_model_name = None
    best_mae = float('inf')
    best_params = None
    best_model_class = None

    for name, res in results.items():
        if res['mae'] < best_mae:
            best_mae = res['mae']
            best_model_name = name
            best_params = res['params']
            best_model_class = RandomForestRegressor if name == 'RandomForest' else GradientBoostingRegressor

    if best_model_name is None:
        raise RuntimeError("No model could be trained successfully.")

    log_info(f"Selected model: {best_model_name} with LOCO MAE: {best_mae:.4f}")

    # 6. Fit Final Model and Scaler on FULL Data
    # CRITICAL: Fit StandardScaler on the full training features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Save transformed data and scaler
    output_dir = PROJECT_ROOT / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    scaler_path = output_dir / 'scaler.pkl'
    x_train_path = output_dir / 'X_train.pkl'
    y_train_path = output_dir / 'y_train.pkl'
    
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    with open(x_train_path, 'wb') as f:
        pickle.dump(X_scaled, f)
    with open(y_train_path, 'wb') as f:
        pickle.dump(y, f)
        
    log_info(f"Saved scaler to {scaler_path}")
    log_info(f"Saved X_train to {x_train_path}")
    log_info(f"Saved y_train to {y_train_path}")

    # Train final model
    final_model = best_model_class(**best_params)
    final_model.fit(X_scaled, y)
    
    # Save model
    model_path = PROJECT_ROOT / 'output' / 'best_model.pkl'
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(final_model, f)
    
    log_info(f"Saved best model to {model_path}")
    
    # Save training metadata
    metadata = {
        'selected_model': best_model_name,
        'loco_mae': best_mae,
        'hyperparameters': best_params,
        'feature_columns': feature_cols,
        'num_samples': len(y),
        'num_features': X_scaled.shape[1]
    }
    metadata_path = PROJECT_ROOT / 'state' / 'training_metadata.json'
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    return metadata

def main():
    """Entry point for the training script."""
    log_info("Starting Model Training (T021)")
    try:
        df = load_features_data()
        metadata = train_models(df)
        log_info(f"Training complete. Metadata: {metadata}")
    except Exception as e:
        log_critical(f"Training pipeline failed: {e}")
        raise

if __name__ == '__main__':
    main()