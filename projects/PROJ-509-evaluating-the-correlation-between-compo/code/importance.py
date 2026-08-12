import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
from sklearn.inspection import permutation_importance
from scipy.stats import pearsonr
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import load_paths
from utils.logging import get_logger
from utils.io import load_dataframe_safely

logger = get_logger(__name__)

def load_models(models_dir: Path) -> Dict[str, Any]:
    """
    Loads pre-trained models from a directory.
    """
    models = {}
    for model_file in models_dir.glob("model_*.pkl"):
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
            name = model_file.stem.replace("model_", "")
            models[name] = model
    return models

def load_feature_names(input_path: Path) -> List[str]:
    """
    Loads feature names from the dataset header.
    """
    df = pd.read_csv(input_path, nrows=0)
    return list(df.columns)

def extract_rf_importances(
    model: Any,
    feature_names: List[str]
) -> Dict[str, float]:
    """
    Extracts feature importances from a Random Forest model.
    """
    importances = model.feature_importances_
    return dict(zip(feature_names, importances))

def calculate_permutation_importance(
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    scoring: str = 'r2',
    n_repeats: int = 10,
    random_state: int = 42
) -> Dict[str, float]:
    """
    Calculates permutation importance.
    """
    result = permutation_importance(
        model, X, y,
        scoring=scoring,
        n_repeats=n_repeats,
        random_state=random_state
    )
    return dict(zip(X.columns, result.importances_mean))

def validate_correlation(
    imp1: Dict[str, float],
    imp2: Dict[str, float]
) -> Tuple[float, bool]:
    """
    Validates correlation between two importance dictionaries.
    """
    keys = sorted(set(imp1.keys()) & set(imp2.keys()))
    if len(keys) < 2:
        return 0.0, False
    
    v1 = [imp1[k] for k in keys]
    v2 = [imp2[k] for k in keys]
    
    r, p = pearsonr(v1, v2)
    return r, r >= 0.8

def rank_features(
    importances: Dict[str, float],
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Ranks features by importance.
    """
    sorted_items = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    return [
        {"feature": k, "importance": v}
        for k, v in sorted_items[:top_n]
    ]

def calculate_vif(
    df: pd.DataFrame,
    feature_cols: List[str]
) -> Dict[str, float]:
    """
    Calculates Variance Inflation Factor for each feature.
    """
    vif_data = {}
    for i, col in enumerate(feature_cols):
        X = df[feature_cols]
        y = df[col]  # Not used, but needed for VIF calculation context
        # VIF is calculated for each feature against others
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = vif
        except Exception:
            vif_data[col] = np.inf
    return vif_data

def main() -> None:
    """
    Main entry point for the importance script.
    """
    paths = load_paths()
    models_dir = paths['evaluation']
    data_path = paths['computed_descriptors']
    output_dir = paths['evaluation']
    
    # Load models
    models = load_models(models_dir)
    if 'rf' not in models:
        logger.error("Random Forest model not found.")
        sys.exit(1)
    
    # Load data
    df = load_data(data_path)
    if df is None:
        logger.error("Failed to load data.")
        sys.exit(1)
    
    feature_cols = [
        "mean_electronegativity", "variance_electronegativity",
        "mean_radius", "variance_radius",
        "mean_valence", "variance_valence",
        "mean_melting_point", "variance_melting_point",
        "mean_ionization_energy", "variance_ionization_energy"
    ]
    
    # Extract RF importances
    rf_importances = extract_rf_importances(models['rf'], feature_cols)
    
    # Calculate permutation importance
    X = df[feature_cols]
    y = df['formation_energy']
    perm_importances = calculate_permutation_importance(models['rf'], X, y)
    
    # Validate correlation
    r, passed = validate_correlation(rf_importances, perm_importances)
    
    # Rank features
    ranked_features = rank_features(rf_importances)
    
    # Calculate VIF
    vif_scores = calculate_vif(df, feature_cols)
    
    # Save results
    ranking_path = output_dir / "feature_ranking.json"
    with open(ranking_path, 'w') as f:
        json.dump(ranked_features, f, indent=2)
    
    perm_path = output_dir / "permutation_importance.json"
    perm_data = {
        "correlation_r": r,
        "importance_correlation_pass": passed,
        "permutation_importances": perm_importances
    }
    with open(perm_path, 'w') as f:
        json.dump(perm_data, f, indent=2)
    
    vif_path = output_dir / "vif_scores.json"
    with open(vif_path, 'w') as f:
        json.dump(vif_scores, f, indent=2)
    
    logger.info("Feature importance analysis complete.")

if __name__ == "__main__":
    from utils.logging import setup_logging
    setup_logging()
    main()
