"""
User Story 2: Associational Correlation Analysis

Implements Spearman rank correlations between genus-level microbial abundances
and cognitive test scores with CLR transformation and FDR correction.
"""
import os
import sys
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests

# Import project utilities
from utils.logging import get_logger
from utils.resource_guard import check_cpu_only

# Configure logging
logger = get_logger(__name__)

def load_preprocessed_data(data_path: str) -> pd.DataFrame:
    """
    Load the preprocessed dataset from the specified path.
    
    Args:
        data_path: Path to the processed CSV file.
        
    Returns:
        DataFrame with microbial abundances and cognitive scores.
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {data_path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded preprocessed data: {df.shape[0]} rows, {df.shape[1]} columns")
    return df

def clr_transform(abundance_df: pd.DataFrame, epsilon: float = 1e-6) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to rarefied taxonomic data.
    
    Args:
        abundance_df: DataFrame of relative abundances (rows=samples, cols=taxa).
        epsilon: Small constant to avoid log(0).
        
    Returns:
        DataFrame with CLR-transformed values.
    """
    # Ensure non-negative values and add epsilon
    data = abundance_df.clip(lower=0) + epsilon
    
    # Calculate geometric mean for each sample
    # Using log-sum-exp trick for numerical stability: log(gm) = mean(log(x))
    log_data = np.log(data)
    log_gm = log_data.mean(axis=1)
    
    # Subtract geometric mean from each log value
    clr_data = log_data.sub(log_gm, axis=0)
    
    return pd.DataFrame(clr_data, index=abundance_df.index, columns=abundance_df.columns)

def calculate_spearman_correlations(
    features: pd.DataFrame, 
    target: pd.Series
) -> pd.DataFrame:
    """
    Calculate Spearman rank correlation between each feature and the target.
    
    Args:
        features: DataFrame of predictor variables (e.g., CLR-transformed abundances).
        target: Series of target variable (e.g., cognitive score).
        
    Returns:
        DataFrame with correlation coefficients (rho) and p-values.
    """
    results = []
    
    for col in features.columns:
        # Drop pairs with any missing values
        valid_pairs = features[col].notna() & target.notna()
        if valid_pairs.sum() < 10:
            logger.warning(f"Skipping {col}: insufficient valid pairs ({valid_pairs.sum()})")
            continue
            
        rho, p_val = spearmanr(
            features.loc[valid_pairs, col], 
            target.loc[valid_pairs]
        )
        
        results.append({
            'taxon': col,
            'rho': rho,
            'p_value': p_val
        })
    
    return pd.DataFrame(results)

def apply_fdr_correction(p_values: pd.Series, alpha: float = 0.05) -> pd.Series:
    """
    Apply Benjamini-Hochberg FDR correction to raw p-values.
    
    Args:
        p_values: Series of raw p-values.
        alpha: Significance threshold.
        
    Returns:
        Series of adjusted p-values (q-values).
    """
    # Use statsmodels for BH correction
    # method='fdr_bh' implements Benjamini-Hochberg
    rejected, pvals_corrected, _, _ = multipletests(
        p_values, 
        alpha=alpha, 
        method='fdr_bh'
    )
    
    return pd.Series(pvals_corrected, index=p_values.index)

def filter_significant_associations(
    results_df: pd.DataFrame, 
    alpha: float = 0.05,
    label: str = "associational"
) -> pd.DataFrame:
    """
    Filter results for significant associations and add labels.
    
    Args:
        results_df: DataFrame with correlation results including adj_p_value.
        alpha: Significance threshold for adjusted p-values.
        label: Label to apply to significant associations.
        
    Returns:
        Filtered DataFrame with significant associations only.
    """
    if 'adj_p_value' not in results_df.columns:
        raise ValueError("Input DataFrame must contain 'adj_p_value' column")
        
    significant = results_df[results_df['adj_p_value'] < alpha].copy()
    significant['significance_label'] = label
    
    logger.info(f"Found {len(significant)} significant associations at alpha={alpha}")
    return significant

def generate_summary_report(
    significant_df: pd.DataFrame, 
    output_path: str
) -> None:
    """
    Generate a summary report of significant genus-score pairs.
    
    Args:
        significant_df: DataFrame of significant associations.
        output_path: Path to save the CSV report.
    """
    if significant_df.empty:
        logger.warning("No significant associations found. Creating empty report.")
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    significant_df.to_csv(output_path, index=False)
    logger.info(f"Saved summary report to {output_path}")
    
    # Log summary statistics
    if not significant_df.empty:
        logger.info(f"Report contains {len(significant_df)} significant pairs")
        logger.info(f"Top 5 by absolute rho:\n{significant_df.nlargest(5, 'rho_abs')}")

def run_analysis_pipeline(
    input_path: str,
    output_path: str,
    cognitive_score_col: str = 'cognitive_score',
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Run the full correlation analysis pipeline.
    
    Args:
        input_path: Path to preprocessed data.
        output_path: Path to save correlation results.
        cognitive_score_col: Name of the cognitive score column.
        alpha: FDR significance threshold.
        
    Returns:
        DataFrame of significant associations.
    """
    # 1. Load data
    df = load_preprocessed_data(input_path)
    
    # Identify microbial columns (assume they start with 'genus_' or are not covariates)
    # Based on preprocessing, microbial cols are likely numeric and not ID/covariate columns
    exclude_cols = ['participant_id', 'age', 'bmi', 'education', cognitive_score_col]
    microbial_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ['float64', 'int64']]
    
    if len(microbial_cols) == 0:
        raise ValueError("No microbial abundance columns found in input data")
        
    logger.info(f"Analyzing {len(microbial_cols)} microbial genera")
    
    # 2. CLR Transform microbial data
    microbial_df = df[microbial_cols]
    clr_df = clr_transform(microbial_df)
    
    # 3. Calculate correlations
    target = df[cognitive_score_col]
    corr_results = calculate_spearman_correlations(clr_df, target)
    
    # 4. Apply FDR correction
    corr_results['adj_p_value'] = apply_fdr_correction(corr_results['p_value'])
    
    # 5. Calculate absolute rho for sorting
    corr_results['rho_abs'] = corr_results['rho'].abs()
    
    # 6. Filter significant associations
    significant_df = filter_significant_associations(
        corr_results, 
        alpha=alpha,
        label="associational"
    )
    
    # 7. Generate summary report
    generate_summary_report(significant_df, output_path)
    
    return significant_df

def main():
    """Entry point for correlation analysis."""
    check_cpu_only()
    
    # Default paths
    input_path = "data/processed/preprocessed_data.csv"
    output_path = "data/processed/correlation_results.csv"
    
    # Allow override via command line
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
        
    logger.info(f"Starting correlation analysis pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        results = run_analysis_pipeline(input_path, output_path)
        logger.info("Pipeline completed successfully")
        return results
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
