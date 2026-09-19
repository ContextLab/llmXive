"""
Correlation Analysis Module (US2)

Implements Spearman rank correlation between genus-level microbial abundances
and cognitive test scores, with CLR transformation and FDR correction.
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

# Import project config and utils
sys.path.insert(0, str(Path(__file__).parent))
from config import get_config
from utils.logging import get_logger

logger = get_logger(__name__)
config = get_config()

def load_preprocessed_data(input_path: str) -> pd.DataFrame:
    """
    Load the preprocessed analysis dataset.
    Expects a CSV with microbial genera columns and cognitive score columns.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {input_path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded preprocessed data: {df.shape}")
    return df

def clr_transform(data: pd.DataFrame, epsilon: float = 1e-6) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to microbial abundance data.
    
    Args:
        data: DataFrame with microbial abundance columns (non-negative)
        epsilon: Small constant to avoid log(0)
    
    Returns:
        DataFrame with CLR-transformed values
    """
    logger.info("Applying CLR transformation...")
    
    # Ensure non-negative
    data_clamped = data.clip(lower=0)
    
    # Add pseudo-count to avoid log(0)
    data_pseudo = data_clamped + epsilon
    
    # Calculate geometric mean for each sample (row)
    # Using log-sum-exp trick for numerical stability
    log_data = np.log(data_pseudo)
    log_geometric_mean = log_data.mean(axis=1)
    
    # CLR: log(x) - mean(log(x))
    clr_data = log_data - log_geometric_mean.values[:, np.newaxis]
    
    logger.info("CLR transformation complete.")
    return pd.DataFrame(clr_data, index=data.index, columns=data.columns)

def calculate_spearman_correlations(abundance_df: pd.DataFrame, score_df: pd.Series) -> pd.DataFrame:
    """
    Calculate Spearman rank correlations between each genus and the cognitive score.
    
    Args:
        abundance_df: DataFrame of CLR-transformed genus abundances
        score_df: Series of cognitive scores
    
    Returns:
        DataFrame with correlation coefficients (rho) and p-values
    """
    logger.info("Calculating Spearman correlations...")
    
    results = []
    
    for genus in abundance_df.columns:
        rho, p_value = spearmanr(abundance_df[genus], score_df)
        results.append({
            'genus': genus,
            'score_name': score_df.name,
            'rho': rho,
            'p_value': p_value
        })
    
    results_df = pd.DataFrame(results)
    logger.info(f"Calculated {len(results_df)} correlations.")
    return results_df

def apply_fdr_correction(results_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        results_df: DataFrame with 'p_value' column
        alpha: Significance threshold
    
    Returns:
        DataFrame with added 'adj_p_value' and 'significant' columns
    """
    logger.info(f"Applying FDR correction (alpha={alpha})...")
    
    p_values = results_df['p_value'].values
    
    # Apply BH correction
    reject, p_values_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    
    results_df['adj_p_value'] = p_values_corrected
    results_df['significant'] = reject
    
    logger.info(f"FDR correction complete. {reject.sum()} significant associations found.")
    return results_df

def filter_significant_associations(results_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Filter for significant associations (adj_p < alpha) and label as 'associational'.
    
    Args:
        results_df: DataFrame with 'adj_p_value' and 'significant' columns
        alpha: Significance threshold
    
    Returns:
        Filtered DataFrame with significant associations only
    """
    logger.info(f"Filtering significant associations (adj_p < {alpha})...")
    
    significant_df = results_df[results_df['significant']].copy()
    
    # Add explicit label
    significant_df['association_type'] = 'associational'
    
    logger.info(f"Found {len(significant_df)} significant genus-score pairs.")
    return significant_df

def generate_summary_report(significant_df: pd.DataFrame, output_path: str):
    """
    Generate a summary report of significant genus-score pairs.
    
    Args:
        significant_df: DataFrame of significant associations
        output_path: Path to save the CSV report
    """
    logger.info(f"Generating summary report to {output_path}...")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Sort by adjusted p-value
    report_df = significant_df.sort_values('adj_p_value')
    
    # Save to CSV
    report_df.to_csv(output_path, index=False)
    
    logger.info(f"Summary report saved: {len(report_df)} rows.")
    
    # Log top hits
    if len(report_df) > 0:
        logger.info("Top 5 significant associations:")
        for _, row in report_df.head().iterrows():
            logger.info(f"  {row['genus']} vs {row['score_name']}: rho={row['rho']:.3f}, adj_p={row['adj_p_value']:.4f}")

def run_analysis_pipeline(input_path: str, output_path: str, alpha: float = 0.05):
    """
    Run the full correlation analysis pipeline.
    
    Args:
        input_path: Path to preprocessed data CSV
        output_path: Path to save correlation results CSV
        alpha: FDR significance threshold
    """
    logger.info("Starting correlation analysis pipeline...")
    
    # 1. Load data
    df = load_preprocessed_data(input_path)
    
    # Identify microbial genera columns (assume they don't contain 'score' or 'age' or 'id')
    # This is a heuristic; in practice, column names should be known
    meta_cols = ['participant_id', 'age', 'bmi', 'education', 'score', 'score_name']
    genus_cols = [c for c in df.columns if c not in meta_cols and c != 'score_name']
    
    if len(genus_cols) == 0:
        raise ValueError("No microbial genus columns found in input data.")
    
    # Extract cognitive score (assume single score column for this pipeline, or handle multiple)
    # The spec implies a single cognitive score column for correlation
    if 'score' in df.columns:
        score_col = 'score'
    elif 'score_name' in df.columns:
        # If we have multiple scores, we might need to iterate, but for now assume one
        score_col = df.columns[0] # Fallback
        logger.warning(f"Using first column as score: {score_col}")
    else:
        raise ValueError("No cognitive score column found.")
    
    score_series = df[score_col]
    abundance_df = df[genus_cols]
    
    # 2. CLR Transform
    abundance_clr = clr_transform(abundance_df)
    
    # 3. Calculate Spearman Correlations
    corr_results = calculate_spearman_correlations(abundance_clr, score_series)
    
    # 4. Apply FDR Correction
    corr_results = apply_fdr_correction(corr_results, alpha=alpha)
    
    # 5. Filter Significant
    significant_df = filter_significant_associations(corr_results, alpha=alpha)
    
    # 6. Generate Summary Report
    generate_summary_report(significant_df, output_path)
    
    logger.info("Correlation analysis pipeline complete.")
    return significant_df

def main():
    """
    Main entry point for the correlation analysis script.
    """
    # Setup paths
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / "data" / "processed" / "analysis_dataset.csv"
    output_path = base_dir / "data" / "processed" / "correlation_results.csv"
    
    # Check config for overrides
    if hasattr(config, 'correlation_input'):
        input_path = Path(config.correlation_input)
    if hasattr(config, 'correlation_output'):
        output_path = Path(config.correlation_output)
    
    # Run pipeline
    run_analysis_pipeline(str(input_path), str(output_path))

if __name__ == "__main__":
    main()