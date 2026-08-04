"""
Module to generate the final results table for the gut microbiome and circadian rhythm study.

This module aggregates correlation results, effect sizes, p-values, and FDR-corrected p-values
into a single CSV file as required by T028.
"""
import os
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd

# Import from sibling modules as per API surface
from analysis import load_processed_cohort, calculate_correlations, apply_fdr_correction, run_all_correlations
from utils.logging_utils import setup_logging, get_logger
from config import get_config

logger = get_logger(__name__)

def load_correlation_results(results_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load correlation results from the analysis module.
    
    Args:
        results_path: Optional path to the results file. If None, uses the default path from config.
        
    Returns:
        DataFrame containing correlation results.
    """
    config = get_config()
    if results_path is None:
        # Default path for intermediate results if they exist
        default_path = Path(config.data_dir) / "processed" / "correlation_results_raw.csv"
        if default_path.exists():
            logger.info(f"Loading existing correlation results from {default_path}")
            return pd.read_csv(default_path)
        else:
            # If no pre-computed results, we must compute them
            logger.info("No pre-computed results found. Running correlation analysis...")
            return run_all_correlations()
    else:
        path = Path(results_path)
        if not path.exists():
            raise FileNotFoundError(f"Results file not found at {results_path}")
        logger.info(f"Loading correlation results from {results_path}")
        return pd.read_csv(results_path)

def generate_results_table(
    correlations_df: pd.DataFrame,
    output_path: str,
    include_fdr: bool = True
) -> pd.DataFrame:
    """
    Generate the final results table with effect sizes, p-values, and FDR-corrected p-values.
    
    Args:
        correlations_df: DataFrame containing raw correlation results.
        output_path: Path where the final CSV will be saved.
        include_fdr: Whether to include FDR-corrected p-values.
        
    Returns:
        The final results DataFrame.
    """
    logger.info(f"Generating results table with {len(correlations_df)} rows")
    
    # Ensure we have the necessary columns
    required_cols = ['metric', 'sleep_variable', 'correlation', 'p_value']
    missing_cols = [col for col in required_cols if col not in correlations_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in correlation results: {missing_cols}")
    
    # Create the final results DataFrame
    results_df = pd.DataFrame()
    results_df['metric'] = correlations_df['metric']
    results_df['sleep_variable'] = correlations_df['sleep_variable']
    results_df['effect_size'] = correlations_df['correlation']
    results_df['p_value'] = correlations_df['p_value']
    
    # Apply FDR correction if requested
    if include_fdr:
        if 'p_value' in correlations_df.columns:
            fdr_results = apply_fdr_correction(correlations_df['p_value'].values)
            results_df['fdr_p_value'] = fdr_results['fdr_p_value']
            results_df['is_significant_fdr'] = fdr_results['is_significant']
            logger.info(f"Applied FDR correction. Significant results (FDR < 0.05): {results_df['is_significant_fdr'].sum()}")
        else:
            logger.warning("No p_value column found, skipping FDR correction")
    
    # Sort by p-value for readability
    results_df = results_df.sort_values('p_value', ascending=True)
    
    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved results table to {output_path}")
    
    return results_df

def main():
    """Main entry point for generating the final results table."""
    parser = argparse.ArgumentParser(description="Generate final correlation results table")
    parser.add_argument(
        "--input", 
        type=str, 
        default=None,
        help="Path to input correlation results CSV (optional, will compute if not provided)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="Path to output results CSV (defaults to config output path)"
    )
    parser.add_argument(
        "--no-fdr",
        action="store_true",
        help="Skip FDR correction"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    config = get_config()
    output_path = args.output or str(Path(config.output_dir) / "correlation_results.csv")
    
    try:
        # Load or compute correlations
        correlations_df = load_correlation_results(args.input)
        
        # Generate results table
        results_df = generate_results_table(
            correlations_df,
            output_path,
            include_fdr=not args.no_fdr
        )
        
        # Print summary
        print(f"\nFinal Results Summary:")
        print(f"Total correlations tested: {len(results_df)}")
        if 'is_significant_fdr' in results_df.columns:
            print(f"Significant correlations (FDR < 0.05): {results_df['is_significant_fdr'].sum()}")
        print(f"\nResults saved to: {output_path}")
        
        # Display top 10 results
        print("\nTop 10 Results (by p-value):")
        print(results_df.head(10).to_string(index=False))
        
    except Exception as e:
        logger.error(f"Failed to generate results table: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()