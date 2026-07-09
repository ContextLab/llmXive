"""
Generate the final results table for the gut microbiome and circadian rhythm study.

This module loads correlation results (including effect sizes, p-values, and FDR-corrected p-values)
from the analysis module and saves them to a CSV file in the data/outputs directory.
"""
import os
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd

# Import from sibling modules based on the provided API surface
from analysis import load_processed_cohort, load_biom_table, load_metadata, calculate_alpha_diversity, calculate_beta_diversity, calculate_correlations, apply_fdr_correction, run_all_correlations, save_results
from utils.logging_utils import setup_logging, get_logger
from utils.config import get_config

logger = get_logger(__name__)

def load_correlation_results() -> pd.DataFrame:
    """
    Load correlation results from the analysis module.
    
    Returns:
        pd.DataFrame: DataFrame containing correlation results with effect sizes, p-values, and FDR-corrected p-values.
    """
    # Re-run the full analysis pipeline to ensure we have the latest results
    # This matches the approach used in other modules
    config = get_config()
    cohort_path = Path(config.get('paths.cohort', 'data/processed/cohort_merged.csv'))
    
    if not cohort_path.exists():
        raise FileNotFoundError(f"Cohort file not found at {cohort_path}")
    
    logger.info(f"Loading cohort from {cohort_path}")
    cohort = load_processed_cohort(cohort_path)
    
    # Calculate diversity metrics
    logger.info("Calculating alpha diversity metrics")
    alpha_div = calculate_alpha_diversity(cohort)
    
    logger.info("Calculating beta diversity metrics")
    beta_div = calculate_beta_diversity(cohort)
    
    # Run all correlations
    logger.info("Running all correlation analyses")
    results = run_all_correlations(cohort, alpha_div, beta_div)
    
    return results

def generate_results_table(results: pd.DataFrame, output_path: Path) -> None:
    """
    Generate and save the final results table.
    
    Args:
        results: DataFrame containing correlation results.
        output_path: Path where the results CSV will be saved.
    """
    if results.empty:
        logger.warning("No correlation results to save. Creating empty results file.")
        # Create a minimal header-only file to indicate completion
        empty_df = pd.DataFrame(columns=['variable_type', 'variable_name', 'sleep_variable', 'correlation_type', 'effect_size', 'p_value', 'fdr_corrected_p_value', 'sample_size'])
        empty_df.to_csv(output_path, index=False)
        return
    
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sort results by FDR-corrected p-value for easier interpretation
    if 'fdr_corrected_p_value' in results.columns:
        results = results.sort_values('fdr_corrected_p_value')
    
    # Save to CSV
    results.to_csv(output_path, index=False)
    logger.info(f"Results table saved to {output_path}")
    logger.info(f"Total correlations tested: {len(results)}")
    
    # Log summary statistics
    if 'p_value' in results.columns:
        significant_at_005 = (results['p_value'] < 0.05).sum()
        logger.info(f"Significant correlations at p < 0.05: {significant_at_005}")
    
    if 'fdr_corrected_p_value' in results.columns:
        significant_at_fdr = (results['fdr_corrected_p_value'] < 0.05).sum()
        logger.info(f"Significant correlations at FDR < 0.05: {significant_at_fdr}")

def main():
    """Main entry point for generating the results table."""
    # Setup logging
    setup_logging()
    
    parser = argparse.ArgumentParser(description='Generate final results table for gut microbiome and circadian rhythm study')
    parser.add_argument('--output', type=str, default='data/outputs/correlation_results.csv',
                      help='Path to save the results CSV file')
    parser.add_argument('--log-level', type=str, default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='Logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logger.setLevel(getattr(logging, args.log_level))
    
    try:
        # Load correlation results
        logger.info("Loading correlation results from analysis pipeline")
        results = load_correlation_results()
        
        # Generate and save results table
        output_path = Path(args.output)
        logger.info(f"Generating results table at {output_path}")
        generate_results_table(results, output_path)
        
        logger.info("Results table generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error generating results table: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
