"""
Analysis module for molecular flexibility and permeability correlation.
Implements correlation analysis, FDR correction, and model validation.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root, get_data_path

logger = get_logger(__name__)

def load_analysis_data() -> pd.DataFrame:
    """
    Load the processed data containing flexibility descriptors and permeability values.
    
    Returns:
        pd.DataFrame: DataFrame with smiles, logPapp, and flexibility descriptors.
    """
    data_path = get_data_path()
    input_file = data_path / "processed" / "descriptors_raw.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    df = pd.read_csv(input_file)
    
    # Ensure required columns exist
    required_cols = ['smiles', 'logPapp', 'dihedral_variance']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter out rows with NaN in critical columns
    df = df.dropna(subset=required_cols)
    
    logger.info(f"Loaded {len(df)} records for analysis from {input_file}")
    return df

def compute_correlations_with_fdr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Pearson and Spearman correlations between dihedral_variance and logPapp,
    with FDR correction for multiple hypothesis testing.
    
    Args:
        df: DataFrame with molecular data including dihedral_variance and logPapp.
        
    Returns:
        pd.DataFrame: Correlation results with p-values and FDR-corrected q-values.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty")
    
    x = df['dihedral_variance'].values
    y = df['logPapp'].values
    
    # Remove any remaining NaN pairs
    valid_mask = ~(np.isnan(x) | np.isnan(y))
    x = x[valid_mask]
    y = y[valid_mask]
    
    if len(x) < 3:
        raise ValueError("Insufficient data points for correlation analysis")
    
    # Compute Pearson correlation
    pearson_r, pearson_p = stats.pearsonr(x, y)
    
    # Compute Spearman correlation
    spearman_r, spearman_p = stats.spearmanr(x, y)
    
    # Collect p-values for FDR correction
    p_values = [pearson_p, spearman_p]
    test_names = ['pearson', 'spearman']
    
    # Apply Benjamini-Hochberg FDR correction
    reject, q_values, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    
    results = []
    for i, name in enumerate(test_names):
        if name == 'pearson':
            results.append({
                'correlation_type': 'pearson',
                'r_value': pearson_r,
                'p_value': pearson_p,
                'q_value': q_values[i],
                'significant': reject[i],
                'sample_size': len(x)
            })
        else:
            results.append({
                'correlation_type': 'spearman',
                'r_value': spearman_r,
                'p_value': spearman_p,
                'q_value': q_values[i],
                'significant': reject[i],
                'sample_size': len(x)
            })
    
    result_df = pd.DataFrame(results)
    logger.info(f"Computed correlations: Pearson r={pearson_r:.4f}, Spearman rho={spearman_r:.4f}")
    return result_df

def write_correlation_results(results_df: pd.DataFrame, output_path: Path) -> None:
    """
    Write correlation results to CSV file.
    
    Args:
        results_df: DataFrame containing correlation results.
        output_path: Path to save the results CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved correlation results to {output_path}")

def main() -> None:
    """
    Main entry point for correlation analysis.
    Loads data, computes correlations with FDR correction, and saves results.
    """
    configure_root_logger()
    
    try:
        # Load data
        df = load_analysis_data()
        
        # Compute correlations
        results = compute_correlations_with_fdr(df)
        
        # Save results
        data_path = get_data_path()
        output_file = data_path / "processed" / "correlation_results.csv"
        write_correlation_results(results, output_file)
        
        logger.info("Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()