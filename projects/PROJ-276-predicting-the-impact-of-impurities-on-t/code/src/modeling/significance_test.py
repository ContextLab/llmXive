"""
Significance testing module for impurity impact analysis.

This module performs VIF analysis, handles collinearity, and calculates
p-values for impurity impact on superconductivity (Tc).
"""
import os
import sys
import json
import argparse
import warnings
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Project imports based on API surface
from code.src.utils.logging import get_modeling_logger
from code.src.utils.constants import VIF_THRESHOLD

logger = get_modeling_logger()


def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        df: DataFrame containing features
        feature_cols: List of feature column names
        
    Returns:
        DataFrame with features and their VIF values
    """
    vif_data = []
    X = df[feature_cols].dropna()
    
    if X.empty or X.shape[0] <= 1:
        logger.warning("Insufficient data for VIF calculation")
        return pd.DataFrame({'feature': feature_cols, 'VIF': [np.inf] * len(feature_cols)})
    
    for i, col in enumerate(feature_cols):
        if col not in X.columns:
            vif_data.append({'feature': col, 'VIF': np.inf})
            continue
        
        try:
            # VIF for feature i is 1 / (1 - R_i^2) where R_i^2 is from regression
            # of feature i on all other features
            y = X[col]
            X_other = X.drop(columns=[col])
            
            if X_other.shape[1] == 0:
                vif = np.inf
            else:
                # Fit linear model
                model = ols(f"{col} ~ .", data=X).fit()
                vif = model.rsquared_adj
                # Actually calculate VIF properly
                try:
                    vif = variance_inflation_factor(X.values, i)
                except:
                    # Fallback if VIF calculation fails
                    vif = np.inf
            
            vif_data.append({'feature': col, 'VIF': vif})
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data.append({'feature': col, 'VIF': np.inf})
    
    return pd.DataFrame(vif_data)


def remove_collinear_features(df: pd.DataFrame, vif_threshold: float = 5.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Iteratively remove features with VIF >= threshold until all VIF < threshold.
    
    Args:
        df: DataFrame with features
        vif_threshold: VIF threshold for removal
        
    Returns:
        Tuple of (reduced DataFrame, list of removed feature names)
    """
    feature_cols = df.columns.tolist()
    removed_features = []
    current_df = df.copy()
    
    while True:
        vif_df = calculate_vif(current_df, feature_cols)
        high_vif = vif_df[vif_df['VIF'] >= vif_threshold]
        
        if high_vif.empty:
            break
        
        # Remove feature with highest VIF
        max_vif_feature = high_vif.loc[high_vif['VIF'].idxmax(), 'feature']
        logger.info(f"Removing {max_vif_feature} with VIF = {high_vif.loc[high_vif['VIF'].idxmax(), 'VIF']:.2f}")
        
        current_df = current_df.drop(columns=[max_vif_feature])
        feature_cols.remove(max_vif_feature)
        removed_features.append(max_vif_feature)
        
        if len(feature_cols) <= 1:
            break
    
    return current_df, removed_features


