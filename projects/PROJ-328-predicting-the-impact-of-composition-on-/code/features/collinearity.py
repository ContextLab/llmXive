"""
Collinearity Analysis Module.
Provides Variance Inflation Factor (VIF) calculations and feature selection logic.
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from utils.logging_config import get_logger
from pathlib import Path
import yaml

logger = get_logger(__name__)

def calculate_vif(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each numeric column in a DataFrame.

    Args:
        df: DataFrame containing numeric features.
        exclude_cols: List of column names to exclude from VIF calculation.

    Returns:
        Dictionary mapping column names to their VIF scores.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty")

    cols = df.columns.tolist()
    if exclude_cols:
        cols = [c for c in cols if c not in exclude_cols]

    X = df[cols].dropna()
    if X.empty:
        logger.warning("No valid data after dropping NaNs for VIF calculation")
        return {c: np.inf for c in cols}

    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    vif_data = {}
    for col in cols:
        try:
            vif = variance_inflation_factor(X_with_const.values, X_with_const.columns.get_loc(col))
            vif_data[col] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = np.inf

    return vif_data

def get_collinear_features(vif_scores: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Identify features with VIF above a threshold.

    Args:
        vif_scores: Dictionary of VIF scores from calculate_vif.
        threshold: VIF threshold for flagging collinearity (default 5.0).

    Returns:
        List of feature names flagged as collinear.
    """
    return [col for col, vif in vif_scores.items() if vif >= threshold]

def remove_collinear_features(df: pd.DataFrame, vif_scores: Dict[str, float], threshold: float = 5.0) -> pd.DataFrame:
    """
    Remove features flagged as collinear from a DataFrame.

    Args:
        df: Original DataFrame.
        vif_scores: Dictionary of VIF scores.
        threshold: VIF threshold.

    Returns:
        DataFrame with collinear features removed.
    """
    collinear = get_collinear_features(vif_scores, threshold)
    cols_to_keep = [c for c in df.columns if c not in collinear]
    logger.info(f"Removing collinear features: {collinear}. Keeping: {cols_to_keep}")
    return df[cols_to_keep]

def save_vif_report(vif_scores: Dict[str, float], output_path: str, threshold: float = 5.0) -> None:
    """
    Save VIF analysis results to a YAML report.

    Args:
        vif_scores: Dictionary of VIF scores.
        output_path: Path to save the YAML report.
        threshold: Threshold used for collinearity flagging.
    """
    report = {
        "threshold": threshold,
        "features": []
    }
    
    sorted_vif = sorted(vif_scores.items(), key=lambda x: x[1], reverse=True)
    
    for feat, vif in sorted_vif:
        report["features"].append({
            "feature_name": feat,
            "vif_score": float(vif) if not np.isinf(vif) else "inf",
            "is_collinear": vif >= threshold
        })

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"VIF report saved to {output_path}")

def main():
    """
    Main entry point for testing collinearity analysis.
    """
    logger.info("Starting Collinearity Analysis test")
    
    # Create dummy data
    data = {
        'feature_a': [1.0, 2.0, 3.0, 4.0, 5.0],
        'feature_b': [2.0, 4.0, 6.0, 8.0, 10.0],  # Perfectly correlated with A
        'feature_c': [1.0, 0.5, 0.2, 0.1, 0.05],
        'clr_sn': [0.1, 0.2, 0.3, 0.4, 0.5],
        'clr_ag': [0.05, 0.1, 0.15, 0.2, 0.25]
    }
    df = pd.DataFrame(data)

    vif_scores = calculate_vif(df)
    logger.info(f"VIF Scores: {vif_scores}")

    collinear = get_collinear_features(vif_scores, threshold=5.0)
    logger.info(f"Collinear features: {collinear}")

    save_vif_report(vif_scores, 'data/processed/vif_report.yaml', threshold=5.0)
    
    logger.info("Collinearity Analysis test completed successfully")

if __name__ == "__main__":
    main()