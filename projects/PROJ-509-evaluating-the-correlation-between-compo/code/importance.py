import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from scipy.stats import pearsonr
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import load_paths

logger = logging.getLogger(__name__)


def load_models(rf_path: Path) -> RandomForestRegressor:
    """Load the Random Forest model."""
    with open(rf_path, "rb") as f:
        return pickle.load(f)


def load_feature_names(input_path: Path) -> List[str]:
    """Load feature names from the processed dataset."""
    df = pd.read_csv(input_path)
    exclude = [
        "formula",
        "formula_pretty",
        "formation_energy_per_atom",
        "dominant_element",
    ]
    return [c for c in df.columns if c not in exclude]


def extract_rf_importances(
    model: RandomForestRegressor, feature_names: List[str]
) -> Dict[str, float]:
    """Extract feature importances from the RF model."""
    importances = model.feature_importances_
    return {name: float(imp) for name, imp in zip(feature_names, importances)}


def calculate_permutation_importance(
    model: RandomForestRegressor,
    X: pd.DataFrame,
    y: pd.Series,
    n_repeats: int = 10,
    random_state: int = 42,
) -> Dict[str, float]:
    """Calculate permutation importance."""
    result = permutation_importance(
        model, X, y, n_repeats=n_repeats, random_state=random_state, scoring="r2"
    )
    return {
        name: float(imp) for name, imp in zip(X.columns, result.importances_mean)
    }


def validate_correlation(
    imp1: Dict[str, float], imp2: Dict[str, float]
) -> Tuple[float, bool]:
    """Validate correlation between two importance dictionaries."""
    common_keys = set(imp1.keys()) & set(imp2.keys())
    if len(common_keys) < 2:
        return 0.0, False

    v1 = [imp1[k] for k in common_keys]
    v2 = [imp2[k] for k in common_keys]

    r, p = pearsonr(v1, v2)
    return float(r), r >= 0.8


def rank_features(
    importances: Dict[str, float], top_n: int = 10
) -> List[Dict[str, Any]]:
    """Rank features by importance."""
    sorted_items = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    return [{"feature": k, "importance": v} for k, v in sorted_items[:top_n]]


def calculate_vif(X: pd.DataFrame) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for each feature."""
    vif_data = {}
    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = float(vif)
    return vif_data


def main() -> None:
    """Main entry point for feature importance analysis."""
    logging.basicConfig(level=logging.INFO)
    paths = load_paths()

    # Load model and data
    rf_path = paths["data_evaluation"] / "model_rf.pkl"
    model = load_models(rf_path)

    input_path = paths["data_processed"] / "computed_descriptors.csv"
    df = pd.read_csv(input_path)

    feature_names = load_feature_names(input_path)
    X = df[feature_names]
    y = df["formation_energy_per_atom"]

    # Extract RF importances
    rf_imp = extract_rf_importances(model, feature_names)

    # Permutation importance
    perm_imp = calculate_permutation_importance(model, X, y)

    # Validate correlation
    r, passed = validate_correlation(rf_imp, perm_imp)
    logger.info(f"Correlation between RF and Permutation importance: {r:.4f}")

    # Save results
    perm_path = paths["data_evaluation"] / "permutation_importance.json"
    with open(perm_path, "w") as f:
        json.dump(
            {
                "correlation_r": r,
                "importance_correlation_pass": passed,
                "permutation_scores": perm_imp,
            },
            f,
            indent=2,
        )

    # Rank features
    ranked = rank_features(rf_imp)
    rank_path = paths["data_evaluation"] / "feature_ranking.json"
    with open(rank_path, "w") as f:
        json.dump(ranked, f, indent=2)

    # VIF
    vif_scores = calculate_vif(X)
    vif_path = paths["data_evaluation"] / "vif_scores.json"
    with open(vif_path, "w") as f:
        json.dump(vif_scores, f, indent=2)

    logger.info("Feature importance analysis complete")


if __name__ == "__main__":
    main()
