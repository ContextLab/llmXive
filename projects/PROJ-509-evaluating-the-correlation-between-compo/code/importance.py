"""
Feature Importance Analysis and Multi-Collinearity Check (VIF).

This module handles:
1. Loading trained models.
2. Extracting Random Forest importances.
3. Calculating Permutation Importance.
4. Validating correlation between methods.
5. Ranking features.
6. Calculating Variance Inflation Factor (VIF) for multi-collinearity.
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import project utilities
from config import load_paths
from utils.logging import get_logger

# Constants
VIF_THRESHOLD = 10.0
CORRELATION_THRESHOLD = 0.8

logger = get_logger(__name__)

def load_models(models_path: Path) -> Dict[str, Any]:
    """Load trained models from the pickle file."""
    if not models_path.exists():
        raise FileNotFoundError(f"Models file not found: {models_path}")
    
    with open(models_path, 'rb') as f:
        return pickle.load(f)

def load_feature_names(data_path: Path) -> List[str]:
    """Load feature names from the processed dataset."""
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    # Exclude target and non-feature columns
    feature_cols = [col for col in df.columns if col not in ['formation_energy', 'material_id', 'structure_id']]
    return feature_cols

def extract_rf_importances(model: RandomForestRegressor, feature_names: List[str]) -> Dict[str, float]:
    """Extract feature importances from a trained Random Forest model."""
    importances = model.feature_importances_
    return dict(zip(feature_names, importances.tolist()))

def calculate_permutation_importance(
    model: RandomForestRegressor,
    X: pd.DataFrame,
    y: pd.Series,
    feature_names: List[str],
    n_repeats: int = 10,
    random_state: int = 42
) -> Dict[str, float]:
    """Calculate permutation importance for a model."""
    result = permutation_importance(
        model, X, y, 
        n_repeats=n_repeats, 
        random_state=random_state, 
        scoring='r2'
    )
    # Use mean importance
    return dict(zip(feature_names, result.importances_mean.tolist()))

def validate_correlation(
    rf_importances: Dict[str, float],
    perm_importances: Dict[str, float]
) -> float:
    """Calculate Pearson correlation between RF and Permutation importances."""
    keys = list(rf_importances.keys())
    if not keys:
        return 0.0
    
    rf_vals = np.array([rf_importances[k] for k in keys])
    perm_vals = np.array([perm_importances[k] for k in keys])
    
    # Handle constant arrays
    if np.std(rf_vals) == 0 or np.std(perm_vals) == 0:
        return 0.0
    
    corr_matrix = np.corrcoef(rf_vals, perm_vals)
    return float(corr_matrix[0, 1])

def rank_features(importances: Dict[str, float]) -> List[Dict[str, Any]]:
    """Rank features by importance score."""
    sorted_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    return [
        {"rank": i + 1, "feature": name, "importance": score}
        for i, (name, score) in enumerate(sorted_features)
    ]

def calculate_vif(X: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature to detect multi-collinearity.
    
    VIF > 10 indicates high multi-collinearity.
    
    Args:
        X: DataFrame containing only feature columns (no target).
    
    Returns:
        Dictionary mapping feature names to their VIF scores.
    """
    if X.empty:
        raise ValueError("Feature DataFrame is empty.")
    
    # Add constant for intercept (required by VIF calculation)
    X_with_const = sm.add_constant(X)
    
    vif_data = {}
    features = X.columns
    
    for feature in features:
        # VIF for feature j is 1 / (1 - R_j^2)
        # R_j^2 is from regressing feature j on all other features
        vif = variance_inflation_factor(X_with_const.values, list(X_with_const.columns).index(feature))
        vif_data[feature] = float(vif)
    
    return vif_data

def main():
    """Main entry point for feature importance and VIF analysis."""
    paths = load_paths()
    data_dir = paths['data']
    evaluation_dir = data_dir / 'evaluation'
    processed_dir = data_dir / 'processed'
    
    # Ensure output directory exists
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    
    # Paths
    models_path = evaluation_dir / 'trained_models.pkl'
    data_path = processed_dir / 'computed_descriptors.csv'
    vif_output_path = evaluation_dir / 'vif_scores.json'
    
    # Load configuration
    logger.info(f"Loading models from {models_path}")
    try:
        models = load_models(models_path)
    except FileNotFoundError as e:
        logger.error(f"Models file missing: {e}")
        # Re-raise to fail loudly as per constraints
        raise
    
    logger.info(f"Loading data from {data_path}")
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    
    # Prepare features and target
    feature_cols = [col for col in df.columns if col not in ['formation_energy', 'material_id', 'structure_id']]
    if not feature_cols:
        raise ValueError("No feature columns found in dataset.")
    
    X = df[feature_cols]
    y = df['formation_energy']
    
    # 1. Extract RF Importances
    logger.info("Extracting Random Forest importances...")
    rf_model = models.get('random_forest')
    if rf_model is None:
        raise ValueError("Random Forest model not found in trained_models.pkl")
    
    rf_importances = extract_rf_importances(rf_model, feature_cols)
    
    # 2. Calculate Permutation Importance
    logger.info("Calculating Permutation Importance...")
    perm_importances = calculate_permutation_importance(rf_model, X, y, feature_cols)
    
    # 3. Validate Correlation
    logger.info("Validating correlation between methods...")
    corr = validate_correlation(rf_importances, perm_importances)
    logger.info(f"Correlation (r) between RF and Permutation importance: {corr:.4f}")
    
    if corr < CORRELATION_THRESHOLD:
        logger.warning(f"Correlation {corr:.4f} is below threshold {CORRELATION_THRESHOLD}. Features may be unstable.")
    
    # 4. Rank Features
    logger.info("Ranking features...")
    ranked_features = rank_features(rf_importances)
    
    # 5. Calculate VIF (Multi-Collinearity Check)
    logger.info("Calculating Variance Inflation Factor (VIF) for multi-collinearity...")
    vif_scores = calculate_vif(X)
    
    # Check for high VIF
    high_vif_features = {k: v for k, v in vif_scores.items() if v > VIF_THRESHOLD}
    if high_vif_features:
        logger.warning(f"High VIF detected (> {VIF_THRESHOLD}) for features: {list(high_vif_features.keys())}")
    else:
        logger.info(f"No features with VIF > {VIF_THRESHOLD} detected.")
    
    # 6. Save Outputs
    # Save VIF scores
    logger.info(f"Saving VIF scores to {vif_output_path}")
    with open(vif_output_path, 'w') as f:
        json.dump(vif_scores, f, indent=2)
    
    # Also save other relevant outputs if not already done by previous tasks
    # (Ensuring idempotency and completeness)
    
    # Save permutation importance and correlation
    perm_output_path = evaluation_dir / 'permutation_importance.json'
    with open(perm_output_path, 'w') as f:
        json.dump({
            "correlation_r": corr,
            "permutation_scores": perm_importances
        }, f, indent=2)
    
    # Save feature ranking
    ranking_output_path = evaluation_dir / 'feature_ranking.json'
    with open(ranking_output_path, 'w') as f:
        json.dump(ranked_features, f, indent=2)
    
    logger.info("Feature importance and VIF analysis completed successfully.")
    logger.info(f"VIF output saved to: {vif_output_path}")

if __name__ == "__main__":
    main()
