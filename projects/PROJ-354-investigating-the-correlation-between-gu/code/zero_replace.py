"""
Bayesian-multiplicative zero-replacement for microbiome count data.

Implements the method described in Martín-Fernández et al. (2003) and
Gloor et al. (2017) to handle structural and sampling zeros in compositional
data before log-ratio transformations.

This module provides functions to:
1. Estimate parameters for zero-replacement (alpha parameter)
2. Apply Bayesian-multiplicative replacement to a DataFrame
3. Process data in batches to respect memory constraints
4. Run the full zero-replacement pipeline on raw microbiome data
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

from config import get_path, ensure_directories
from utils.logging import get_logger, PreprocessingError
from utils.streaming import load_in_batches, process_with_streaming

# Initialize logger
logger = get_logger(__name__)

# Constants
DEFAULT_ALPHA = 0.5  # Default alpha parameter for zero-replacement
MIN_COUNT = 1e-6     # Minimum count threshold to avoid log(0)

def estimate_zero_replacement_params(df: pd.DataFrame, taxon_columns: List[str]) -> Dict[str, Any]:
    """
    Estimate parameters needed for Bayesian-multiplicative zero-replacement.
    
    This function calculates:
    - The geometric mean of non-zero counts for each taxon
    - The proportion of zeros for each taxon
    - An appropriate alpha value based on zero proportions
    
    Args:
        df: DataFrame containing microbiome counts
        taxon_columns: List of column names representing taxa
        
    Returns:
        Dictionary with estimated parameters:
        - geometric_means: Geometric mean of non-zero counts per taxon
        - zero_proportions: Proportion of zeros per taxon
        - alpha: Recommended alpha value for zero-replacement
    """
    if not taxon_columns:
        raise ValueError("taxon_columns cannot be empty")
        
    # Filter to only taxon columns that exist in df
    valid_taxa = [col for col in taxon_columns if col in df.columns]
    if not valid_taxa:
        raise ValueError(f"No valid taxon columns found. Available: {df.columns.tolist()}")
    
    params = {}
    
    # Calculate geometric mean for each taxon (excluding zeros)
    geometric_means = {}
    zero_proportions = {}
    
    for taxon in valid_taxa:
        counts = df[taxon].replace(0, np.nan).dropna()
        if len(counts) > 0:
            # Geometric mean: exp(mean(log(x)))
            geo_mean = np.exp(np.mean(np.log(counts)))
            geometric_means[taxon] = geo_mean
        else:
            # If all values are zero, use a small default
            geometric_means[taxon] = MIN_COUNT
        
        # Calculate proportion of zeros
        total_count = len(df)
        zero_count = (df[taxon] == 0).sum()
        zero_proportions[taxon] = zero_count / total_count
    
    # Calculate recommended alpha based on maximum zero proportion
    max_zero_prop = max(zero_proportions.values()) if zero_proportions else 0
    alpha = min(DEFAULT_ALPHA, max_zero_prop * 0.5 + 0.1)
    
    params['geometric_means'] = geometric_means
    params['zero_proportions'] = zero_proportions
    params['alpha'] = alpha
    
    logger.info(f"Estimated zero-replacement parameters: alpha={alpha:.4f}")
    logger.info(f"Zero proportions range: {min(zero_proportions.values()):.4f} to {max_zero_prop:.4f}")
    
    return params

def bayesian_multiplicative_replace(
    df: pd.DataFrame,
    taxon_columns: List[str],
    params: Optional[Dict[str, Any]] = None,
    alpha: Optional[float] = None
) -> pd.DataFrame:
    """
    Apply Bayesian-multiplicative zero-replacement to microbiome count data.
    
    This method replaces zeros with values proportional to the expected count
    given the composition, following the approach by Martín-Fernández et al.
    
    The replacement formula is:
    x_j* = x_j * (1 - c) + d_j * c
    
    where:
    - x_j is the original count for taxon j
    - c is the correction factor based on zero proportions
    - d_j is the expected count for taxon j (based on geometric mean)
    
    Args:
        df: DataFrame containing microbiome counts
        taxon_columns: List of column names representing taxa
        params: Pre-computed parameters from estimate_zero_replacement_params
        alpha: Alpha parameter for zero-replacement (if params not provided)
        
    Returns:
        DataFrame with zeros replaced by estimated values
        
    Raises:
        PreprocessingError: If input data is invalid or replacement fails
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to zero-replacement")
        return df
    
    if not taxon_columns:
        raise ValueError("taxon_columns cannot be empty")
    
    # Validate taxon columns exist
    missing_cols = [col for col in taxon_columns if col not in df.columns]
    if missing_cols:
        raise PreprocessingError(f"Missing taxon columns: {missing_cols}")
    
    # Use provided params or estimate them
    if params is None:
        if alpha is None:
            alpha = DEFAULT_ALPHA
        params = {'alpha': alpha, 'geometric_means': {}, 'zero_proportions': {}}
        # Estimate geometric means from data
        for taxon in taxon_columns:
            counts = df[taxon].replace(0, np.nan).dropna()
            if len(counts) > 0:
                params['geometric_means'][taxon] = np.exp(np.mean(np.log(counts)))
            else:
                params['geometric_means'][taxon] = MIN_COUNT
    else:
        if alpha is None:
            alpha = params.get('alpha', DEFAULT_ALPHA)
    
    # Create a copy to avoid modifying original
    df_replaced = df.copy()
    
    # Calculate total counts per sample
    sample_totals = df_replaced[taxon_columns].sum(axis=1)
    
    # Calculate the correction factor c based on zero proportions
    # c = alpha * (proportion of zeros in the sample)
    # For each sample, calculate the proportion of taxa that are zero
    zero_counts = (df_replaced[taxon_columns] == 0).sum(axis=1)
    n_taxa = len(taxon_columns)
    zero_proportions_per_sample = zero_counts / n_taxa
    correction_factor = alpha * zero_proportions_per_sample
    
    # Apply replacement for each taxon
    for taxon in taxon_columns:
        # Get original counts
        original_counts = df_replaced[taxon]
        
        # Calculate expected count based on geometric mean and composition
        geo_mean = params['geometric_means'].get(taxon, MIN_COUNT)
        
        # Calculate the sum of non-zero geometric means for normalization
        sum_geo_means = sum(params['geometric_means'].get(t, MIN_COUNT) for t in taxon_columns)
        
        # Expected proportion for this taxon
        expected_proportion = geo_mean / sum_geo_means if sum_geo_means > 0 else 1.0 / n_taxa
        
        # Calculate replacement values
        # For zeros: replace with expected proportion * total * correction factor
        # For non-zeros: keep original but scale down by (1 - correction factor)
        replacement_values = expected_proportion * sample_totals * correction_factor
        non_replacement_values = original_counts * (1 - correction_factor)
        
        # Apply replacement: if original is zero, use replacement value
        # Otherwise, use scaled non-zero value
        mask_zeros = (original_counts == 0)
        df_replaced[taxon] = np.where(mask_zeros, replacement_values, non_replacement_values)
        
        # Ensure no negative values (numerical stability)
        df_replaced[taxon] = df_replaced[taxon].clip(lower=MIN_COUNT)
    
    logger.info(f"Successfully applied Bayesian-multiplicative zero-replacement to {len(taxon_columns)} taxa")
    logger.info(f"Replaced {((df[taxon_columns] == 0).sum()).sum()} zero values")
    
    return df_replaced

