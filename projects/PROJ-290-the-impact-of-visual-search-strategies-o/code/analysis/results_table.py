"""
Generate statistical results tables for the visual search study.

This module aggregates results from the primary LMM analysis (continuous predictor)
and the exploratory cluster-based analysis to produce a comprehensive results table
with estimates, standard errors, t-values, p-values, and adjusted p-values.

Output: results/statistical_results_table.csv
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from statsmodels.stats.multitest import multipletests

# Import from existing API surface
from config import get_config
from utils.logging import get_logger
from analysis.lmm import (
    get_logger_wrapper, 
    load_processed_features, 
    fit_lmm_with_fallback, 
    extract_results_table, 
    run_primary_analysis, 
    run_exploratory_analysis,
    run_permutation_test
)

def get_logger_wrapper(name: str) -> logging.Logger:
    """Get a logger for this module."""
    return get_logger(name)

def load_lmm_results(
    primary_results_path: Path,
    exploratory_results_path: Optional[Path] = None
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """
    Load LMM results from saved JSON files.
    
    Args:
        primary_results_path: Path to primary analysis results (T029a)
        exploratory_results_path: Path to exploratory analysis results (T029b), optional
    
    Returns:
        Tuple of (primary_results, exploratory_results)
    """
    logger = get_logger("results_table")
    
    if not primary_results_path.exists():
        raise FileNotFoundError(f"Primary results file not found: {primary_results_path}")
    
    with open(primary_results_path, 'r') as f:
        primary_results = json.load(f)
    
    exploratory_results = None
    if exploratory_results_path and exploratory_results_path.exists():
        with open(exploratory_results_path, 'r') as f:
            exploratory_results = json.load(f)
        logger.info(f"Loaded exploratory results from {exploratory_results_path}")
    else:
        logger.warning(f"Exploratory results not found at {exploratory_results_path}")
    
    return primary_results, exploratory_results

def extract_coefficients_table(
    model_results: Dict[str, Any],
    model_type: str = "primary"
) -> pd.DataFrame:
    """
    Extract coefficients table from LMM results.
    
    Args:
        model_results: Dictionary containing model results
        model_type: Type of model ('primary' or 'exploratory')
    
    Returns:
        DataFrame with coefficients, SE, t-values, and p-values
    """
    logger = get_logger("results_table")
    
    if 'fixed_effects' not in model_results:
        logger.warning(f"No fixed effects found in {model_type} results")
        return pd.DataFrame()
    
    fixed_effects = model_results['fixed_effects']
    
    # Convert to DataFrame
    df = pd.DataFrame(fixed_effects)
    
    # Standardize column names if needed
    expected_cols = ['term', 'estimate', 'std_error', 't_value', 'p_value']
    if df.shape[1] == len(expected_cols):
        df.columns = expected_cols
    elif 'parameter' in df.columns:
        df = df.rename(columns={'parameter': 'term'})
    
    # Ensure numeric columns
    numeric_cols = ['estimate', 'std_error', 't_value', 'p_value']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Add model type column
    df['model_type'] = model_type
    
    # Add effect description
    if model_type == 'primary':
        df['description'] = 'Primary: Continuous Fixation Ratio (Eye/Mouth)'
    else:
        df['description'] = 'Exploratory: Cluster-based Processing Strategy'
    
    logger.info(f"Extracted {len(df)} coefficients from {model_type} model")
    return df

def compute_adjusted_pvalues(
    df: pd.DataFrame,
    method: str = 'fdr_bh'
) -> pd.DataFrame:
    """
    Compute adjusted p-values for multiple comparisons.
    
    Args:
        df: DataFrame with p-values
        method: Correction method ('fdr_bh', 'bonferroni', etc.)
    
    Returns:
        DataFrame with adjusted p-values added
    """
    logger = get_logger("results_table")
    
    if 'p_value' not in df.columns or len(df) == 0:
        return df
    
    p_values = df['p_value'].dropna().values
    if len(p_values) == 0:
        logger.warning("No p-values to adjust")
        return df
    
    try:
        # Apply multiple comparison correction
        reject, p_adjusted, _, _ = multipletests(p_values, alpha=0.05, method=method)
        
        # Create mapping back to original indices
        valid_indices = df['p_value'].notna().values
        p_adjusted_full = np.full(len(df), np.nan)
        p_adjusted_full[valid_indices] = p_adjusted
        
        df['p_adjusted'] = p_adjusted_full
        df['significant_after_correction'] = reject if len(reject) == len(p_values) else False
        
        logger.info(f"Applied {method} correction to {len(p_values)} p-values")
    except Exception as e:
        logger.error(f"Failed to compute adjusted p-values: {e}")
        df['p_adjusted'] = np.nan
    
    return df

def generate_combined_results_table(
    primary_results: Dict[str, Any],
    exploratory_results: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Generate combined results table from primary and exploratory analyses.
    
    Args:
        primary_results: Primary LMM results
        exploratory_results: Exploratory LMM results (optional)
    
    Returns:
        Combined DataFrame with all statistical results
    """
    logger = get_logger("results_table")
    
    tables = []
    
    # Extract primary results
    primary_table = extract_coefficients_table(primary_results, model_type='primary')
    if not primary_table.empty:
        tables.append(primary_table)
        logger.info(f"Primary table has {len(primary_table)} rows")
    
    # Extract exploratory results if available
    if exploratory_results:
        exploratory_table = extract_coefficients_table(exploratory_results, model_type='exploratory')
        if not exploratory_table.empty:
            tables.append(exploratory_table)
            logger.info(f"Exploratory table has {len(exploratory_table)} rows")
    
    if not tables:
        logger.warning("No tables extracted from results")
        return pd.DataFrame()
    
    # Combine tables
    combined = pd.concat(tables, ignore_index=True)
    
    # Compute adjusted p-values
    combined = compute_adjusted_pvalues(combined, method='fdr_bh')
    
    # Reorder columns for clarity
    cols = ['model_type', 'description', 'term', 'estimate', 'std_error', 
            't_value', 'p_value', 'p_adjusted', 'significant_after_correction']
    existing_cols = [c for c in cols if c in combined.columns]
    combined = combined[existing_cols]
    
    # Round numeric columns
    numeric_cols = ['estimate', 'std_error', 't_value', 'p_value', 'p_adjusted']
    for col in numeric_cols:
        if col in combined.columns:
            combined[col] = combined[col].round(4)
    
    logger.info(f"Generated combined results table with {len(combined)} rows")
    return combined