def calculate_pvalues(df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> pd.DataFrame:
    """
    Calculate p-values for each feature's impact on target using linear regression.
    
    Args:
        df: DataFrame with features and target
        target_col: Name of target column
        feature_cols: List of feature column names
        
    Returns:
        DataFrame with features and their p-values
    """
    pvalue_data = []
    
    # Clean data
    clean_df = df[feature_cols + [target_col]].dropna()
    
    if clean_df.empty:
        logger.warning("No valid data for p-value calculation")
        return pd.DataFrame({'feature': feature_cols, 'p_value': [1.0] * len(feature_cols)})
    
    for feature in feature_cols:
        try:
            # Simple linear regression for each feature
            formula = f"{target_col} ~ {feature}"
            model = ols(formula, data=clean_df).fit()
            p_value = model.pvalues[feature]
            pvalue_data.append({'feature': feature, 'p_value': p_value})
        except Exception as e:
            logger.error(f"Error calculating p-value for {feature}: {e}")
            pvalue_data.append({'feature': feature, 'p_value': 1.0})
    
    return pd.DataFrame(pvalue_data)


def run_significance_test_on_reduced_set(
    reduced_data_path: str,
    output_path: str,
    target_col: str = "Tc",
    vif_threshold: float = 5.0,
    pvalue_threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Run significance testing on a pre-reduced feature set (output of T026).
    
    This function assumes collinearity has already been addressed and
    calculates final p-values on the non-collinear feature set.
    
    Args:
        reduced_data_path: Path to reduced_feature_set.csv
        output_path: Path for output results
        target_col: Target variable name
        vif_threshold: VIF threshold (for verification)
        pvalue_threshold: P-value threshold for significance
        
    Returns:
        Dictionary with results summary
    """
    logger.info(f"Loading reduced feature set from {reduced_data_path}")
    
    if not os.path.exists(reduced_data_path):
        logger.error(f"Reduced feature set not found: {reduced_data_path}")
        raise FileNotFoundError(f"Reduced feature set not found: {reduced_data_path}")
    
    df = pd.read_csv(reduced_data_path)
    
    # Identify feature columns (exclude target and metadata)
    exclude_cols = [target_col, 'impurity_type', 'synthesis_method', 'provenance']
    feature_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in [np.float64, np.int64]]
    
    logger.info(f"Found {len(feature_cols)} features for significance testing")
    
    if len(feature_cols) == 0:
        logger.error("No features found for significance testing")
        raise ValueError("No features found for significance testing")
    
    # Verify VIF on reduced set
    logger.info("Verifying VIF on reduced feature set...")
    vif_df = calculate_vif(df, feature_cols)
    high_vif = vif_df[vif_df['VIF'] >= vif_threshold]
    
    if not high_vif.empty:
        logger.warning(f"Still have {len(high_vif)} features with VIF >= {vif_threshold} after reduction")
        for _, row in high_vif.iterrows():
            logger.warning(f"  {row['feature']}: VIF = {row['VIF']:.2f}")
    else:
        logger.info("All features have VIF < threshold")
    
    # Calculate p-values
    logger.info("Calculating p-values...")
    pvalue_df = calculate_pvalues(df, target_col, feature_cols)
    
    # Filter significant features
    significant = pvalue_df[pvalue_df['p_value'] < pvalue_threshold]
    
    results = {
        'total_features': len(feature_cols),
        'significant_features': len(significant),
        'pvalue_threshold': pvalue_threshold,
        'vif_threshold': vif_threshold,
        'all_pvalues': pvalue_df.to_dict('records'),
        'significant_pvalues': significant.to_dict('records'),
        'vif_verification': vif_df.to_dict('records')
    }
    
    # Save results
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Significance test results saved to {output_path}")
    logger.info(f"Found {len(significant)} significant features (p < {pvalue_threshold})")
    
    return results


def main():
    """Main entry point for significance testing on reduced feature set."""
    parser = argparse.ArgumentParser(description="Run significance test on reduced feature set")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/reduced_feature_set.csv",
        help="Path to reduced feature set CSV"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/significance_results.json",
        help="Path for output results JSON"
    )
    parser.add_argument(
        "--target",
        type=str,
        default="Tc",
        help="Target column name"
    )
    parser.add_argument(
        "--vif-threshold",
        type=float,
        default=5.0,
        help="VIF threshold for collinearity"
    )
    parser.add_argument(
        "--pvalue-threshold",
        type=float,
        default=0.05,
        help="P-value threshold for significance"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_significance_test_on_reduced_set(
            args.input,
            args.output,
            args.target,
            args.vif_threshold,
            args.pvalue_threshold
        )
        
        print(f"Significance testing complete.")
        print(f"Total features analyzed: {results['total_features']}")
        print(f"Significant features (p < {args.pvalue_threshold}): {results['significant_features']}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