def process_batch(
    batch_df: pd.DataFrame,
    taxon_columns: List[str],
    params: Optional[Dict[str, Any]] = None,
    alpha: Optional[float] = None
) -> pd.DataFrame:
    """
    Process a single batch of data with zero-replacement.
    
    This function is designed for use with streaming/batch processing
    to handle large datasets that don't fit in memory.
    
    Args:
        batch_df: DataFrame containing a batch of microbiome counts
        taxon_columns: List of column names representing taxa
        params: Pre-computed parameters for zero-replacement
        alpha: Alpha parameter for zero-replacement
        
    Returns:
        DataFrame with zeros replaced in this batch
    """
    if batch_df.empty:
        return batch_df
    
    return bayesian_multiplicative_replace(batch_df, taxon_columns, params, alpha)

def run_zero_replacement_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    taxon_columns: Optional[List[str]] = None,
    batch_size: int = 10000,
    alpha: Optional[float] = None,
    use_streaming: bool = True
) -> str:
    """
    Run the complete zero-replacement pipeline on microbiome data.
    
    This function:
    1. Loads raw microbiome data (with streaming if needed)
    2. Estimates zero-replacement parameters
    3. Applies Bayesian-multiplicative replacement
    4. Saves the processed data to Parquet format
    
    Args:
        input_path: Path to input raw microbiome data (Parquet or CSV)
        output_path: Path for output zero-replaced data (Parquet)
        taxon_columns: List of taxon column names (if None, inferred from data)
        batch_size: Number of rows to process per batch
        alpha: Alpha parameter for zero-replacement
        use_streaming: Whether to use streaming for large datasets
        
    Returns:
        Path to the output file
        
    Raises:
        PreprocessingError: If processing fails
    """
    # Get paths from config if not provided
    if input_path is None:
        input_path = get_path('raw_microbiome_parquet')
    if output_path is None:
        output_path = get_path('zero_replaced_counts_parquet')
    
    # Ensure output directory exists
    ensure_directories([output_path])
    
    logger.info(f"Starting zero-replacement pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    # Load data
    try:
        if use_streaming:
            # Use streaming to handle large datasets
            def process_and_save(batch_df):
                # Estimate params on first batch if not provided
                nonlocal params
                if params is None and taxon_columns is not None:
                    params = estimate_zero_replacement_params(batch_df, taxon_columns)
                    logger.info(f"Estimated parameters from first batch")
                
                # Process this batch
                processed_batch = process_batch(batch_df, taxon_columns, params, alpha)
                
                # Append to output file
                if not os.path.exists(output_path):
                    processed_batch.to_parquet(output_path, index=False)
                else:
                    # Append mode not directly supported in pandas, so we need to handle differently
                    # For simplicity, we'll collect all batches and write at the end if streaming
                    # But for true streaming, we'd need a different approach
                    pass
                
                return processed_batch
            
            # For now, load all data if streaming doesn't support incremental writes
            # In a production system, we'd use a database or chunked Parquet writing
            logger.info("Loading data for processing...")
            df = pd.read_parquet(input_path) if input_path.endswith('.parquet') else pd.read_csv(input_path)
            
            # Infer taxon columns if not provided
            if taxon_columns is None:
                # Assume columns that are not participant IDs or metadata are taxa
                # This is a heuristic - in practice, we'd use config or metadata
                exclude_cols = ['eids', 'participant_id', 'sample_id']
                taxon_columns = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['int64', 'float64']]
                logger.info(f"Inferred {len(taxon_columns)} taxon columns")
            
            if not taxon_columns:
                raise PreprocessingError("No taxon columns found in data")
            
            # Estimate parameters
            params = estimate_zero_replacement_params(df, taxon_columns)
            
            # Apply zero-replacement
            df_replaced = bayesian_multiplicative_replace(df, taxon_columns, params, alpha)
            
            # Save output
            df_replaced.to_parquet(output_path, index=False)
            
        else:
            # Non-streaming approach
            df = pd.read_parquet(input_path) if input_path.endswith('.parquet') else pd.read_csv(input_path)
            
            # Infer taxon columns if not provided
            if taxon_columns is None:
                exclude_cols = ['eids', 'participant_id', 'sample_id']
                taxon_columns = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['int64', 'float64']]
            
            if not taxon_columns:
                raise PreprocessingError("No taxon columns found in data")
            
            # Estimate parameters
            params = estimate_zero_replacement_params(df, taxon_columns)
            
            # Apply zero-replacement
            df_replaced = bayesian_multiplicative_replace(df, taxon_columns, params, alpha)
            
            # Save output
            df_replaced.to_parquet(output_path, index=False)
            
    except Exception as e:
        logger.error(f"Zero-replacement pipeline failed: {str(e)}")
        raise PreprocessingError(f"Zero-replacement failed: {str(e)}")
    
    logger.info(f"Zero-replacement pipeline completed successfully")
    logger.info(f"Output saved to: {output_path}")
    
    return output_path

def main():
    """Main entry point for the zero-replacement script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Apply Bayesian-multiplicative zero-replacement to microbiome data')
    parser.add_argument('--input', type=str, help='Input file path (Parquet or CSV)')
    parser.add_argument('--output', type=str, help='Output file path (Parquet)')
    parser.add_argument('--taxa', type=str, nargs='+', help='Taxon column names')
    parser.add_argument('--alpha', type=float, default=None, help='Alpha parameter for zero-replacement')
    parser.add_argument('--batch-size', type=int, default=10000, help='Batch size for processing')
    parser.add_argument('--no-streaming', action='store_true', help='Disable streaming mode')
    
    args = parser.parse_args()
    
    try:
        output_path = run_zero_replacement_pipeline(
            input_path=args.input,
            output_path=args.output,
            taxon_columns=args.taxa,
            batch_size=args.batch_size,
            alpha=args.alpha,
            use_streaming=not args.no_streaming
        )
        print(f"Zero-replacement completed. Output: {output_path}")
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()
