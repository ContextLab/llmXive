"""
Bayesian-multiplicative zero-replacement for microbiome count data.

This module implements the Bayesian-multiplicative replacement method
to handle zero counts in compositional microbiome data before log-ratio
transformations. This approach avoids the bias introduced by fixed
pseudocounts.

The algorithm:
1. Estimates the expected counts for zero cells based on the Dirichlet
   posterior of the non-zero observations.
2. Replaces zeros with small positive values proportional to the
   estimated expectations.
3. Adjusts non-zero counts to maintain the total sum (multiplicative).
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.special import digamma, gamma
from scipy.stats import dirichlet

from config import get_path, ensure_directories
from utils.logging import get_logger, log_exception, PreprocessingError
from utils.streaming import load_in_batches, estimate_memory_usage

# Initialize logger
logger = get_logger(__name__)

# Constants
DEFAULT_ZERO_REPLACEMENT_ALPHA = 0.5  # Dirichlet prior concentration
DEFAULT_BATCH_SIZE = 10000  # Rows per batch for memory efficiency
EPSILON = 1e-10  # Small value to prevent log(0)

def estimate_zero_replacement_params(
    df: pd.DataFrame, 
    taxon_columns: List[str],
    alpha: float = DEFAULT_ZERO_REPLACEMENT_ALPHA
) -> Dict[str, float]:
    """
    Estimate Dirichlet parameters for zero replacement from non-zero data.
    
    Args:
        df: DataFrame with raw counts
        taxon_columns: List of columns containing taxon counts
        alpha: Dirichlet prior concentration parameter
        
    Returns:
        Dictionary mapping taxon names to estimated concentration parameters
    """
    if not taxon_columns:
        raise ValueError("No taxon columns provided for zero replacement")
        
    # Filter to non-zero rows for estimation
    non_zero_mask = (df[taxon_columns] > 0).all(axis=1)
    non_zero_data = df.loc[non_zero_mask, taxon_columns]
    
    if len(non_zero_data) == 0:
        logger.warning("No non-zero rows found. Using prior only.")
        return {col: alpha for col in taxon_columns}
    
    # Calculate geometric means for non-zero data
    # This approximates the Dirichlet parameters
    log_data = np.log(non_zero_data + EPSILON)
    log_means = log_data.mean(axis=0)
    
    # Estimate concentration parameters using method of moments
    # alpha_i = exp(log_mean_i) * (sum_alpha / sum(exp(log_mean)))
    # We use the prior alpha as a baseline
    concentrations = {}
    total_sum = non_zero_data.sum().sum()
    if total_sum == 0:
        return {col: alpha for col in taxon_columns}
        
    for col in taxon_columns:
        # Use geometric mean as a proxy for expected proportion
        geo_mean = np.exp(log_means[col])
        # Scale by prior
        concentrations[col] = max(alpha, geo_mean * alpha)
        
    return concentrations

def bayesian_multiplicative_replace(
    counts: np.ndarray,
    concentrations: Dict[str, float],
    alpha: float = DEFAULT_ZERO_REPLACEMENT_ALPHA
) -> np.ndarray:
    """
    Apply Bayesian-multiplicative zero-replacement to count matrix.
    
    Args:
        counts: 2D numpy array of counts (rows=participants, cols=taxa)
        concentrations: Dictionary of estimated Dirichlet concentrations
        alpha: Dirichlet prior concentration
        
    Returns:
        2D numpy array with zeros replaced
    """
    if counts.ndim != 2:
        raise ValueError("Counts must be 2D array")
        
    result = counts.copy().astype(float)
    n_rows, n_cols = result.shape
    
    # Convert concentrations to array in correct order
    conc_array = np.array([concentrations.get(f"taxon_{i}", alpha) 
                          for i in range(n_cols)])
    
    # Find zero positions
    zero_mask = result == 0
    non_zero_mask = ~zero_mask
    
    # Calculate expected values for zeros using Dirichlet posterior
    # E[X_i | X_j > 0] = (alpha_i + sum_{j!=i} X_j) / (sum_alpha + sum_all_X)
    row_sums = result.sum(axis=1, keepdims=True)
    row_sums_zero = np.where(row_sums == 0, 1, row_sums)  # Avoid division by zero
    
    # For each zero cell, estimate replacement value
    for i in range(n_rows):
        row_data = result[i, :]
        row_zeros = zero_mask[i, :]
        row_nonzeros = non_zero_mask[i, :]
        
        if not row_zeros.any():
            continue  # No zeros to replace
            
        if not row_nonzeros.any():
            # All zeros - use prior distribution
            total_conc = conc_array.sum()
            expected_proportions = conc_array / total_conc
            row_sum = row_data.sum() if row_data.sum() > 0 else 1.0
            result[i, row_zeros] = expected_proportions[row_zeros] * row_sum
            continue
            
        # Calculate posterior parameters
        posterior_conc = conc_array.copy()
        posterior_conc[row_nonzeros] += row_data[row_nonzeros]
        
        # Expected value for zero cells
        total_posterior = posterior_conc.sum()
        expected_values = posterior_conc / total_posterior
        
        # Multiply by row sum to get counts
        row_sum = row_data.sum() if row_data.sum() > 0 else 1.0
        result[i, row_zeros] = expected_values[row_zeros] * row_sum
        
        # Apply multiplicative adjustment to non-zero cells
        # This maintains the total sum constraint
        adjustment = (row_sum - result[i, row_zeros].sum()) / result[i, row_nonzeros].sum() if result[i, row_nonzeros].sum() > 0 else 1.0
        result[i, row_nonzeros] *= adjustment
    
    # Ensure no zeros remain and all values are positive
    result = np.maximum(result, EPSILON)
    
    return result

def process_batch(
    batch_df: pd.DataFrame,
    taxon_columns: List[str],
    concentrations: Optional[Dict[str, float]] = None,
    alpha: float = DEFAULT_ZERO_REPLACEMENT_ALPHA
) -> pd.DataFrame:
    """
    Process a single batch of data with zero replacement.
    
    Args:
        batch_df: DataFrame batch to process
        taxon_columns: List of taxon column names
        concentrations: Pre-computed concentrations (optional)
        alpha: Dirichlet prior concentration
        
    Returns:
        Processed DataFrame with zeros replaced
    """
    if concentrations is None:
        concentrations = estimate_zero_replacement_params(batch_df, taxon_columns, alpha)
    
    # Extract count matrix
    count_matrix = batch_df[taxon_columns].values.astype(float)
    
    # Apply zero replacement
    replaced_matrix = bayesian_multiplicative_replace(count_matrix, concentrations, alpha)
    
    # Update DataFrame
    result_df = batch_df.copy()
    for i, col in enumerate(taxon_columns):
        result_df[col] = replaced_matrix[:, i]
        
    return result_df

def run_zero_replacement_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    taxon_columns: Optional[List[str]] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    alpha: float = DEFAULT_ZERO_REPLACEMENT_ALPHA
) -> Dict[str, Any]:
    """
    Run the complete zero replacement pipeline.
    
    Args:
        input_path: Path to input parquet file (optional, uses config if None)
        output_path: Path to output parquet file (optional, uses config if None)
        taxon_columns: List of taxon column names (optional, detected if None)
        batch_size: Number of rows per batch
        alpha: Dirichlet prior concentration
        
    Returns:
        Dictionary with processing statistics
    """
    # Use config paths if not provided
    if input_path is None:
        input_path = str(get_path("data/processed/cohort_filtered.parquet"))
    if output_path is None:
        output_path = str(get_path("data/processed/zero_replaced_counts.parquet"))
    
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise PreprocessingError(f"Input file not found: {input_path}")
    
    ensure_directories([output_path.parent])
    
    logger.info(f"Starting zero replacement pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    # Read schema to identify taxon columns if not provided
    if taxon_columns is None:
        logger.info("Auto-detecting taxon columns...")
        # Read first batch to detect columns
        first_batch = next(load_in_batches(str(input_path), batch_size=1000))
        # Assume columns containing 'genus' or 'species' or starting with 'taxon_'
        taxon_columns = [col for col in first_batch.columns 
                       if 'genus' in col.lower() or 'species' in col.lower() 
                       or col.startswith('taxon_')]
        
        if not taxon_columns:
            # Fallback: all numeric columns except metadata
            metadata_cols = ['participant_id', 'age', 'sex', 'bmi', 'diet_score']
            taxon_columns = [col for col in first_batch.columns 
                           if col not in metadata_cols and first_batch[col].dtype in ['int64', 'float64', 'int32', 'float32']]
        
        logger.info(f"Detected {len(taxon_columns)} taxon columns")
    
    # Estimate parameters from first batch
    logger.info("Estimating zero replacement parameters from first batch...")
    first_batch = next(load_in_batches(str(input_path), batch_size=1000))
    concentrations = estimate_zero_replacement_params(first_batch, taxon_columns, alpha)
    
    # Process all batches
    logger.info("Processing batches with zero replacement...")
    total_rows = 0
    zero_counts = {col: 0 for col in taxon_columns}
    
    # Write output in batches
    writer = None
    
    for batch_idx, batch_df in enumerate(load_in_batches(str(input_path), batch_size=batch_size)):
        # Process batch
        processed_batch = process_batch(batch_df, taxon_columns, concentrations, alpha)
        
        # Count zeros before and after
        before_zeros = (batch_df[taxon_columns] == 0).sum()
        after_zeros = (processed_batch[taxon_columns] == 0).sum()
        
        for col in taxon_columns:
            zero_counts[col] += before_zeros[col]
        
        total_rows += len(processed_batch)
        
        # Write to parquet
        if writer is None:
            # Initialize writer with schema
            table = pa.Table.from_pandas(processed_batch)
            writer = pq.ParquetWriter(output_path, table.schema)
        
        table = pa.Table.from_pandas(processed_batch)
        writer.write_table(table)
        
        if batch_idx % 10 == 0:
            logger.info(f"Processed {batch_idx + 1} batches ({total_rows} rows)")
    
    if writer:
        writer.close()
    
    # Calculate statistics
    stats = {
        "total_rows_processed": total_rows,
        "taxon_columns_processed": len(taxon_columns),
        "zero_replacement_alpha": alpha,
        "original_zero_counts": zero_counts,
        "output_path": str(output_path),
        "parameters": concentrations
    }
    
    logger.info(f"Zero replacement complete. Processed {total_rows} rows.")
    logger.info(f"Output written to: {output_path}")
    
    # Save statistics
    stats_path = output_path.parent / "zero_replacement_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Statistics saved to: {stats_path}")
    
    return stats

def main():
    """Main entry point for zero replacement pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Apply Bayesian-multiplicative zero-replacement to microbiome data")
    parser.add_argument("--input", type=str, help="Input parquet file path")
    parser.add_argument("--output", type=str, help="Output parquet file path")
    parser.add_argument("--alpha", type=float, default=DEFAULT_ZERO_REPLACEMENT_ALPHA,
                      help="Dirichlet prior concentration parameter")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
                      help="Batch size for processing")
    
    args = parser.parse_args()
    
    try:
        stats = run_zero_replacement_pipeline(
            input_path=args.input,
            output_path=args.output,
            alpha=args.alpha,
            batch_size=args.batch_size
        )
        print(json.dumps(stats, indent=2))
    except Exception as e:
        log_exception(logger, e)
        raise

if __name__ == "__main__":
    main()