def generate_results_summary(
    combined_table: pd.DataFrame,
    permutation_results: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a summary dictionary of key findings.
    
    Args:
        combined_table: Combined results DataFrame
        permutation_results: Permutation test results (optional)
    
    Returns:
        Dictionary with summary statistics
    """
    logger = get_logger("results_table")
    
    summary = {
        'primary_analysis': {},
        'exploratory_analysis': {},
        'permutation_test': None,
        'total_tests': len(combined_table),
        'significant_tests': 0,
        'significant_after_correction': 0
    }
    
    if not combined_table.empty:
        primary = combined_table[combined_table['model_type'] == 'primary']
        if not primary.empty:
            summary['primary_analysis'] = {
                'coefficient': float(primary[primary['term'] == 'continuous_ratio']['estimate'].iloc[0]) 
                               if not primary[primary['term'] == 'continuous_ratio'].empty else None,
                'p_value': float(primary[primary['term'] == 'continuous_ratio']['p_value'].iloc[0])
                           if not primary[primary['term'] == 'continuous_ratio'].empty else None,
                'significant': bool(primary[primary['term'] == 'continuous_ratio']['significant_after_correction'].iloc[0])
                               if not primary[primary['term'] == 'continuous_ratio'].empty else False
            }
        
        exploratory = combined_table[combined_table['model_type'] == 'exploratory']
        if not exploratory.empty:
            summary['exploratory_analysis'] = {
                'n_terms': len(exploratory),
                'significant_terms': int(exploratory['significant_after_correction'].sum())
            }
        
        summary['significant_tests'] = int(combined_table['significant_after_correction'].sum())
        summary['significant_after_correction'] = summary['significant_tests']
    
    if permutation_results:
        summary['permutation_test'] = {
            'observed_t': permutation_results.get('observed_t'),
            'null_distribution_mean': permutation_results.get('null_mean'),
            'p_value': permutation_results.get('p_value'),
            'iterations': permutation_results.get('n_iterations')
        }
    
    return summary

def save_results_table(
    combined_table: pd.DataFrame,
    summary: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save results table and summary to files.
    
    Args:
        combined_table: Combined results DataFrame
        summary: Summary dictionary
        output_path: Path to save the CSV file
    """
    logger = get_logger("results_table")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save CSV table
    combined_table.to_csv(output_path, index=False)
    logger.info(f"Saved results table to {output_path}")
    
    # Save summary JSON
    summary_path = output_path.with_suffix('.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info(f"Saved summary to {summary_path}")

def run_results_table_generation(
    config: Optional[Dict[str, Any]] = None
) -> Tuple[Path, Dict[str, Any]]:
    """
    Main function to generate the statistical results table.
    
    This function:
    1. Loads primary and exploratory LMM results
    2. Extracts coefficients tables
    3. Computes adjusted p-values
    4. Generates and saves the combined results table
    
    Args:
        config: Optional configuration dictionary
    
    Returns:
        Tuple of (output_path, summary)
    """
    logger = get_logger("results_table")
    logger.info("Starting results table generation")
    
    # Load configuration
    if config is None:
        config = get_config()
    
    # Define paths
    results_dir = Path(config['paths']['results'])
    primary_results_path = results_dir / 'lmm_continuous.json'
    exploratory_results_path = results_dir / 'lmm_cluster.json'
    permutation_results_path = results_dir / 'permutation_test.json'
    output_path = results_dir / 'statistical_results_table.csv'
    
    # Load results
    try:
        primary_results, exploratory_results = load_lmm_results(
            primary_results_path, 
            exploratory_results_path
        )
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # Load permutation results if available
    permutation_results = None
    if permutation_results_path.exists():
        with open(permutation_results_path, 'r') as f:
            permutation_results = json.load(f)
        logger.info("Loaded permutation test results")
    
    # Generate combined table
    combined_table = generate_combined_results_table(primary_results, exploratory_results)
    
    # Generate summary
    summary = generate_results_summary(combined_table, permutation_results)
    
    # Save results
    save_results_table(combined_table, summary, output_path)
    
    logger.info("Results table generation completed successfully")
    return output_path, summary

def main() -> int:
    """
    Entry point for the results table generation script.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger = get_logger("results_table_main")
    try:
        config = get_config()
        output_path, summary = run_results_table_generation(config)
        
        logger.info(f"Results table saved to: {output_path}")
        logger.info(f"Summary: {json.dumps(summary, indent=2, default=str)}")
        
        return 0
    except Exception as e:
        logger.error(f"Error generating results table: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == '__main__':
    sys.exit(main())
