import os
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd

from config import get_config
from utils.logging_utils import setup_logging, get_logger

logger = get_logger(__name__)

def load_correlation_results(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the correlation results from the analysis module.
    
    Args:
        input_path: Optional path to the results CSV. If None, uses config default.
        
    Returns:
        DataFrame containing correlation results.
    """
    config = get_config()
    if input_path is None:
        input_path = str(config.OUTPUTS_DIR / "correlation_results_raw.csv")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Correlation results file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} correlation results from {input_path}")
    return df

def generate_results_table(df: pd.DataFrame, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Generate the final results table with effect sizes, p-values, and FDR-corrected p-values.
    
    This function ensures the output table contains all required columns for the final report:
    - Variable 1 (e.g., Shannon Diversity)
    - Variable 2 (e.g., Sleep Duration)
    - Correlation Coefficient (effect size)
    - P-value (raw)
    - P-value (FDR corrected)
    - Method (Spearman/Pearson)
    - N (sample size)
    
    Args:
        df: Input DataFrame with correlation results.
        output_path: Optional path to save the final CSV. If None, uses config default.
        
    Returns:
        DataFrame with the finalized results table.
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.OUTPUTS_DIR / "correlation_results.csv")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Standardize column names if they differ slightly
    column_mapping = {
        'var1': 'variable_1',
        'var2': 'variable_2',
        'correlation': 'correlation_coefficient',
        'p_value': 'p_value_raw',
        'p_value_fdr': 'p_value_fdr_corrected',
        'method': 'statistical_method',
        'n': 'sample_size'
    }
    
    # Rename columns if they exist in the input
    for old, new in column_mapping.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
    
    # Ensure required columns exist
    required_columns = [
        'variable_1', 
        'variable_2', 
        'correlation_coefficient', 
        'p_value_raw', 
        'p_value_fdr_corrected',
        'statistical_method'
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")
    
    # Sort by FDR-corrected p-value for readability
    if 'p_value_fdr_corrected' in df.columns:
        df = df.sort_values(by='p_value_fdr_corrected', ascending=True)
    
    # Round numerical values for presentation
    numerical_cols = ['correlation_coefficient', 'p_value_raw', 'p_value_fdr_corrected']
    for col in numerical_cols:
        if col in df.columns:
            df[col] = df[col].round(6)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved final results table to {output_path} with {len(df)} rows")
    
    return df

def main():
    """
    Main entry point for generating the final results table.
    """
    parser = argparse.ArgumentParser(description="Generate final correlation results table")
    parser.add_argument("--input", type=str, default=None, help="Path to raw correlation results CSV")
    parser.add_argument("--output", type=str, default=None, help="Path to save final results CSV")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    try:
        # Load raw results
        raw_df = load_correlation_results(args.input)
        
        # Generate final table
        final_df = generate_results_table(raw_df, args.output)
        
        # Print summary
        logger.info("--- Results Summary ---")
        logger.info(f"Total correlations tested: {len(final_df)}")
        
        if 'p_value_fdr_corrected' in final_df.columns:
            significant = final_df[final_df['p_value_fdr_corrected'] < 0.05]
            logger.info(f"Significant correlations (FDR < 0.05): {len(significant)}")
            
            if len(significant) > 0:
                logger.info("Top 5 significant results:")
                for _, row in significant.head().iterrows():
                    logger.info(f"  {row['variable_1']} vs {row['variable_2']}: "
                              f"r={row['correlation_coefficient']:.3f}, "
                              f"p(FDR)={row['p_value_fdr_corrected']:.4f}")
        
        logger.info("Results table generation complete.")
        
    except Exception as e:
        logger.error(f"Error generating results table: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()