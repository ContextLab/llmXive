"""
Collinearity analysis and VIF calculation.
Computes Variance Inflation Factor (VIF) for predictors to detect multicollinearity.
"""
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
import yaml
from pathlib import Path

from config import get_vif_threshold, get_data_processed_dir

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    VIF = 1 / (1 - R^2) where R^2 is from regressing feature i against all other features.
    
    Args:
        df: DataFrame containing the features.
        feature_cols: List of column names to calculate VIF for.
        
    Returns:
        Dictionary mapping feature names to their VIF values.
    """
    vif_values = {}
    
    # Filter dataframe to only include requested features
    X = df[feature_cols].copy()
    
    for i, feature in enumerate(feature_cols):
        # Create X matrix with all features except current
        X_regress = X.drop(columns=[feature])
        y = X[feature]
        
        # Add intercept
        X_regress['intercept'] = 1.0
        
        # Check for perfect collinearity or insufficient samples
        if X_regress.shape[1] > X_regress.shape[0]:
            logger.warning(f"More features than samples for VIF calculation of {feature}")
            vif_values[feature] = float('inf')
            continue
        
        # Check for constant features (zero variance)
        if y.std() < 1e-10:
            logger.warning(f"Feature {feature} has near-zero variance, VIF undefined")
            vif_values[feature] = float('inf')
            continue
        
        # Calculate R^2 using OLS
        try:
            XtX = X_regress.T @ X_regress
            
            # Check for singularity
            if np.linalg.matrix_rank(XtX) < XtX.shape[0]:
                vif_values[feature] = float('inf')
                continue
            
            XtX_inv = np.linalg.inv(XtX)
            Xty = X_regress.T @ y
            beta = XtX_inv @ Xty
            
            y_pred = X_regress @ beta
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - y.mean()) ** 2)
            
            if ss_tot == 0:
                r_squared = 0
            else:
                r_squared = 1 - (ss_res / ss_tot)
            
            # Avoid division by zero
            if r_squared >= 1.0 - 1e-10:
                vif_values[feature] = float('inf')
            else:
                vif_values[feature] = 1.0 / (1.0 - r_squared)
                
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {feature}: {e}")
            vif_values[feature] = float('inf')
    
    return vif_values

def get_collinear_features(vif_results: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Get list of features with VIF >= threshold.
    
    Args:
        vif_results: Dictionary of VIF values.
        threshold: VIF threshold for flagging collinearity.
        
    Returns:
        List of feature names with high VIF.
    """
    return [f for f, vif in vif_results.items() if vif >= threshold]

def remove_collinear_features(df: pd.DataFrame, feature_cols: List[str], 
                             vif_results: Dict[str, float], threshold: float = 5.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Remove features with high VIF from dataframe and return updated list of features.
    
    Args:
        df: Original DataFrame.
        feature_cols: Original list of feature columns.
        vif_results: Dictionary of VIF values.
        threshold: VIF threshold.
        
    Returns:
        Tuple of (reduced DataFrame, list of remaining feature names).
    """
    collinear = get_collinear_features(vif_results, threshold)
    remaining = [f for f in feature_cols if f not in collinear]
    return df[remaining], remaining

def save_vif_report(vif_results: Dict[str, float], output_path: str, threshold: float = 5.0):
    """
    Save VIF results to a YAML report.
    
    Args:
        vif_results: Dictionary of VIF values.
        output_path: Path to save the YAML report.
        threshold: VIF threshold used for flagging.
    """
    report = {
        "vif_scores": {k: float(v) if not np.isinf(v) else "inf" for k, v in vif_results.items()},
        "threshold": threshold,
        "collinear_features": get_collinear_features(vif_results, threshold),
        "is_collinear": any(v >= threshold for v in vif_results.values())
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(report, f, default_flow_style=False)
    
    logger.info(f"VIF report saved to {output_path}")

def main():
    """
    Main entry point to run VIF analysis on the cleaned dataset.
    Reads descriptors from data/processed/descriptors.csv and writes report to data/processed/vif_report.yaml.
    """
    logger.info("Starting VIF analysis on descriptor features")
    
    # Load descriptors
    descriptors_path = get_data_processed_dir() / "descriptors.csv"
    if not descriptors_path.exists():
        logger.error(f"Descriptors file not found: {descriptors_path}")
        raise FileNotFoundError(f"Required input file not found: {descriptors_path}")
    
    df = pd.read_csv(descriptors_path)
    
    # Identify feature columns (exclude metadata like 'hardness_hv', 'alloy_family', 'source_citation')
    exclude_cols = ['hardness_hv', 'alloy_family', 'source_citation', 'sample_id']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        logger.error("No feature columns found in descriptors.csv")
        raise ValueError("No feature columns found in descriptors.csv")
    
    logger.info(f"Calculating VIF for {len(feature_cols)} features: {feature_cols}")
    
    # Calculate VIF
    vif_results = calculate_vif(df, feature_cols)
    
    # Log results
    for feature, vif in vif_results.items():
        status = "HIGH" if vif >= 5.0 else "OK"
        logger.info(f"  {feature}: VIF = {vif:.2f} [{status}]")
    
    # Save report
    threshold = get_vif_threshold()
    output_path = get_data_processed_dir() / "vif_report.yaml"
    save_vif_report(vif_results, str(output_path), threshold)
    
    # Log collinear features
    collinear = get_collinear_features(vif_results, threshold)
    if collinear:
        logger.warning(f"Found {len(collinear)} collinear features (VIF >= {threshold}): {collinear}")
    else:
        logger.info("No collinear features found (all VIF < 5.0)")
    
    logger.info("VIF analysis completed successfully")

if __name__ == "__main__":
    main()