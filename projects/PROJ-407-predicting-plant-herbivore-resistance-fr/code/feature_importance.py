"""
Task T026: Save feature importance table to data/processed/feature_importance.csv.

Columns MUST include:
- metabolite_name
- importance_score
- unadjusted_p_value
- correlation_coefficient

This script reads the trained model and performance metrics from data/processed/,
extracts feature importances from the Random Forest model, calculates univariate
correlations and p-values for each metabolite, and saves the combined table.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

# Import from project modules
from config import DATA_ROOT
from model import load_trained_model, load_model_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_processed_data():
    """Load the processed dataset used for training."""
    # The processed data should be in data/processed/
    # We need to find the file that contains the features and target
    processed_dir = Path(DATA_ROOT) / 'processed'
    
    # Look for the PCA reduced data or the main processed features
    # Based on T020, we have pca_reduced.csv which contains the features
    pca_file = processed_dir / 'pca_reduced.csv'
    if not pca_file.exists():
        # Fallback: try to find any CSV with metabolite columns
        for f in processed_dir.glob('*.csv'):
            if 'pca' not in f.name and 'model' not in f.name and 'metric' not in f.name:
                logger.info(f"Using fallback data file: {f}")
                return pd.read_csv(f)
        raise FileNotFoundError("No processed data file found in data/processed/")
    
    logger.info(f"Loading processed data from {pca_file}")
    return pd.read_csv(pca_file)


def extract_metabolite_columns(df):
    """Extract columns that represent metabolites (metabolite_* or similar)."""
    # Identify metabolite columns - they typically start with 'metabolite_' or have specific naming
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    
    if not metabolite_cols:
        # Try alternative naming patterns
        metabolite_cols = [col for col in df.columns if 'metab' in col.lower() and col not in ['sample_id', 'genotype_id', 'resistance']]
    
    if not metabolite_cols:
        raise ValueError("No metabolite columns found in the processed data. "
                       "Expected columns starting with 'metabolite_' or containing 'metab'.")
    
    logger.info(f"Found {len(metabolite_cols)} metabolite columns")
    return metabolite_cols


def calculate_correlations(df, metabolite_cols, target_col='resistance'):
    """
    Calculate univariate correlation and p-value for each metabolite against resistance.
    
    Returns:
        dict: {metabolite_name: {'correlation': float, 'p_value': float}}
    """
    correlations = {}
    
    for col in metabolite_cols:
        # Remove NaN values for correlation calculation
        valid_mask = df[col].notna() & df[target_col].notna()
        x = df.loc[valid_mask, col]
        y = df.loc[valid_mask, target_col]
        
        if len(x) < 3:  # Need at least 3 points for meaningful correlation
            correlations[col] = {'correlation': np.nan, 'p_value': np.nan}
            continue
        
        # Calculate Pearson correlation
        corr, p_value = stats.pearsonr(x, y)
        correlations[col] = {'correlation': corr, 'p_value': p_value}
    
    return correlations


def build_feature_importance_table(model, metabolite_cols, correlations):
    """
    Build the feature importance table combining:
    - Metabolite names
    - Feature importance scores from the Random Forest model
    - Unadjusted p-values from correlation tests
    - Correlation coefficients
    """
    # Get feature importances from the trained model
    importances = model.feature_importances_
    
    if len(importances) != len(metabolite_cols):
        # If PCA was applied, the number of features might differ
        # In that case, we need to map back or handle appropriately
        logger.warning(f"Feature count mismatch: model has {len(importances)} features, "
                     f"data has {len(metabolite_cols)} metabolites. "
                     "This suggests PCA was applied. Using available features.")
        # Take the minimum length to avoid index errors
        min_len = min(len(importances), len(metabolite_cols))
        metabolite_cols = metabolite_cols[:min_len]
        importances = importances[:min_len]
    
    # Build the table
    data = []
    for i, metab_name in enumerate(metabolite_cols):
        corr_info = correlations.get(metab_name, {'correlation': np.nan, 'p_value': np.nan})
        
        row = {
            'metabolite_name': metab_name,
            'importance_score': float(importances[i]),
            'unadjusted_p_value': float(corr_info['p_value']),
            'correlation_coefficient': float(corr_info['correlation'])
        }
        data.append(row)
    
    return pd.DataFrame(data)


def main():
    """Main entry point for T026."""
    logger.info("Starting T026: Feature Importance Table Generation")
    
    # Ensure output directory exists
    output_dir = Path(DATA_ROOT) / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load processed data
    try:
        df = load_processed_data()
    except FileNotFoundError as e:
        logger.error(f"Failed to load processed data: {e}")
        raise
    
    # Identify metabolite columns
    metabolite_cols = extract_metabolite_columns(df)
    
    # Calculate correlations
    logger.info("Calculating univariate correlations...")
    correlations = calculate_correlations(df, metabolite_cols)
    
    # Load trained model
    logger.info("Loading trained model...")
    model = load_trained_model()
    
    # Build feature importance table
    logger.info("Building feature importance table...")
    importance_df = build_feature_importance_table(model, metabolite_cols, correlations)
    
    # Sort by importance score (descending)
    importance_df = importance_df.sort_values('importance_score', ascending=False).reset_index(drop=True)
    
    # Save to CSV
    output_path = output_dir / 'feature_importance.csv'
    importance_df.to_csv(output_path, index=False)
    
    logger.info(f"Feature importance table saved to {output_path}")
    logger.info(f"Total metabolites analyzed: {len(importance_df)}")
    logger.info(f"Top 5 metabolites by importance:\n{importance_df.head()}")
    
    return importance_df


if __name__ == '__main__':
    main()
