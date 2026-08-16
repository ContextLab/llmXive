"""
Model utility functions for the perovskite stability prediction pipeline.

This module provides helper functions for model evaluation and interpretation,
including permutation importance calculation.
"""
import numpy as np
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, List, Union, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def calculate_permutation_importance(
    model,
    X: Union[np.ndarray, List],
    y: Union[np.ndarray, List],
    feature_names: Optional[List[str]] = None,
    n_repeats: int = 10,
    random_state: int = 42,
    scoring: Optional[str] = 'neg_mean_squared_error'
) -> Dict[str, float]:
    """
    Calculate permutation importance for a trained model.
    
    Permutation importance measures the decrease in a model's performance
    when a single feature's values are randomly shuffled. A feature is
    considered important if shuffling its values decreases the model
    performance (increases error).
    
    Parameters
    ----------
    model : sklearn estimator
        A trained scikit-learn model with a predict method.
    X : array-like of shape (n_samples, n_features)
        The input samples.
    y : array-like of shape (n_samples,)
        The target values.
    feature_names : list of str, optional
        Names of the features. If None, feature indices are used as names.
    n_repeats : int, default=10
        Number of times to permute a feature.
    random_state : int, default=42
        Pseudo-random number generator seed.
    scoring : str, default='neg_mean_squared_error'
        Scoring strategy to use for permutation importance.
        
    Returns
    -------
    dict
        Dictionary mapping feature names to their mean importance scores
        (higher values indicate more important features).
        
    Raises
    ------
    ValueError
        If feature_names length does not match number of features in X.
    """
    # Convert inputs to numpy arrays if they aren't already
    X = np.array(X)
    y = np.array(y)
    
    # Validate input dimensions
    if X.ndim != 2:
        raise ValueError(f"X must be 2-dimensional, got {X.ndim} dimensions")
        
    n_features = X.shape[1]
    
    # Generate feature names if not provided
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    elif len(feature_names) != n_features:
        raise ValueError(
            f"feature_names length ({len(feature_names)}) does not match "
            f"number of features in X ({n_features})"
        )
    
    logger.info(
        f"Calculating permutation importance with {n_repeats} repeats "
        f"for {n_features} features"
    )
    
    # Calculate permutation importance
    perm_importance = permutation_importance(
        model,
        X,
        y,
        n_repeats=n_repeats,
        random_state=random_state,
        scoring=scoring
    )
    
    # Convert to dictionary with feature names as keys
    # Note: permutation_importance returns mean decrease in score (negative for regression)
    # We return the mean importance (which is negative of the decrease in performance)
    importance_dict = {}
    for i, name in enumerate(feature_names):
        # Use mean importance (positive values mean the feature is important)
        importance_dict[name] = float(perm_importance.importances_mean[i])
        
    logger.info(
        f"Permutation importance calculated. Top features: "
        f"{sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:3]}"
    )
    
    return importance_dict