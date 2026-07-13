"""
Collinearity analysis for feature selection.

Provides tools for calculating Variance Inflation Factor (VIF)
and identifying/removing collinear features.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import get_vif_threshold

logger = logging.getLogger(__name__)

def calculate_vif(X: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    VIF measures how much the variance of an estimated regression coefficient
    increases because of collinearity.
    
    Args:
        X: DataFrame of features (numeric columns only).
    
    Returns:
        Dict mapping feature names to their VIF scores.
    """
    # Select only numeric columns
    X_numeric = X.select_dtypes(include=[np.number])
    
    if X_numeric.shape[1] == 0:
        logger.warning("No numeric columns found in input DataFrame")
        return {}
    
    if X_numeric.shape[1] == 1:
        # VIF is undefined for a single feature
        return {X_numeric.columns[0]: 1.0}
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X_numeric)
    
    vif_scores = {}
    for i, col in enumerate(X_with_const.columns):
        if col == 'const':
            continue
        
        try:
            vif = variance_inflation_factor(X_with_const.values, i)
            vif_scores[col] = vif
        except Exception as e:
            logger.error(f"Could not calculate VIF for {col}: {e}")
            vif_scores[col] = np.nan

    return vif_scores

def get_collinear_features(vif_scores: Dict[str, float], threshold: Optional[float] = None) -> List[str]:
    """
    Identify features with VIF above the threshold.
    
    Args:
        vif_scores: Dictionary of feature VIF scores.
        threshold: VIF threshold for flagging collinearity. Defaults to config value.
    
    Returns:
        List of feature names with VIF >= threshold.
    """
    if threshold is None:
        threshold = get_vif_threshold()
    
    collinear = [
        feature for feature, vif in vif_scores.items()
        if not np.isnan(vif) and vif >= threshold
    ]
    
    if collinear:
        logger.warning(
            f"Found {len(collinear)} features with VIF >= {threshold}: {collinear}"
        )
    
    return collinear

def remove_collinear_features(
    X: pd.DataFrame,
    threshold: Optional[float] = None,
    keep_first: bool = True
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Remove collinear features from the DataFrame.
    
    Iteratively removes features with the highest VIF until all remaining
    features have VIF below the threshold.
    
    Args:
        X: DataFrame of features.
        threshold: VIF threshold. Defaults to config value.
        keep_first: If True, keep the first feature when multiple are collinear.
                   If False, remove all collinear features.
    
    Returns:
        Tuple of (cleaned DataFrame, list of removed feature names).
    """
    if threshold is None:
        threshold = get_vif_threshold()
    
    X_clean = X.copy()
    removed_features = []
    
    while True:
        vif_scores = calculate_vif(X_clean)
        
        if not vif_scores:
            break
        
        max_vif_feature = max(vif_scores, key=vif_scores.get)
        max_vif = vif_scores[max_vif_feature]
        
        if max_vif < threshold:
            break
        
        if keep_first:
            # Remove the feature with the highest VIF
            X_clean = X_clean.drop(columns=[max_vif_feature])
            removed_features.append(max_vif_feature)
            logger.info(f"Removed {max_vif_feature} (VIF={max_vif:.2f}) due to collinearity")
        else:
            # Remove all features with VIF >= threshold
            collinear = get_collinear_features(vif_scores, threshold)
            if not collinear:
                break
            X_clean = X_clean.drop(columns=collinear)
            removed_features.extend(collinear)
            logger.info(f"Removed {len(collinear)} collinear features: {collinear}")
            break
    
    return X_clean, removed_features

def main():
    """
    Main function to demonstrate collinearity analysis.
    Reads from data/processed/solder_hardness_validated.csv if it exists,
    otherwise uses synthetic data for demonstration.
    """
    import logging
    import os
    from pathlib import Path
    
    logging.basicConfig(level=logging.INFO)
    
    # Try to load real data first
    data_path = Path("data/processed/solder_hardness_validated.csv")
    if data_path.exists():
        logger.info(f"Loading real data from {data_path}")
        df = pd.read_csv(data_path)
        
        # Select feature columns (exclude target 'hardness' and composition columns if any)
        # Assuming the processed data has descriptor columns like 'clr_sn', 'clr_ag', etc.
        feature_cols = [c for c in df.columns if c.startswith('clr_') or c in ['weighted_mean_atomic_mass', 'electronegativity_variance', 'atomic_radius_variance', 'weighted_avg_melting_point', 'valence_electron_concentration']]
        
        if not feature_cols:
            logger.warning("No descriptor columns found in data. Using synthetic data.")
            feature_cols = None
        else:
            X = df[feature_cols].dropna()
    else:
        logger.warning("Real data file not found. Using synthetic data for demonstration.")
        feature_cols = None
    
    if feature_cols is None or X.empty:
        # Fallback to synthetic data
        np.random.seed(42)
        n_samples = 100
        
        X = pd.DataFrame({
            'feature_a': np.random.randn(n_samples),
            'feature_b': np.random.randn(n_samples),
            'feature_c': np.random.randn(n_samples),
        })
        
        # Create a collinear feature
        X['feature_d'] = X['feature_a'] * 2 + np.random.randn(n_samples) * 0.1
    
    print(f"\nAnalyzing VIF for {X.shape[1]} features:")
    print(X.columns.tolist())
    
    vif_scores = calculate_vif(X)
    print("\nVIF Scores:")
    for feature, vif in vif_scores.items():
        print(f"  {feature}: {vif:.2f}")
    
    collinear = get_collinear_features(vif_scores)
    print(f"\nCollinear features (VIF >= {get_vif_threshold()}): {collinear}")
    
    cleaned_X, removed = remove_collinear_features(X)
    print(f"\nRemoved features: {removed}")
    print("Remaining features:")
    print(cleaned_X.columns.tolist())
    
    # Save report to data/processed if running in project context
    try:
        output_path = Path("data/processed/collinearity_report.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            "vif_scores": {k: float(v) for k, v in vif_scores.items()},
            "collinear_features": collinear,
            "removed_features": removed,
            "threshold": get_vif_threshold()
        }
        
        import json
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nCollinearity report saved to {output_path}")
    except Exception as e:
        logger.warning(f"Could not save collinearity report: {e}")

if __name__ == "__main__":
    main()