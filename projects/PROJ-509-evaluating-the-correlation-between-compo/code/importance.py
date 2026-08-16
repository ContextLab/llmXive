import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.inspection import permutation_importance
from scipy.stats import pearsonr
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import load_paths
from utils.logging import get_logger

logger = get_logger(__name__)

def load_models(model_path: Path) -> Dict[str, Any]:
    """Load trained models.
    
    Args:
        model_path: Path to model files.
        
    Returns:
        Dictionary of models.
    """
    models = {}
    rf_path = model_path / "model_rf.pkl"
    if rf_path.exists():
        with open(rf_path, "rb") as f:
            models["rf"] = pickle.load(f)
    return models

def load_feature_names(data_path: Path) -> List[str]:
    """Load feature names from processed dataset.
    
    Args:
        data_path: Path to processed CSV.
        
    Returns:
        List of feature names.
    """
    df = pd.read_csv(data_path)
    return [c for c in df.columns if c not in ["composition", "formation_energy"]]

def extract_rf_importances(
    model: Any,
    feature_names: List[str]
) -> Dict[str, float]:
    """Extract feature importances from Random Forest.
    
    Args:
        model: Trained Random Forest model.
        feature_names: List of feature names.
        
    Returns:
        Dictionary mapping feature names to importances.
    """
    importances = model.feature_importances_
    return dict(zip(feature_names, importances))

def calculate_permutation_importance(
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    n_repeats: int = 10,
    random_state: int = 42
) -> Dict[str, float]:
    """Calculate permutation importance.
    
    Args:
        model: Trained model.
        X: Feature matrix.
        y: Target vector.
        n_repeats: Number of repeats.
        random_state: Random seed.
        
    Returns:
        Dictionary of permutation importances.
    """
    result = permutation_importance(
        model, X, y, n_repeats=n_repeats,
        random_state=random_state, scoring="r2"
    )
    return dict(zip(X.columns, result.importances_mean))

def validate_correlation(
    imp1: Dict[str, float],
    imp2: Dict[str, float]
) -> Tuple[float, float, bool]:
    """Validate correlation between two importance vectors.
    
    Args:
        imp1: First importance dictionary.
        imp2: Second importance dictionary.
        
    Returns:
        Tuple of (correlation, p_value, passed).
    """
    common_keys = set(imp1.keys()).intersection(imp2.keys())
    if len(common_keys) < 2:
        return 0.0, 1.0, False
    
    v1 = [imp1[k] for k in common_keys]
    v2 = [imp2[k] for k in common_keys]
    
    r, p = pearsonr(v1, v2)
    return r, p, r >= 0.8

def rank_features(
    importances: Dict[str, float],
    top_n: int = 10
) -> List[Tuple[str, float]]:
    """Rank features by importance.
    
    Args:
        importances: Feature importances.
        top_n: Number of top features to return.
        
    Returns:
        List of (feature, importance) tuples.
    """
    sorted_items = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    return sorted_items[:top_n]

def calculate_vif(
    X: pd.DataFrame,
    feature_names: List[str]
) -> Dict[str, float]:
    """Calculate Variance Inflation Factors.
    
    Args:
        X: Feature matrix.
        feature_names: List of feature names.
        
    Returns:
        Dictionary of VIF scores.
    """
    vif_data = {}
    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
    return vif_data

def main() -> None:
    """Main entry point for feature importance analysis."""
    paths = load_paths()
    
    # Load model and data
    model_path = paths["data_evaluation"]
    data_path = paths["data_processed"] / "computed_descriptors.csv"
    
    models = load_models(model_path)
    if "rf" not in models:
        raise RuntimeError("Random Forest model not found")
    
    feature_names = load_feature_names(data_path)
    df = pd.read_csv(data_path)
    X = df[feature_names]
    y = df["formation_energy"]
    
    # Extract importances
    rf_imp = extract_rf_importances(models["rf"], feature_names)
    
    # Permutation importance
    perm_imp = calculate_permutation_importance(models["rf"], X, y)
    
    # Validate correlation
    r, p, passed = validate_correlation(rf_imp, perm_imp)
    
    # Save results
    results = {
        "correlation_r": r,
        "p_value": p,
        "importance_correlation_pass": passed,
        "permutation_importance": perm_imp,
        "feature_ranking": rank_features(rf_imp)
    }
    
    output_path = paths["data_evaluation"] / "permutation_importance.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Calculate VIF
    vif_scores = calculate_vif(X, feature_names)
    vif_path = paths["data_evaluation"] / "vif_scores.json"
    with open(vif_path, "w") as f:
        json.dump(vif_scores, f, indent=2)
    
    logger.info(f"Feature importance results saved to {output_path}")

if __name__ == "__main__":
    main()
