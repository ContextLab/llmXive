"""
Collinearity module for Variance Inflation Factor (VIF) calculations.
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
import yaml
from pathlib import Path
from statsmodels.stats.outliers_influence import variance_inflation_factor
from utils.logging_config import get_logger

logger = get_logger(__name__)

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Calculate VIF for a list of features.
    
    Args:
        df: DataFrame containing the features.
        feature_cols: List of column names to calculate VIF for.
        
    Returns:
        Dictionary mapping feature names to VIF scores.
    """
    if len(feature_cols) == 0:
        return {}
    
    X = df[feature_cols].values
    
    # Add constant for intercept if needed, but VIF calculation in statsmodels
    # usually expects the design matrix. We calculate for each column.
    vif_scores = {}
    for i, col in enumerate(feature_cols):
        vif = variance_inflation_factor(X, i)
        vif_scores[col] = float(vif)
        
    return vif_scores

def get_collinear_features(vif_scores: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Identify features with VIF >= threshold.
    """
    return [col for col, score in vif_scores.items() if score >= threshold]

def remove_collinear_features(df: pd.DataFrame, vif_scores: Dict[str, float], threshold: float = 5.0) -> pd.DataFrame:
    """
    Return a DataFrame with collinear features removed (highest VIF first iteratively).
    Simple implementation: remove all features above threshold at once.
    """
    collinear = get_collinear_features(vif_scores, threshold)
    cols_to_keep = [c for c in df.columns if c not in collinear]
    return df[cols_to_keep]

def save_vif_report(vif_scores: Dict[str, float], output_path: str, threshold: float = 5.0):
    """
    Save VIF report to YAML.
    """
    report = {
        "threshold": threshold,
        "features": []
    }
    
    for col, score in sorted(vif_scores.items(), key=lambda x: x[1], reverse=True):
        is_collinear = score >= threshold
        report["features"].append({
            "name": col,
            "vif_score": round(score, 4),
            "is_collinear": is_collinear
        })
    
    with open(output_path, 'w') as f:
        yaml.dump(report, f, default_flow_style=False)
    logger.info(f"VIF report saved to {output_path}")

def main():
    """
    Main entry point.
    Reads descriptors, calculates VIF, and saves report.
    """
    logger.info("Starting VIF Analysis Pipeline")
    
    input_path = Path("data/processed/descriptors.csv")
    output_path = Path("data/processed/vif_report.yaml")
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Run Descriptor Engine first."
        )
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    
    # Select feature columns (exclude any target if present, though descriptors are just features)
    feature_cols = list(df.columns)
    
    if not feature_cols:
        logger.warning("No feature columns found in descriptors.")
        return
    
    vif_scores = calculate_vif(df, feature_cols)
    
    # Save report
    save_vif_report(vif_scores, str(output_path), threshold=5.0)
    
    collinear = get_collinear_features(vif_scores)
    if collinear:
        logger.warning(f"Collinear features detected (VIF >= 5): {collinear}")
    else:
        logger.info("No collinear features detected.")
        
    logger.info("VIF Analysis Pipeline completed successfully")

if __name__ == "__main__":
    main()
