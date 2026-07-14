"""
Benjamini-Hochberg False Discovery Rate (FDR) correction for multiple hypothesis testing.

This module implements the BH procedure to adjust p-values across multiple outcome tests
(Depression, Anxiety, PTSD) derived from the regression analysis.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def load_regression_results(input_path: str) -> pd.DataFrame:
    """
    Load the regression results CSV containing p-values.
    
    Args:
        input_path: Path to the regression results CSV file.
        
    Returns:
        DataFrame containing the regression results.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(path)
    
    # Expected columns based on T020/T021/T022 output
    required_cols = ['outcome', 'term', 'coef', 'std_err', 'p_value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns in regression results: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} regression results from {input_path}")
    return df

def apply_benjamini_hochberg(p_values: pd.Series, alpha: float = 0.05) -> Tuple[pd.Series, pd.Series]:
    """
    Apply the Benjamini-Hochberg FDR correction to a series of p-values.
    
    The BH procedure controls the expected proportion of incorrectly rejected 
    null hypotheses (false discoveries).
    
    Args:
        p_values: Series of raw p-values.
        alpha: Significance level for FDR (default 0.05).
        
    Returns:
        Tuple containing:
            - adjusted_p_values: Series of BH-adjusted p-values.
            - is_significant: Boolean series indicating significance at level alpha.
            
    Note:
        The algorithm:
        1. Sort p-values in ascending order: p(1) <= p(2) <= ... <= p(m)
        2. Calculate adjusted p-values: p_adj(i) = p(i) * m / i
        3. Ensure monotonicity: p_adj(i) = min(p_adj(i), p_adj(i+1), ..., p_adj(m))
        4. Cap at 1.0
    """
    if len(p_values) == 0:
        return pd.Series(dtype=float), pd.Series(dtype=bool)
        
    m = len(p_values)
    logger.info(f"Applying BH correction to {m} tests")
    
    # Create a DataFrame to track original indices
    df_p = pd.DataFrame({'p_raw': p_values.values}, index=p_values.index)
    df_p['rank'] = df_p['p_raw'].rank(method='min').astype(int)
    
    # Sort by p-value
    df_sorted = df_p.sort_values('p_raw')
    
    # Calculate BH adjusted p-values: p * m / rank
    df_sorted['p_adj'] = df_sorted['p_raw'] * m / df_sorted['rank']
    
    # Ensure monotonicity (cumulative minimum from the end)
    # We need to go from largest rank to smallest, taking the min of current and subsequent
    df_sorted['p_adj'] = df_sorted['p_adj'].cummax().iloc[::-1].cummin().iloc[::-1]
    
    # Cap at 1.0
    df_sorted['p_adj'] = df_sorted['p_adj'].clip(upper=1.0)
    
    # Sort back to original order
    df_result = df_sorted.sort_index()
    
    adjusted_p_values = df_result['p_adj']
    is_significant = adjusted_p_values <= alpha
    
    return adjusted_p_values, is_significant

def add_fdr_correction_to_results(df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Add FDR-corrected p-values and significance flags to the regression results.
    
    Args:
        df: DataFrame with regression results (must have 'p_value' column).
        alpha: Significance level for FDR.
        
    Returns:
        DataFrame with added columns: 'p_value_fdr', 'is_significant_fdr'
    """
    if 'p_value' not in df.columns:
        raise ValueError("DataFrame must contain 'p_value' column")
        
    # Apply BH correction
    adj_pvals, is_sig = apply_benjamini_hochberg(df['p_value'], alpha=alpha)
    
    df_out = df.copy()
    df_out['p_value_fdr'] = adj_pvals
    df_out['is_significant_fdr'] = is_sig
    
    logger.info(f"Added FDR correction (alpha={alpha}) to {len(df_out)} rows")
    return df_out

def main():
    """
    Main entry point for running FDR correction on regression results.
    
    Reads from data/results/regression_results.csv (if it exists from T024)
    or expects the file to be provided. For this task, we assume the file
    exists as T024 is the subsequent step that saves the final results.
    
    This script:
    1. Loads regression results.
    2. Applies BH FDR correction.
    3. Saves the updated results to a new file (intermediate) or prepares for T024.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths
    project_root = Path(__file__).resolve().parents[2]
    results_dir = project_root / 'data' / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    input_file = results_dir / 'regression_results_raw.csv'
    output_file = results_dir / 'regression_results.csv'
    
    # Check for input file
    # Note: In a real pipeline, T024 would save the raw results first.
    # Since T023 runs before T024 in the logical flow of "calculate then save",
    # we expect the raw results to be generated by the models step or passed in.
    # For this implementation, we look for a raw file or the standard output file.
    
    if not input_file.exists():
        # Fallback: check if the standard file exists (in case of re-run)
        if output_file.exists():
            logger.warning(f"Raw file {input_file} not found. Using {output_file} as input.")
            input_file = output_file
        else:
            # If no file exists, we cannot proceed.
            # In a real pipeline, this would be a dependency error.
            logger.error(f"Input file not found: {input_file}. Cannot perform FDR correction.")
            # Create a dummy file for demonstration if in a test environment? 
            # No, per constraints: "If no real source is reachable, return verdict: failed".
            # However, this is a code artifact. The code must be runnable.
            # We will raise an error to indicate the pipeline step cannot run without data.
            raise FileNotFoundError(
                f"Regression results file not found at {input_file}. "
                "Ensure T020-T022 have run and saved results."
            )
    
    try:
        df = load_regression_results(str(input_file))
        
        # Apply correction
        df_corrected = add_fdr_correction_to_results(df, alpha=0.05)
        
        # Save results
        # The task says "attach adjusted p-values to the results".
        # T024 will save this to data/results/regression_results.csv.
        # We save to the final location to satisfy the pipeline flow.
        df_corrected.to_csv(output_file, index=False)
        
        logger.info(f"Successfully saved FDR-corrected results to {output_file}")
        
        # Print summary
        significant_count = df_corrected['is_significant_fdr'].sum()
        logger.info(f"Significant results at alpha=0.05 (FDR): {significant_count} / {len(df_corrected)}")
        
    except Exception as e:
        logger.error(f"Error during FDR correction: {e}")
        raise

if __name__ == '__main__':
    main()