import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

from utils.logging import get_logger

logger = get_logger(__name__)

def load_config(config_path='code/config.yaml'):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results(lzc_path='data/processed/lzc_metrics.csv', 
                          pe_path='data/processed/pe_metrics.csv',
                          fatigue_path='data/processed/fatigue_ratings.csv'):
    """Load complexity metrics and fatigue ratings for analysis."""
    lzc_df = pd.read_csv(lzc_path)
    pe_df = pd.read_csv(pe_path)
    
    # Merge complexity metrics
    # Assuming both have participant_id and channel columns
    # We pivot to have channels as columns for each metric type
    lzc_pivot = lzc_df.pivot(index='participant_id', columns='channel', values='lzc_value')
    pe_pivot = pe_df.pivot(index='participant_id', columns='channel', values='pe_value')
    
    # Merge with fatigue ratings if available
    # This assumes fatigue_path exists and has participant_id and fatigue_score columns
    if os.path.exists(fatigue_path):
        fatigue_df = pd.read_csv(fatigue_path)
        # Merge on participant_id
        combined = lzc_pivot.merge(pe_pivot, left_index=True, right_index=True, suffixes=('_lzc', '_pe'))
        combined = combined.merge(fatigue_df, on='participant_id', how='inner')
    else:
        # Just combine LZC and PE for collinearity check
        combined = lzc_pivot.merge(pe_pivot, left_index=True, right_index=True, suffixes=('_lzc', '_pe'))
    
    return combined

def calculate_vif(df, exclude_cols=None):
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        df: DataFrame with features as columns
        exclude_cols: List of column names to exclude from VIF calculation
        
    Returns:
        DataFrame with feature names and their VIF values
    """
    if exclude_cols is None:
        exclude_cols = []
    
    # Select only numeric columns for VIF calculation
    numeric_df = df.select_dtypes(include=[np.number])
    
    # Remove excluded columns
    features = numeric_df.columns.difference(exclude_cols)
    
    if len(features) == 0:
        logger.warning("No features available for VIF calculation after exclusions.")
        return pd.DataFrame(columns=['feature', 'vif'])
    
    # Add constant for intercept
    X = numeric_df[features]
    X = X.dropna()  # Drop rows with NaN values
    
    if len(X) == 0:
        logger.warning("No valid data rows for VIF calculation.")
        return pd.DataFrame(columns=['feature', 'vif'])
    
    # Calculate VIF
    vif_data = pd.DataFrame()
    vif_data['feature'] = X.columns
    vif_data['vif'] = [variance_inflation_factor(X.values, i) for i in range(len(X.columns))]
    
    return vif_data

def run_collinearity_diagnostics(df, threshold=5.0):
    """
    Run collinearity diagnostics and check for VIF values exceeding threshold.
    
    Args:
        df: DataFrame with features
        threshold: VIF threshold for concern (default 5.0)
        
    Returns:
        tuple: (vif_df, warning_list)
    """
    vif_df = calculate_vif(df)
    
    warnings = []
    for _, row in vif_df.iterrows():
        if row['vif'] >= threshold:
            warnings.append(f"High collinearity detected for '{row['feature']}': VIF = {row['vif']:.2f}")
    
    if warnings:
        for w in warnings:
            logger.warning(w)
    
    return vif_df, warnings

def save_collinearity_report(vif_df, output_path='data/analysis/vif_report.csv'):
    """Save VIF report to CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    vif_df.to_csv(output_path, index=False)
    logger.info(f"VIF report saved to {output_path}")

def main():
    """Main function to run collinearity diagnostics."""
    logger.info("Starting collinearity diagnostics...")
    
    config = load_config()
    
    try:
        # Load data
        df = load_analysis_results(
            lzc_path='data/processed/lzc_metrics.csv',
            pe_path='data/processed/pe_metrics.csv'
        )
        
        # Run diagnostics
        threshold = config.get('collinearity_threshold', 5.0)
        vif_df, warnings = run_collinearity_diagnostics(df, threshold=threshold)
        
        # Save report
        save_collinearity_report(vif_df)
        
        # Print summary
        print(f"VIF Report generated. {len(warnings)} high collinearity warnings found.")
        if warnings:
            print("Warnings:")
            for w in warnings:
                print(f"  - {w}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during collinearity diagnostics: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
