import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from statsmodels.stats.multitest import multipletests

from config import Hyperparameters, ensure_directories, get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        df: DataFrame containing features
        features: List of feature column names to calculate VIF for
        
    Returns:
        Series of VIF values indexed by feature name
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    vif_data = pd.Series(dtype=float)
    X = df[features].dropna()
    
    if X.empty:
        logger.warning("No valid data to calculate VIF")
        return vif_data
        
    for i, feature in enumerate(features):
        if feature not in X.columns:
            logger.warning(f"Feature {feature} not found in data")
            continue
            
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[feature] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {feature}: {e}")
            vif_data[feature] = np.inf
            
    return vif_data

def perform_pca(df: pd.DataFrame, features: List[str]) -> Tuple[pd.DataFrame, Any]:
    """
    Perform PCA on features to handle collinearity.
    
    Args:
        df: DataFrame containing features
        features: List of feature column names
        
    Returns:
        Tuple of (transformed DataFrame, PCA object)
    """
    from sklearn.decomposition import PCA
    
    X = df[features].dropna()
    if X.empty:
        raise ValueError("No valid data for PCA transformation")
        
    pca = PCA(n_components=len(features))
    principal_components = pca.fit_transform(X)
    
    pc_df = pd.DataFrame(
        principal_components,
        columns=[f'PC{i+1}' for i in range(principal_components.shape[1])],
        index=X.index
    )
    
    logger.info(f"PCA explained variance ratio: {pca.explained_variance_ratio_}")
    
    return pc_df, pca

def multiple_comparison_correction(
    p_values: List[float],
    method: str = 'fdr_bh'
) -> Dict[str, Any]:
    """
    Perform multiple comparison correction on p-values.
    
    Supports Bonferroni ('bonferroni') and Benjamini-Hochberg FDR ('fdr_bh').
    
    Args:
        p_values: List of raw p-values from hypothesis tests
        method: Correction method ('bonferroni' or 'fdr_bh')
        
    Returns:
        Dictionary containing:
            - 'rejected': Boolean array indicating which hypotheses are rejected
            - 'adjusted_pvalues': Array of adjusted p-values
            - 'method': The correction method used
            - 'alpha': Significance level used (default 0.05)
    """
    if not p_values:
        logger.warning("No p-values provided for correction")
        return {
            'rejected': np.array([]),
            'adjusted_pvalues': np.array([]),
            'method': method,
            'alpha': 0.05
        }
        
    try:
        # Ensure p-values are within [0, 1]
        p_values = np.clip(p_values, 0, 1)
        
        rejected, adjusted_pvals, _, _ = multipletests(
            p_values,
            alpha=0.05,
            method=method,
            is_sorted=False,
            returnsorted=False
        )
        
        logger.info(f"Applied {method} correction: {sum(rejected)} of {len(p_values)} hypotheses rejected")
        
        return {
            'rejected': rejected,
            'adjusted_pvalues': adjusted_pvals,
            'method': method,
            'alpha': 0.05
        }
        
    except Exception as e:
        logger.error(f"Error in multiple comparison correction: {e}")
        raise

def main():
    """
    Main entry point for analysis module.
    Demonstrates VIF calculation, PCA, and multiple comparison correction.
    """
    config = get_config_summary()
    ensure_directories()
    
    logger.info("Starting analysis module")
    
    # Load merged data if available
    merged_data_path = Path("data/derived/merged_data.csv")
    if merged_data_path.exists():
        df = pd.read_csv(merged_data_path)
        logger.info(f"Loaded merged data with {len(df)} rows")
        
        # Identify numerical features
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Calculate VIF
        if len(numerical_cols) > 1:
            vif_results = calculate_vif(df, numerical_cols)
            logger.info(f"VIF Results:\n{vif_results}")
            
            # Check for high VIF
            high_vif = vif_results[vif_results > 5]
            if not high_vif.empty:
                logger.warning(f"High VIF detected for: {high_vif.index.tolist()}")
        
        # Perform PCA if needed
        if len(numerical_cols) > 1:
            try:
                pc_df, pca_model = perform_pca(df, numerical_cols)
                logger.info(f"PCA completed. Shape: {pc_df.shape}")
            except Exception as e:
                logger.error(f"PCA failed: {e}")
                
    else:
        logger.info("No merged data found. Skipping analysis.")
        
    # Example of multiple comparison correction
    # In a real scenario, these would come from actual hypothesis tests
    example_p_values = [0.01, 0.03, 0.04, 0.06, 0.15, 0.20]
    correction_results = multiple_comparison_correction(example_p_values, method='fdr_bh')
    logger.info(f"Multiple comparison correction results: {correction_results}")
    
    return {
        'vif': vif_results if 'vif_results' in locals() else None,
        'pca': pc_df if 'pc_df' in locals() else None,
        'correction': correction_results
    }

if __name__ == "__main__":
    result = main()
    logger.info("Analysis module completed")
    sys.exit(0)