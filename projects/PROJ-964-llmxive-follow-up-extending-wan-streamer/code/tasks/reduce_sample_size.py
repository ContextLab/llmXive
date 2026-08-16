"""
Module to reduce dataset sample size on power limit exceedance.

This module provides functionality to reduce the sample size of a dataset
when power limits are exceeded, with a hard fail if the minimum sample size
is reached.

FR-014: Power Limitation Handling
FR-023: Graceful failure with specific error message
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np

# Define minimum sample size constant explicitly (FR-014)
# This is the absolute minimum number of samples required for statistical validity
MIN_SAMPLE_SIZE = 10000

# Power limit threshold in MB (7 GB = 7000 MB)
MEMORY_LIMIT_MB = 7000

class PowerLimitationError(Exception):
    """Exception raised when power limitation prevents further reduction."""
    pass


def get_current_memory_usage_mb() -> float:
    """
    Get current memory usage in megabytes.

    Returns:
        float: Current memory usage in MB
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback if psutil is not available
        logging.warning("psutil not available, using placeholder memory estimate")
        return 0.0


def reduce_sample_size(
    df: pd.DataFrame,
    target_size: Optional[int] = None,
    memory_limit_mb: float = MEMORY_LIMIT_MB,
    min_sample_size: int = MIN_SAMPLE_SIZE,
    stratify_column: Optional[str] = None,
    seed: int = 42
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Reduce dataset sample size by a deferred amount on power limit exceedance.

    This function reduces the sample size of a DataFrame when power limits are
    exceeded, with stratified sampling to preserve distribution if a stratify
    column is provided. If the target size is below the minimum sample size,
    a PowerLimitationError is raised.

    Args:
        df: Input DataFrame to reduce
        target_size: Target number of samples. If None, reduces to fit memory limit.
        memory_limit_mb: Maximum memory usage in MB (default: 7000 MB = 7 GB)
        min_sample_size: Minimum allowed sample size (default: MIN_SAMPLE_SIZE constant)
        stratify_column: Column name to use for stratified sampling
        seed: Random seed for reproducibility

    Returns:
        Tuple of (reduced DataFrame, metadata dict with reduction info)

    Raises:
        PowerLimitationError: If reduction would go below minimum sample size
        ValueError: If input DataFrame is empty or invalid
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty")

    original_size = len(df)
    logging.info(f"Original dataset size: {original_size:,} samples")

    # If target_size is provided and it's below minimum, fail immediately
    if target_size is not None and target_size < min_sample_size:
        raise PowerLimitationError(
            f"Power Limitation: Cannot reduce to {target_size:,} samples "
            f"(minimum is {min_sample_size:,})"
        )

    # If already at or below target, no reduction needed
    if target_size is not None and original_size <= target_size:
        logging.info(f"Dataset already at or below target size ({original_size:,} <= {target_size:,})")
        return df, {
            'original_size': original_size,
            'reduced_size': original_size,
            'reduction_ratio': 1.0,
            'reason': 'no_reduction_needed'
        }

    # Calculate target size if not provided (based on memory limit)
    if target_size is None:
        # Estimate samples per MB from current data
        current_memory_mb = get_current_memory_usage_mb()
        if current_memory_mb > 0:
            samples_per_mb = original_size / current_memory_mb
            # Target is 80% of memory limit to leave headroom
            estimated_target = int((memory_limit_mb * 0.8) * samples_per_mb)
            target_size = max(min_sample_size, estimated_target)
            logging.info(f"Estimated target size based on memory: {target_size:,} samples")

    # Ensure we don't go below minimum
    if target_size < min_sample_size:
        raise PowerLimitationError(
            f"Power Limitation: Cannot reduce to {target_size:,} samples "
            f"(minimum is {min_sample_size:,})"
        )

    # Perform stratified or random sampling
    np.random.seed(seed)

    if stratify_column and stratify_column in df.columns:
        # Stratified sampling to preserve distribution
        logging.info(f"Performing stratified sampling on column: {stratify_column}")
        stratified_dfs = []
        for group_name, group_df in df.groupby(stratify_column):
            group_size = len(group_df)
            # Calculate proportionate sample size for this group
            group_target = max(1, int(group_size * (target_size / original_size)))
            group_target = min(group_size, group_target)  # Don't sample more than available

            if group_target >= group_size:
                stratified_dfs.append(group_df)
            else:
                sampled = group_df.sample(n=group_target, random_state=seed)
                stratified_dfs.append(sampled)

        reduced_df = pd.concat(stratified_dfs, ignore_index=True)
    else:
        # Simple random sampling
        logging.info("Performing random sampling")
        if target_size >= original_size:
            reduced_df = df.copy()
        else:
            reduced_df = df.sample(n=target_size, random_state=seed)

    reduced_size = len(reduced_df)
    reduction_ratio = reduced_size / original_size

    logging.info(f"Reduced dataset from {original_size:,} to {reduced_size:,} samples "
                f"(ratio: {reduction_ratio:.2%})")

    metadata = {
        'original_size': original_size,
        'reduced_size': reduced_size,
        'reduction_ratio': reduction_ratio,
        'target_size': target_size,
        'min_sample_size': min_sample_size,
        'stratify_column': stratify_column,
        'seed': seed,
        'reason': 'power_limit_reduction' if target_size < original_size else 'no_reduction_needed'
    }

    return reduced_df, metadata


def main():
    """
    Main entry point for command-line usage.

    Usage:
        python -m code.tasks.reduce_sample_size \
            --input data/processed/raw_extract.parquet \
            --output data/processed/reduced_dataset.parquet \
            --target-size 50000 \
            --stratify-column turn_label
    """
    parser = argparse.ArgumentParser(
        description='Reduce dataset sample size on power limit exceedance'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Input parquet file path'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Output parquet file path'
    )
    parser.add_argument(
        '--target-size', '-t',
        type=int,
        default=None,
        help='Target number of samples (optional, calculates from memory if not provided)'
    )
    parser.add_argument(
        '--stratify-column', '-s',
        type=str,
        default=None,
        help='Column to use for stratified sampling'
    )
    parser.add_argument(
        '--min-sample-size',
        type=int,
        default=MIN_SAMPLE_SIZE,
        help=f'Minimum sample size (default: {MIN_SAMPLE_SIZE})'
    )
    parser.add_argument(
        '--memory-limit',
        type=float,
        default=MEMORY_LIMIT_MB,
        help=f'Memory limit in MB (default: {MEMORY_LIMIT_MB})'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load dataset
        logging.info(f"Loading dataset from {input_path}")
        df = pd.read_parquet(input_path)
        logging.info(f"Loaded {len(df):,} samples")

        # Reduce sample size
        reduced_df, metadata = reduce_sample_size(
            df=df,
            target_size=args.target_size,
            memory_limit_mb=args.memory_limit,
            min_sample_size=args.min_sample_size,
            stratify_column=args.stratify_column,
            seed=args.seed
        )

        # Save reduced dataset
        logging.info(f"Saving reduced dataset to {output_path}")
        reduced_df.to_parquet(output_path, index=False)

        # Save metadata
        metadata_path = output_path.parent / f"{output_path.stem}_metadata.json"
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logging.info(f"Reduction complete. Metadata saved to {metadata_path}")
        logging.info(f"Final size: {metadata['reduced_size']:,} samples")

    except PowerLimitationError as e:
        logging.error(f"Power Limitation Error: {e}")
        # Write error log
        error_log_path = output_path.parent / "power_limitation_error.log"
        with open(error_log_path, 'w') as f:
            f.write(f"Power Limitation Error at {args.output}\n")
            f.write(f"Error: {e}\n")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
