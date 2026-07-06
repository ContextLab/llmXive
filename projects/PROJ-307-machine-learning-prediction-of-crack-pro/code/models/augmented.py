"""
Augmented model implementation (Random Forest, XGBoost).

Uses composition and heat-treatment features.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score
import xgboost as xgb

from config import get_config_dict
from logging_config import get_logger

logger = get_logger(__name__)

# Constants for feature handling
COMPOSITION_PREFIX = "wt_"
HEAT_TREATMENT_COL = "heat_treatment"
TARGET_COL = "da_dN"
DELTA_K_COL = "delta_K"

# Fallback handling for missing composition/heat treatment
FALLBACK_COMPOSITION = 0.0
FALLBACK_HEAT_TREATMENT = "Unknown/Not Specified"

def _prepare_features(
    df: pd.DataFrame,
    composition_cols: Optional[List[str]] = None,
    encode_heat_treatment: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Prepare feature matrix X and target y.

    Handles missing composition columns by filling with fallback values.
    Handles missing heat treatment by imputing "Unknown/Not Specified".

    Returns:
        X: Feature DataFrame
        y: Target Series
        meta: Metadata dict with column names and encoding info
    """
    logger.info("Preparing features for augmented model...")

    # Ensure target exists
    if TARGET_COL not in df.columns:
        raise ValueError(f"Target column '{TARGET_COL}' not found in dataset")

    y = df[TARGET_COL].copy()

    # Determine composition columns
    if composition_cols is None:
        composition_cols = [c for c in df.columns if c.startswith(COMPOSITION_PREFIX)]
    
    if not composition_cols:
        logger.warning("No composition columns found (prefix '%s'). Using empty feature set.", COMPOSITION_PREFIX)
    
    # Prepare composition features
    X_comp = pd.DataFrame()
    for col in composition_cols:
        if col in df.columns:
            # Impute missing composition values with 0.0 (fallback)
            X_comp[col] = df[col].fillna(FALLBACK_COMPOSITION)
        else:
            # Column missing entirely - add with fallback values
            logger.warning("Composition column '%s' not found. Filling with fallback.", col)
            X_comp[col] = FALLBACK_COMPOSITION

    # Prepare heat treatment feature
    X_ht = pd.DataFrame()
    if HEAT_TREATMENT_COL in df.columns:
        ht_series = df[HEAT_TREATMENT_COL].fillna(FALLBACK_HEAT_TREATMENT)
    else:
        logger.warning("Heat treatment column '%s' not found. Filling with fallback.", HEAT_TREATMENT_COL)
        ht_series = pd.Series(FALLBACK_HEAT_TREATMENT, index=df.index)

    if encode_heat_treatment:
        # One-hot encode heat treatment
        X_ht = pd.get_dummies(ht_series, prefix="ht")
        if X_ht.empty:
            X_ht = pd.DataFrame(index=df.index)
    else:
        # Keep as string if not encoding (rare case)
        X_ht = pd.DataFrame({HEAT_TREATMENT_COL: ht_series})

    # Combine features
    X = pd.concat([X_comp, X_ht], axis=1)

    # Drop rows with any NaN in features or target
    mask = y.notna()
    if not X.empty:
        mask = mask & X.notna().all(axis=1)
    
    X = X[mask]
    y = y[mask]

    if X.empty:
        raise ValueError("Feature matrix is empty after preprocessing.")

    logger.info("Feature matrix shape: %s, Target shape: %s", X.shape, y.shape)

    meta = {
        "composition_cols": composition_cols,
        "encode_heat_treatment": encode_heat_treatment,
        "feature_cols": list(X.columns),
        "n_samples": len(X)
    }

    return X, y, meta

def train_random_forest(
    X: pd.DataFrame,
    y: pd.Series,
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    random_state: int = 42,
    cv_folds: int = 5
) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """
    Train a Random Forest regressor.

    Args:
        X: Feature matrix
        y: Target vector
        n_estimators: Number of trees
        max_depth: Maximum tree depth
        random_state: Random seed
        cv_folds: Number of CV folds

    Returns:
        model: Trained RandomForestRegressor
        metrics: Dict with R2 scores and feature importance
    """
    logger.info("Training Random Forest (n_estimators=%d, max_depth=%s)...", n_estimators, max_depth)

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
        verbose=0
    )

    # Cross-validation
    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    cv_scores = cross_val_score(model, X, y, cv=kf, scoring='r2')
    
    logger.info("CV R2 scores: %s, Mean: %.4f (+/- %.4f)", 
                cv_scores, cv_scores.mean(), cv_scores.std())

    # Train on full data
    model.fit(X, y)

    # Feature importance
    feature_importance = dict(zip(X.columns, model.feature_importances_))
    sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)

    metrics = {
        "model_type": "RandomForest",
        "cv_r2_mean": float(cv_scores.mean()),
        "cv_r2_std": float(cv_scores.std()),
        "cv_scores": cv_scores.tolist(),
        "feature_importance": sorted_importance,
        "n_features": len(X.columns),
        "n_samples": len(X)
    }

    return model, metrics

