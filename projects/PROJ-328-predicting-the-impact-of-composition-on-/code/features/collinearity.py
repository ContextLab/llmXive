"""
Collinearity Analysis Module.

Calculates Variance Inflation Factors (VIF) to detect multicollinearity
among features and provides utilities to remove them.
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple

import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from utils.logging_config import get_logger

logger = get_logger(__name__)


def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each feature.

    Args:
        df: DataFrame containing the features.
        features: List of column names to calculate VIF for.

    Returns:
        Dictionary mapping feature names to their VIF scores.
    """
    X = df[features].values
    # Add constant for intercept
    X_with_const = sm.add_constant(X)

    vif_scores = {}
    for i, col in enumerate(features):
        # VIF for feature i is calculated using the other features
        # statsmodels VIF function takes the matrix with constant
        # We need to calculate VIF for each column in X (excluding constant)
        # The VIF for the i-th feature is 1 / (1 - R^2_i) where R^2_i is from regressing X_i on all other X_j
        # statsmodels variance_inflation_factor handles this if passed the matrix with constant
        # and the index of the column (0 is constant, so feature i is at i+1)
        try:
            vif = variance_inflation_factor(X_with_const, i + 1)
            vif_scores[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_scores[col] = np.nan

    return vif_scores


def get_collinear_features(vif_scores: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Identify features with VIF above the threshold.

    Args:
        vif_scores: Dictionary of VIF scores.
        threshold: VIF threshold for collinearity.

    Returns:
        List of feature names considered collinear.
    """
    return [feat for feat, vif in vif_scores.items() if vif >= threshold]


def remove_collinear_features(df: pd.DataFrame, vif_scores: Dict[str, float], threshold: float = 5.0) -> pd.DataFrame:
    """
    Remove features with VIF above the threshold.
    Iteratively removes the feature with the highest VIF until all are below threshold.

    Args:
        df: DataFrame with features.
        vif_scores: Initial VIF scores.
        threshold: VIF threshold.

    Returns:
        DataFrame with collinear features removed.
    """
    current_features = list(df.columns)
    current_vif = vif_scores.copy()

    while True:
        collinear = get_collinear_features(current_vif, threshold)
        if not collinear:
            break

        # Find the feature with the highest VIF
        max_vif_feat = max(collinear, key=lambda x: current_vif[x])
        logger.info(f"Removing feature '{max_vif_feat}' with VIF {current_vif[max_vif_feat]:.2f}")

        # Remove from list and recalculate
        current_features.remove(max_vif_feat)
        del current_vif[max_vif_feat]

        # Recalculate VIF for remaining features
        if len(current_features) > 1:
            current_vif = calculate_vif(df[current_features], current_features)
        else:
            break

    return df[current_features]


def main():
    """
    Main entry point for standalone collinearity analysis.
    Loads the descriptor-enhanced dataset, calculates VIF, and reports.
    """
    from seed import init_reproducibility
    from config import get_data_outputs_dir, get_vif_threshold
    import json

    init_reproducibility()

    output_dir = get_data_outputs_dir()
    input_file = output_dir / "solder_hardness_with_descriptors.csv"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}. Run descriptor engine first.")
        return

    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)

    # Identify descriptor columns (exclude composition and target)
    # Heuristic: columns not in original composition set and not 'hardness'
    # We'll assume the last few columns are descriptors
    # Or we can filter by known descriptor names
    possible_descriptors = [
        "weighted_mean_atomic_mass",
        "weighted_mean_electronegativity",
        "electronegativity_variance",
        "atomic_radius_variance",
        "weighted_avg_melting_point",
        "weighted_valence_electron_concentration"
    ]

    feature_cols = [c for c in possible_descriptors if c in df.columns]

    if not feature_cols:
        logger.warning("No descriptor columns found for VIF analysis.")
        return

    logger.info(f"Analyzing VIF for features: {feature_cols}")

    vif_scores = calculate_vif(df, feature_cols)
    threshold = get_vif_threshold()

    logger.info(f"VIF Scores (Threshold: {threshold}):")
    for feat, score in vif_scores.items():
        flag = " [COLLINEAR]" if score >= threshold else ""
        logger.info(f"  {feat}: {score:.4f}{flag}")

    collinear = get_collinear_features(vif_scores, threshold)
    if collinear:
        logger.warning(f"Collinear features found: {collinear}")
        clean_df = remove_collinear_features(df, vif_scores, threshold)
        clean_df.to_csv(output_dir / "solder_hardness_clean_features.csv", index=False)
        logger.info(f"Saved cleaned dataset to {output_dir / 'solder_hardness_clean_features.csv'}")
    else:
        logger.info("No collinear features found.")

    # Save VIF report
    report = {
        "threshold": threshold,
        "vif_scores": vif_scores,
        "collinear_features": collinear
    }
    with open(output_dir / "vif_report.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    main()
