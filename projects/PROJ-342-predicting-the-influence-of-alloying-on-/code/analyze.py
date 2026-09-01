import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/analyze.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def load_descriptors(filepath: str = "data/processed/descriptors.csv") -> pd.DataFrame:
    """
    Load the computed descriptors from the processed CSV file.
    
    Args:
        filepath: Path to the descriptors CSV file.
        
    Returns:
        DataFrame containing the descriptors.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Descriptors file not found at {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded descriptors from {filepath}, shape: {df.shape}")
    
    required_cols = ['radius_mismatch', 'electronegativity_diff', 'VEC']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in descriptors: {missing_cols}")
    
    return df

def calculate_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Pearson and Spearman correlation coefficients between predictors.
    
    Args:
        df: DataFrame containing predictor columns.
        
    Returns:
        DataFrame with correlation coefficients.
    """
    predictor_cols = ['radius_mismatch', 'electronegativity_diff', 'VEC']
    
    # Calculate Pearson correlation
    pearson_corr = df[predictor_cols].corr(method='pearson')
    
    # Calculate Spearman correlation
    spearman_corr = df[predictor_cols].corr(method='spearman')
    
    # Combine into a single DataFrame with MultiIndex columns or separate columns
    # Format: MultiIndex columns (Pearson, Spearman)
    combined = pd.concat({
        'Pearson': pearson_corr,
        'Spearman': spearman_corr
    }, axis=1)
    
    logger.info("Calculated Pearson and Spearman correlation matrices")
    return combined

def calculate_p_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate p-values for Pearson correlations between predictors.
    
    Args:
        df: DataFrame containing predictor columns.
        
    Returns:
        DataFrame with p-values for each pair.
    """
    predictor_cols = ['radius_mismatch', 'electronegativity_diff', 'VEC']
    n = len(df)
    
    p_values = pd.DataFrame(index=predictor_cols, columns=predictor_cols)
    
    for i, col1 in enumerate(predictor_cols):
        for j, col2 in enumerate(predictor_cols):
            if i <= j:
                # Calculate Pearson correlation and p-value
                corr, p_val = stats.pearsonr(df[col1], df[col2])
                p_values.loc[col1, col2] = p_val
                p_values.loc[col2, col1] = p_val
    
    logger.info("Calculated p-values for Pearson correlations")
    return p_values

def benjamini_hochberg_fdr(p_values: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        p_values: DataFrame of p-values.
        alpha: Significance level for FDR control.
        
    Returns:
        DataFrame with adjusted p-values and significance flags.
    """
    # Flatten p-values to a Series, excluding diagonal (which are 0 or 1)
    p_series = p_values.stack()
    p_series = p_series[p_series.index[0] != p_series.index[1]]  # Exclude diagonal
    
    # Sort p-values
    sorted_indices = p_series.argsort()
    sorted_p = p_series.iloc[sorted_indices]
    
    # Calculate adjusted p-values
    m = len(sorted_p)
    adjusted_p = np.zeros(m)
    for i in range(m):
        rank = i + 1
        adjusted_p[i] = sorted_p.iloc[i] * m / rank
    
    # Ensure monotonicity (cumulative min from the end)
    adjusted_p = np.minimum.accumulate(adjusted_p[::-1])[::-1]
    adjusted_p = np.minimum(adjusted_p, 1.0)  # Cap at 1.0
    
    # Map back to original order
    result_p = pd.Series(index=p_series.index, data=0.0)
    result_p.iloc[sorted_indices] = adjusted_p
    
    # Create result DataFrame
    result_df = pd.DataFrame(index=p_values.index, columns=p_values.columns, data=1.0)
    for (row, col), p_val in result_p.items():
        result_df.loc[row, col] = p_val
    
    # Add significance flags
    significant = result_df <= alpha
    
    logger.info(f"Applied Benjamini-Hochberg FDR correction (alpha={alpha})")
    return significant

def save_correlation_matrix(correlation_df: pd.DataFrame, filepath: str = "data/processed/correlation_matrix.csv") -> None:
    """
    Save the correlation matrix to a CSV file.
    
    Args:
        correlation_df: DataFrame containing correlation coefficients.
        filepath: Output path for the CSV file.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    correlation_df.to_csv(filepath)
    logger.info(f"Saved correlation matrix to {filepath}")

def main():
    """
    Main entry point for correlation analysis.
    """
    try:
        # Load descriptors
        descriptors_df = load_descriptors("data/processed/descriptors.csv")
        
        # Calculate correlation matrix (Pearson and Spearman)
        correlation_matrix = calculate_correlation_matrix(descriptors_df)
        
        # Calculate p-values
        p_values = calculate_p_values(descriptors_df)
        
        # Apply FDR correction
        fdr_significant = benjamini_hochberg_fdr(p_values, alpha=0.05)
        
        # Save correlation matrix
        save_correlation_matrix(correlation_matrix, "data/processed/correlation_matrix.csv")
        
        # Log summary
        logger.info("Correlation analysis completed successfully")
        logger.info(f"Correlation matrix shape: {correlation_matrix.shape}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during correlation analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()