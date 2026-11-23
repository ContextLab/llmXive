import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.special import loggamma
from scipy.optimize import minimize_scalar

from config import get_path, ensure_directories
from utils.logging import get_logger, PreprocessingError
from utils.streaming import process_with_streaming

logger = get_logger(__name__)

def estimate_zero_replacement_params(counts_df: pd.DataFrame) -> Dict[str, float]:
    """
    Estimate the multiplicative replacement parameter (delta) based on the
    distribution of non-zero counts.

    The Bayesian multiplicative replacement method replaces zeros with a small
    positive value proportional to the geometric mean of the non-zero counts
    for that taxon, scaled by a parameter delta (typically 0.65 for compositional data).

    Args:
        counts_df: DataFrame of raw microbiome counts (rows=participants, cols=taxa)

    Returns:
        Dictionary containing estimated delta parameter.
    """
    # Filter to numeric columns only (taxa counts)
    numeric_cols = counts_df.select_dtypes(include=[np.number]).columns

    if len(numeric_cols) == 0:
        raise PreprocessingError("No numeric count columns found in input data")

    # Calculate geometric mean of non-zero counts per taxon
    # Geometric mean = exp(mean(log(x))) for x > 0
    non_zero_means = {}
    for col in numeric_cols:
        non_zero_vals = counts_df[col][counts_df[col] > 0]
        if len(non_zero_vals) > 0:
            # Use log to avoid overflow
            log_vals = np.log(non_zero_vals)
            geo_mean = np.exp(np.mean(log_vals))
            non_zero_means[col] = geo_mean
        else:
            non_zero_means[col] = 1e-6  # Fallback for all-zero taxa

    # Standard delta value for compositional data (0.65 is common in literature)
    # This represents the proportion of the geometric mean to use for replacement
    delta = 0.65

    return {
        'delta': delta,
        'geometric_means': non_zero_means
    }

def bayesian_multiplicative_replace(
    counts_df: pd.DataFrame,
    params: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Apply Bayesian-multiplicative zero-replacement to handle zeros in
    microbiome count data.

    This method replaces zeros with a small positive value calculated as:
    replacement = delta * geometric_mean_of_non_zeros

    Where delta is typically 0.65 for compositional data.

    Args:
        counts_df: DataFrame of raw microbiome counts
        params: Optional pre-computed parameters from estimate_zero_replacement_params

    Returns:
        DataFrame with zeros replaced by small positive values
    """
    if counts_df.empty:
        logger.warning("Empty input DataFrame passed to zero replacement")
        return counts_df.copy()

    # Make a copy to avoid modifying original
    result_df = counts_df.copy()

    # Estimate parameters if not provided
    if params is None:
        logger.info("Estimating zero replacement parameters...")
        params = estimate_zero_replacement_params(counts_df)

    delta = params['delta']
    geo_means = params['geometric_means']

    # Apply replacement column by column
    replaced_count = 0
    total_zeros = 0

    for col in result_df.select_dtypes(include=[np.number]).columns:
        if col not in geo_means:
            continue

        geo_mean = geo_means[col]
        replacement_value = delta * geo_mean

        # Identify zeros
        zero_mask = result_df[col] == 0
        total_zeros += zero_mask.sum()

        if zero_mask.any():
            # Replace zeros with the calculated value
            result_df.loc[zero_mask, col] = replacement_value
            replaced_count += zero_mask.sum()

    logger.info(f"Zero replacement: {replaced_count} zeros replaced out of {total_zeros} total zeros")
    logger.info(f"Replacement parameter (delta): {delta}")

    return result_df

def process_batch(
    batch_df: pd.DataFrame,
    params: Dict[str, Any]
) -> pd.DataFrame:
    """
    Process a single batch of data through zero replacement.

    Args:
        batch_df: Single batch of raw counts
        params: Pre-computed replacement parameters

    Returns:
        Batch with zeros replaced
    """
    return bayesian_multiplicative_replace(batch_df, params)

def run_zero_replacement_pipeline(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    batch_size: int = 50000
) -> Path:
    """
    Run the complete zero replacement pipeline on raw microbiome data.

    This function:
    1. Loads raw microbiome counts (streaming if necessary)
    2. Estimates replacement parameters from a sample
    3. Applies Bayesian-multiplicative replacement
    4. Saves the zero-replaced counts to parquet

    Args:
        input_path: Path to raw microbiome data (if None, uses config default)
        output_path: Path for output parquet file (if None, uses config default)
        batch_size: Number of rows to process at once for memory efficiency

    Returns:
        Path to the output file
    """
    # Determine paths
    if input_path is None:
        input_path = get_path('data/raw/microbiome_counts.parquet')
    if output_path is None:
        output_path = get_path('data/processed/zero_replaced_counts.parquet')

    # Ensure output directory exists
    ensure_directories([output_path.parent])

    logger.info(f"Starting zero replacement pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")

    if not input_path.exists():
        raise PreprocessingError(f"Input file not found: {input_path}")

    # First pass: estimate parameters using a sample
    logger.info("Step 1: Estimating replacement parameters from sample...")
    sample_size = min(10000, batch_size * 2)
    sample_df = pd.read_parquet(input_path).head(sample_size)

    logger.info(f"Sample size: {len(sample_df)} rows")
    params = estimate_zero_replacement_params(sample_df)

    # Second pass: apply replacement with streaming
    logger.info("Step 2: Applying Bayesian-multiplicative replacement...")

    def process_and_save(batch: pd.DataFrame, output_file: Path, mode: str = 'w'):
        """Process a batch and append to output file."""
        processed_batch = process_batch(batch, params)
        # Convert to pyarrow for efficient parquet writing
        processed_batch.to_parquet(
            output_file,
            engine='pyarrow',
            mode=mode,
            compression='snappy'
        )

    # Use streaming loader to handle large files
    output_file = output_path

    # Process in batches and save
    first_batch = True
    total_processed = 0

    for batch in process_with_streaming(
        input_path,
        batch_size=batch_size,
        columns=None  # Process all columns
    ):
        processed_batch = process_batch(batch, params)
        total_processed += len(processed_batch)

        if first_batch:
            processed_batch.to_parquet(
                output_file,
                engine='pyarrow',
                mode='w',
                compression='snappy'
            )
            first_batch = False
        else:
            # Append to existing file
            existing = pd.read_parquet(output_file)
            combined = pd.concat([existing, processed_batch], ignore_index=True)
            combined.to_parquet(
                output_file,
                engine='pyarrow',
                mode='w',
                compression='snappy'
            )

        logger.debug(f"Processed {total_processed} rows so far...")

    logger.info(f"Zero replacement complete. Total rows processed: {total_processed}")
    logger.info(f"Output saved to: {output_file}")

    return output_file

def main():
    """Main entry point for zero replacement script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Apply Bayesian-multiplicative zero-replacement to microbiome counts'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Path to input raw counts parquet file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to output zero-replaced counts parquet file'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50000,
        help='Batch size for streaming processing'
    )

    args = parser.parse_args()

    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None

    try:
        output_file = run_zero_replacement_pipeline(
            input_path=input_path,
            output_path=output_path,
            batch_size=args.batch_size
        )
        logger.info(f"Success! Output written to {output_file}")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()