def train_xgboost(
    X: pd.DataFrame,
    y: pd.Series,
    n_estimators: int = 100,
    max_depth: int = 6,
    learning_rate: float = 0.1,
    random_state: int = 42,
    cv_folds: int = 5
) -> Tuple[xgb.XGBRegressor, Dict[str, Any]]:
    """
    Train an XGBoost regressor.

    Args:
        X: Feature matrix
        y: Target vector
        n_estimators: Number of boosting rounds
        max_depth: Maximum tree depth
        learning_rate: Step size shrinkage
        random_state: Random seed
        cv_folds: Number of CV folds

    Returns:
        model: Trained XGBRegressor
        metrics: Dict with R2 scores and feature importance
    """
    logger.info("Training XGBoost (n_estimators=%d, max_depth=%d, lr=%.3f)...", 
                n_estimators, max_depth, learning_rate)

    model = xgb.XGBRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        random_state=random_state,
        n_jobs=-1,
        verbosity=0,
        eval_metric='rmse'
    )

    # Cross-validation
    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    cv_scores = cross_val_score(model, X, y, cv=kf, scoring='r2')
    
    logger.info("CV R2 scores: %s, Mean: %.4f (+/- %.4f)", 
                cv_scores, cv_scores.mean(), cv_scores.std())

    # Train on full data
    model.fit(X, y)

    # Feature importance
    feature_importance = dict(zip(X.columns, model.feature_importances_))
    sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)

    metrics = {
        "model_type": "XGBoost",
        "cv_r2_mean": float(cv_scores.mean()),
        "cv_r2_std": float(cv_scores.std()),
        "cv_scores": cv_scores.tolist(),
        "feature_importance": sorted_importance,
        "n_features": len(X.columns),
        "n_samples": len(X)
    }

    return model, metrics

def train_augmented_model(
    data_path: Union[str, Path],
    model_type: str = "xgboost",
    composition_cols: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None,
    output_path: Optional[Union[str, Path]] = None
) -> Tuple[Any, Dict[str, Any]]:
    """
    Main entry point to train augmented models.

    Args:
        data_path: Path to CSV data file
        model_type: 'random_forest' or 'xgboost'
        composition_cols: List of composition column names (optional)
        config: Hyperparameter config dict (optional)
        output_path: Path to save model and metrics (optional)

    Returns:
        model: Trained model instance
        metrics: Training metrics and metadata
    """
    logger.info("Starting augmented model training for type: %s", model_type)

    # Load config
    if config is None:
        config = get_config_dict()

    # Load data
    logger.info("Loading data from %s", data_path)
    df = pd.read_csv(data_path)
    
    # Prepare features
    X, y, meta = _prepare_features(df, composition_cols)

    # Get hyperparameters from config
    if model_type.lower() == "random_forest":
        n_estimators = config.get("rf_n_estimators", 100)
        max_depth = config.get("rf_max_depth", None)
        random_state = config.get("random_seed", 42)
        cv_folds = config.get("cv_folds", 5)

        model, metrics = train_random_forest(
            X, y,
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            cv_folds=cv_folds
        )
    
    elif model_type.lower() == "xgboost":
        n_estimators = config.get("xgb_n_estimators", 100)
        max_depth = config.get("xgb_max_depth", 6)
        learning_rate = config.get("xgb_learning_rate", 0.1)
        random_state = config.get("random_seed", 42)
        cv_folds = config.get("cv_folds", 5)

        model, metrics = train_xgboost(
            X, y,
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            cv_folds=cv_folds
        )
    
    else:
        raise ValueError(f"Unsupported model_type: {model_type}. Choose 'random_forest' or 'xgboost'.")

    # Merge metadata into metrics
    metrics.update(meta)

    # Save outputs if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model (using joblib would be better, but saving dict for simplicity)
        import pickle
        model_path = output_path / f"{model_type.lower()}_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(model, f)
        
        # Save metrics
        import json
        metrics_path = output_path / f"{model_type.lower()}_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2, default=str)
        
        logger.info("Model and metrics saved to %s", output_path)

    logger.info("Augmented model training completed. CV R2: %.4f", metrics.get("cv_r2_mean", 0))
    return model, metrics

def predict(model: Any, X: pd.DataFrame) -> np.ndarray:
    """
    Generate predictions using a trained augmented model.

    Args:
        model: Trained model (RandomForest or XGBoost)
        X: Feature matrix

    Returns:
        predictions: Array of predicted values
    """
    if not hasattr(model, 'predict'):
        raise TypeError("Model must have a 'predict' method.")
    
    return model.predict(X)

def evaluate_model(
    model: Any,
    X: pd.DataFrame,
    y: pd.Series
) -> Dict[str, float]:
    """
    Evaluate model performance.

    Args:
        model: Trained model
        X: Feature matrix
        y: True target values

    Returns:
        metrics: Dict with R2 and MSE
    """
    y_pred = predict(model, X)
    
    r2 = r2_score(y, y_pred)
    mse = float(np.mean((y - y_pred) ** 2))
    
    return {
        "r2": r2,
        "mse": mse,
        "rmse": np.sqrt(mse)
    }
