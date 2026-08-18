"""
Task T029c: Generate diagnostic plot - Correlation matrix.

Produces a correlation matrix heatmap for key variables (temperature, metallicity, 
water mixing ratio, resolution, SNR) to visualize relationships in the analyzed data.

Depends on: T025b (compute_censored_kendall_tau)
Deliverable: results/plots/correlation_matrix.png
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import seaborn as sns

from config import get_config
from utils import setup_logging

# Configure logging
logger = setup_logging("plots_correlation")

def load_analysis_data_for_correlation(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load the merged analysis data required for correlation analysis.
    
    This function loads:
    1. Metadata (temperature, metallicity, resolution, SNR) from T012
    2. Retrieval results (water mixing ratio) from T020
    
    Returns a merged DataFrame with columns suitable for correlation matrix.
    """
    processed_dir = Path(config['paths']['processed'])
    
    metadata_path = processed_dir / 'metadata.csv'
    retrieval_path = processed_dir / 'retrieval_results.csv'
    
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    if not retrieval_path.exists():
        raise FileNotFoundError(f"Retrieval results file not found: {retrieval_path}")
        
    metadata_df = pd.read_csv(metadata_path)
    retrieval_df = pd.read_csv(retrieval_path)
    
    # Merge on planet_name
    # Ensure consistent column names
    merged_df = pd.merge(
        metadata_df,
        retrieval_df,
        on='planet_name',
        how='inner'
    )
    
    # Select columns for correlation
    # Note: For censored data (upper limits), we use the detected value or the limit value
    # The correlation matrix will show relationships for the available numeric data
    columns_to_corr = [
        'temperature', 
        'metallicity', 
        'water_mixing_ratio', 
        'resolution', 
        'snr'
    ]
    
    # Filter to only existing columns
    available_cols = [col for col in columns_to_corr if col in merged_df.columns]
    
    if len(available_cols) < 2:
        raise ValueError(f"Insufficient columns for correlation. Found: {available_cols}")
        
    corr_df = merged_df[available_cols].copy()
    
    # Handle upper limits for correlation:
    # If is_upper_limit is True, the water_mixing_ratio is actually an upper bound.
    # For a standard correlation matrix, we plot the numeric value but note the limitation.
    # Alternatively, we could impute, but standard practice for diagnostic plots is 
    # to show the raw numeric values with the understanding that some are limits.
    # We drop rows where key values are NaN to ensure a valid correlation matrix.
    corr_df = corr_df.dropna(subset=available_cols)
    
    return corr_df

def plot_correlation_matrix(df: pd.DataFrame, output_path: Path) -> None:
    """
    Generate and save a correlation matrix heatmap.
    
    Args:
        df: DataFrame with numeric columns for correlation
        output_path: Path to save the plot
    """
    # Calculate correlation matrix using Pearson (standard for diagnostic plots)
    # Note: For censored data, Kendall's tau (from T025b) is used for formal stats,
    # but the heatmap provides a quick visual diagnostic.
    corr_matrix = df.corr(method='pearson')
    
    # Create the plot
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap='coolwarm',
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8}
    )
    plt.title('Correlation Matrix: Exoplanet Atmospheric Properties', fontsize=14)
    plt.tight_layout()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Correlation matrix plot saved to: {output_path}")

def main():
    """Main entry point for T029c."""
    config = get_config()
    
    # Define output path
    plots_dir = Path(config['paths']['results']) / 'plots'
    output_path = plots_dir / 'correlation_matrix.png'
    
    try:
        logger.info("Loading analysis data for correlation matrix...")
        df = load_analysis_data_for_correlation(config)
        
        logger.info(f"Loaded {len(df)} records for correlation analysis.")
        logger.info(f"Columns: {list(df.columns)}")
        
        logger.info("Generating correlation matrix plot...")
        plot_correlation_matrix(df, output_path)
        
        logger.info("T029c completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during correlation plot generation: {e}")
        raise

if __name__ == "__main__":
    main()