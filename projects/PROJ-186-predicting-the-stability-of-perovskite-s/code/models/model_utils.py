"""
Utility functions for model evaluation and interpretation.

This module provides functions for calculating permutation importance,
which is used to validate feature importance hypotheses (T028).
"""
import numpy as np
from sklearn.inspection import permutation_result
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, List, Union, Optional
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

def calculate_permutation_importance(
    model,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    n_repeats: int = 5,
    random_state: int = 42,
    scoring: str = 'neg_mean_squared_error'
) -> Dict[str, float]:
    """
    Calculate permutation importance for a trained model.
    
    Permutation importance measures the decrease in a model's performance 
    when a single feature value is randomly shuffled. This breaks the 
    relationship between the feature and the target, allowing us to 
    quantify the feature's importance.
    
    Args:
        model: A trained scikit-learn estimator.
        X: Feature matrix (n_samples, n_features).
        y: Target vector (n_samples,).
        feature_names: List of feature names corresponding to columns in X.
        n_repeats: Number of times to permute a feature.
        random_state: Random seed for reproducibility.
        scoring: Scoring strategy to use. Default is MSE.
        
    Returns:
        A dictionary mapping feature names to their mean permutation importance scores.
        
    Raises:
        ValueError: If feature_names length does not match X columns.
    """
    if len(feature_names) != X.shape[1]:
        raise ValueError(
            f"Length of feature_names ({len(feature_names)}) must match "
            f"number of features in X ({X.shape[1]})"
        )
    
    logger.info(f"Calculating permutation importance with {n_repeats} repeats...")
    
    try:
        result = permutation_result(
            model, X, y, n_repeats=n_repeats, 
            random_state=random_state, scoring=scoring
        )
        
        # permutation_result returns mean and std across repeats
        # We return the mean importance (negative mean squared error change)
        # A positive value means the feature is important (shuffling it hurt performance)
        importance_scores = result.importances_mean
        
        importance_dict = {
            name: float(score) 
            for name, score in zip(feature_names, importance_scores)
        }
        
        logger.info(f"Permutation importance calculated for {len(feature_names)} features.")
        return importance_dict
        
    except Exception as e:
        logger.error(f"Error calculating permutation importance: {e}")
        raise