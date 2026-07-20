"""
Augmented Models for Crack Propagation Prediction.

Implements Random Forest and XGBoost models incorporating composition (wt%)
and heat-treatment descriptors to predict crack growth rates.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
import xgboost as xgb

from config import get_config_dict
from logging_config import get_logger

logger = get_logger(__name__)

# Constants for fallback handling
COMPOSITION_FEATURES = [
    "Fe_wt", "C_wt", "Mn_wt", "Cr_wt", "Ni_wt", "Mo_wt", "V_wt", "Al_wt", "Ti_wt", "Si_wt"
]
HEAT_TREATMENT_FEATURES = [
    "heat_treatment_encoded"
]
REQUIRED_BASE_FEATURES = ["log_dK"]  # Delta K is always required

def _get_available_features(df: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
    """
    Identify available composition and heat-treatment features in the dataframe.
    
    Args:
        df: Input dataframe containing potential features.
        
    Returns:
        Tuple of (available_composition, available_heat_treatment, missing_features)
    """
    available_comp = [col for col in COMPOSITION_FEATURES if col in df.columns]
    available_ht = [col for col in HEAT_TREATMENT_FEATURES if col in df.columns]
    
    missing_comp = [col for col in COMPOSITION_FEATURES if col not in df.columns]
    missing_ht = [col for col in HEAT_TREATMENT_FEATURES if col not in df.columns]
    
    missing_features = []
    if missing_comp:
        missing_features.extend([f"Composition: {c}" for c in missing_comp])
    if missing_ht:
        missing_features.extend([f"Heat Treatment: {h}" for h in missing_ht])
        
    return available_comp, available_ht, missing_features

def _handle_missing_features(
    df: pd.DataFrame,
    comp_features: List[str],
    ht_features: List[str],
    missing_features: List[str]
) -> Tuple[pd.DataFrame, List[str], bool]:
    """
    Gracefully handle missing composition or heat-treatment columns.
    
    Strategy:
    1. If ALL composition features are missing, drop them from the model (log warning)
    2. If ALL heat-treatment features are missing, drop them from the model (log warning)
    3. If SOME features are missing, fill with 0.0 (assuming normalized/encoded) or 
       the mean of available features if present.
    4. If NO enriched features are available (only base features), return a flag.
    
    Args:
        df: Input dataframe.
        comp_features: List of available composition features.
        ht_features: List of available heat-treatment features.
        missing_features: List of missing feature descriptions.
        
    Returns:
        Tuple of (processed_df, remaining_features, is_enriched_model)
    """
    remaining_features = []
    is_enriched = False
    
    # Handle missing composition features
    if comp_features:
        # Some composition features exist
        # Fill missing ones with 0.0 (common for encoded/normalized wt%)
        # or calculate mean if we have at least one value
        for col in COMPOSITION_FEATURES:
            if col in df.columns:
                remaining_features.append(col)
            else:
                # Log that this specific column is being filled with 0
                logger.debug(f"Filling missing composition feature '{col}' with 0.0")
                df[col] = 0.0
                remaining_features.append(col)
        is_enriched = True
    else:
        # No composition features available
        if missing_features:
            logger.warning(
                f"No composition features available. Missing: {missing_features}. "
                "Proceeding without composition data. Model accuracy may be reduced."
            )
        # Ensure columns exist for consistency, filled with 0
        for col in COMPOSITION_FEATURES:
            if col not in df.columns:
                df[col] = 0.0
            else:
                remaining_features.append(col)
    
    # Handle missing heat-treatment features
    if ht_features:
        for col in HEAT_TREATMENT_FEATURES:
            if col in df.columns:
                remaining_features.append(col)
            else:
                logger.debug(f"Filling missing heat-treatment feature '{col}' with 0.0")
                df[col] = 0.0
                remaining_features.append(col)
        is_enriched = True
    else:
        if missing_features:
            logger.warning(
                f"No heat-treatment features available. Missing: {missing_features}. "
                "Proceeding without heat-treatment data. Model accuracy may be reduced."
            )
        for col in HEAT_TREATMENT_FEATURES:
            if col not in df.columns:
                df[col] = 0.0
            else:
                remaining_features.append(col)
                
    return df, remaining_features, is_enriched

def train_random_forest(
    df: pd.DataFrame,
    target_col: str = "log_da_dN",
    config: Optional[Dict[str, Any]] = None,
    random_state: int = 42
) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """
    Train a Random Forest model with graceful handling of missing features.
    
    Args:
        df: Preprocessed dataframe.
        target_col: Name of the target column.
        config: Optional configuration dictionary.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (trained_model, metrics_dict)
    """
    logger.info("Training Random Forest model...")
    
    # Determine available features
    available_comp, available_ht, missing_features = _get_available_features(df)
    
    if missing_features:
        logger.info(f"Missing features detected: {missing_features}")
    
    # Prepare features with fallback handling
    processed_df, feature_columns, is_enriched = _handle_missing_features(
        df, available_comp, available_ht, missing_features
    )
    
    # Ensure base features are present
    for base_col in REQUIRED_BASE_FEATURES:
        if base_col not in processed_df.columns:
            raise ValueError(f"Required base feature '{base_col}' is missing from dataset.")
        if base_col not in feature_columns:
            feature_columns.append(base_col)
    
    logger.info(f"Using features: {feature_columns}")
    if not is_enriched:
        logger.warning("No enriched features (composition/heat-treatment) available. "
                     "Model will rely solely on base features (Paris Law).")
    
    X = processed_df[feature_columns].values
    y = processed_df[target_col].values
    
    # Handle NaNs in target (drop rows if necessary)
    valid_mask = ~np.isnan(y) & ~np.isnan(X).any(axis=1)
    if not np.all(valid_mask):
        logger.warning(f"Dropping {np.sum(~valid_mask)} rows with NaN values.")
        X = X[valid_mask]
        y = y[valid_mask]
    
    if len(X) == 0:
        raise ValueError("No valid data points remaining after filtering NaNs.")
    
    # Initialize model with safe defaults
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=random_state,
        n_jobs=-1
    )
    
    model.fit(X, y)
    
    # Calculate in-sample R2
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    
    metrics = {
        "model_type": "RandomForest",
        "is_enriched": is_enriched,
        "missing_features": missing_features,
        "feature_columns": feature_columns,
        "r2": r2,
        "mse": mse,
        "n_samples": len(y)
    }
    
    logger.info(f"Random Forest trained. R2: {r2:.4f}, MSE: {mse:.4f}")
    return model, metrics

def train_xgboost(
    df: pd.DataFrame,
    target_col: str = "log_da_dN",
    config: Optional[Dict[str, Any]] = None,
    random_state: int = 42
) -> Tuple[xgb.XGBRegressor, Dict[str, Any]]:
    """
    Train an XGBoost model with graceful handling of missing features.
    
    Args:
        df: Preprocessed dataframe.
        target_col: Name of the target column.
        config: Optional configuration dictionary.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (trained_model, metrics_dict)
    """
    logger.info("Training XGBoost model...")
    
    # Determine available features
    available_comp, available_ht, missing_features = _get_available_features(df)
    
    if missing_features:
        logger.info(f"Missing features detected: {missing_features}")
    
    # Prepare features with fallback handling
    processed_df, feature_columns, is_enriched = _handle_missing_features(
        df, available_comp, available_ht, missing_features
    )
    
    # Ensure base features are present
    for base_col in REQUIRED_BASE_FEATURES:
        if base_col not in processed_df.columns:
            raise ValueError(f"Required base feature '{base_col}' is missing from dataset.")
        if base_col not in feature_columns:
            feature_columns.append(base_col)
    
    logger.info(f"Using features: {feature_columns}")
    if not is_enriched:
        logger.warning("No enriched features (composition/heat-treatment) available. "
                     "Model will rely solely on base features (Paris Law).")
    
    X = processed_df[feature_columns].values
    y = processed_df[target_col].values
    
    # Handle NaNs
    valid_mask = ~np.isnan(y) & ~np.isnan(X).any(axis=1)
    if not np.all(valid_mask):
        logger.warning(f"Dropping {np.sum(~valid_mask)} rows with NaN values.")
        X = X[valid_mask]
        y = y[valid_mask]
    
    if len(X) == 0:
        raise ValueError("No valid data points remaining after filtering NaNs.")
    
    # Initialize model
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=random_state,
        n_jobs=-1,
        verbosity=0
    )
    
    model.fit(X, y)
    
    # Calculate in-sample R2
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    
    metrics = {
        "model_type": "XGBoost",
        "is_enriched": is_enriched,
        "missing_features": missing_features,
        "feature_columns": feature_columns,
        "r2": r2,
        "mse": mse,
        "n_samples": len(y)
    }
    
    logger.info(f"XGBoost trained. R2: {r2:.4f}, MSE: {mse:.4f}")
    return model, metrics

def train_augmented_model(
    df: pd.DataFrame,
    model_type: str = "rf",
    target_col: str = "log_da_dN",
    config: Optional[Dict[str, Any]] = None
) -> Tuple[Any, Dict[str, Any]]:
    """
    Factory function to train an augmented model (RF or XGBoost).
    
    Args:
        df: Preprocessed dataframe.
        model_type: 'rf' for Random Forest, 'xgb' for XGBoost.
        target_col: Target column name.
        config: Optional configuration.
        
    Returns:
        Tuple of (model, metrics)
    """
    if model_type.lower() == "rf":
        return train_random_forest(df, target_col, config)
    elif model_type.lower() == "xgb":
        return train_xgboost(df, target_col, config)
    else:
        raise ValueError(f"Unsupported model type: {model_type}. Use 'rf' or 'xgb'.")

def predict(
    model: Any,
    df: pd.DataFrame,
    feature_columns: Optional[List[str]] = None
) -> np.ndarray:
    """
    Generate predictions using a trained model.
    
    Args:
        model: Trained model instance.
        df: Dataframe with features.
        feature_columns: List of feature columns to use (if None, model expects all columns).
        
    Returns:
        Array of predictions.
    """
    if feature_columns is None:
        # Try to infer from model if possible, otherwise raise error
        if hasattr(model, 'feature_names_in_'):
            feature_columns = model.feature_names_in_
        elif hasattr(model, 'feature_importances_'):
            # Fallback: assume standard order if not known
            logger.warning("Feature names not found in model. Attempting to use standard features.")
            feature_columns = REQUIRED_BASE_FEATURES + COMPOSITION_FEATURES + HEAT_TREATMENT_FEATURES
            feature_columns = [c for c in feature_columns if c in df.columns]
        else:
            raise ValueError("Cannot determine feature columns for prediction.")
    
    # Ensure all required columns exist
    missing = [c for c in feature_columns if c not in df.columns]
    if missing:
        # Graceful fallback: fill missing with 0
        logger.warning(f"Missing features for prediction: {missing}. Filling with 0.")
        for col in missing:
            df[col] = 0.0
    
    X = df[feature_columns].values
    return model.predict(X)

def evaluate_model(
    model: Any,
    df: pd.DataFrame,
    target_col: str = "log_da_dN",
    feature_columns: Optional[List[str]] = None
) -> Dict[str, float]:
    """
    Evaluate model performance on a dataset.
    
    Args:
        model: Trained model.
        df: Evaluation dataframe.
        target_col: Target column.
        feature_columns: Feature columns to use.
        
    Returns:
        Dictionary of metrics (R2, MSE, RMSE).
    """
    y_true = df[target_col].values
    y_pred = predict(model, df, feature_columns)
    
    r2 = r2_score(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    
    return {
        "r2": r2,
        "mse": mse,
        "rmse": rmse
    }