"""
Collinearity analysis using Variance Inflation Factor (VIF).

Identifies and flags highly correlated predictors in feature sets.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from utils.logging_config import get_logger
from config import get_config

logger = get_logger(__name__)
config = get_config()

def calculate_vif(X: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each feature.
    
    Args:
        X: Feature dataframe (numeric columns only).
    
    Returns:
        Dictionary mapping feature names to VIF values.
    """
    logger.info("Calculating VIF for %d features", X.shape[1])
    
    vif_dict = {}
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    for i, col in enumerate(X.columns):
        try:
            vif = variance_inflation_factor(X_with_const.values, i + 1)  # +1 because of const
            vif_dict[col] = vif
        except Exception as e:
            logger.warning("Could not calculate VIF for %s: %s", col, str(e))
            vif_dict[col] = np.nan
    
    logger.info("VIF calculation complete")
    return vif_dict

def get_collinear_features(vif_dict: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Identify features with VIF above threshold.
    
    Args:
        vif_dict: VIF values from calculate_vif.
        threshold: VIF threshold for flagging (default 5.0).
    
    Returns:
        List of feature names with high collinearity.
    """
    collinear = [
        col for col, vif in vif_dict.items()
        if not np.isnan(vif) and vif >= threshold
    ]
    
    if collinear:
        logger.warning("Found %d collinear features (VIF >= %s): %s", 
                     len(collinear), threshold, collinear)
    else:
        logger.info("No collinear features found (threshold=%s)", threshold)
    
    return collinear

def remove_collinear_features(X: pd.DataFrame, vif_dict: Dict[str, float], 
                             threshold: float = 5.0) -> pd.DataFrame:
    """
    Remove features with high VIF iteratively.
    
    Args:
        X: Feature dataframe.
        vif_dict: Initial VIF values.
        threshold: VIF threshold.
    
    Returns:
        Reduced feature dataframe.
    """
    X_reduced = X.copy()
    current_vif = vif_dict.copy()
    
    while True:
        collinear = get_collinear_features(current_vif, threshold)
        
        if not collinear:
            break
        
        # Remove the feature with highest VIF
        worst_feature = max(collinear, key=lambda x: current_vif[x])
        logger.info("Removing collinear feature: %s (VIF=%.2f)", 
                   worst_feature, current_vif[worst_feature])
        
        X_reduced = X_reduced.drop(columns=[worst_feature])
        
        # Recalculate VIF
        if len(X_reduced.columns) > 0:
            current_vif = calculate_vif(X_reduced)
        else:
            break
    
    logger.info("Removed collinear features. Remaining: %d", len(X_reduced.columns))
    return X_reduced

def save_vif_report(vif_dict: Dict[str, float], output_path: str, 
                   collinear_features: List[str]) -> None:
    """
    Save VIF analysis report to file.
    
    Args:
        vif_dict: VIF values.
        output_path: Path to save report.
        collinear_features: List of flagged features.
    """
    report = {
        'threshold': config.get_vif_threshold(),
        'total_features': len(vif_dict),
        'collinear_count': len(collinear_features),
        'collinear_features': collinear_features,
        'vif_values': {k: float(v) for k, v in vif_dict.items()}
    }
    
    import json
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info("VIF report saved to %s", output_path)

def main():
    """
    Main entry point for standalone execution.
    
    Tests VIF calculation on sample data.
    """
    from seed import init_reproducibility
    init_reproducibility(seed=42)
    
    logger.info("Testing VIF calculation...")
    
    # Create sample data with some collinearity
    np.random.seed(42)
    n_samples = 100
    
    # Create correlated features
    x1 = np.random.randn(n_samples)
    x2 = x1 * 0.9 + np.random.randn(n_samples) * 0.1  # Highly correlated with x1
    x3 = np.random.randn(n_samples)
    x4 = x3 * 0.95 + np.random.randn(n_samples) * 0.05  # Highly correlated with x3
    x5 = np.random.randn(n_samples)
    
    df = pd.DataFrame({
        'x1': x1,
        'x2': x2,
        'x3': x3,
        'x4': x4,
        'x5': x5
    })
    
    logger.info("Sample data shape: %s", df.shape)
    
    # Calculate VIF
    vif_dict = calculate_vif(df)
    
    logger.info("VIF values:")
    for col, vif in vif_dict.items():
        logger.info("  %s: %.2f", col, vif)
    
    # Get collinear features
    threshold = config.get_vif_threshold()
    collinear = get_collinear_features(vif_dict, threshold)
    
    logger.info("Collinear features (VIF >= %s): %s", threshold, collinear)
    
    # Remove collinear features
    df_reduced = remove_collinear_features(df, vif_dict, threshold)
    
    logger.info("Reduced data shape: %s", df_reduced.shape)
    
    logger.info("VIF calculation test completed successfully.")

if __name__ == "__main__":
    main()
