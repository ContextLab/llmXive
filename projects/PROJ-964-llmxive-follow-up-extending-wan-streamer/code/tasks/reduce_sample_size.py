"""
Module to reduce dataset sample size by a fixed amount on power limit exceedance.
Implements FR-014 and FR-023: Power Limitation handling.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np

# Constants
MIN_SAMPLE_SIZE = 1000  # Minimum sample size allowed before failing
MEMORY_THRESHOLD_MB = 7000  # 7 GB limit in MB
REDUCTION_FACTOR = 0.5  # Reduce sample size by 50% on power limit exceedance

class PowerLimitationError(Exception):
    """Raised when sample size reduction hits the minimum threshold."""
    pass

def get_current_memory_usage_mb() -> float:
    """
    Get current memory usage in MB.
    Uses psutil if available, otherwise falls back to resource (Unix) or returns 0.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except ImportError:
            logging.warning("psutil and resource not available for memory tracking.")
            return 0.0

def reduce_sample_size(
    data: pd.DataFrame,
    target_size: Optional[int] = None,
    min_size: int = MIN_SAMPLE_SIZE,
    reduction_factor: float = REDUCTION_FACTOR
) -> Tuple[pd.DataFrame, int]:
    """
    Reduce the sample size of the dataframe by a fixed amount or factor.

    Args:
        data: Input DataFrame to reduce.
        target_size: Optional explicit target size. If provided, reduces to this size.
        min_size: Minimum allowed sample size.
        reduction_factor: Factor to reduce by if target_size not provided (e.g., 0.5 for 50%).

    Returns:
        Tuple of (reduced DataFrame, new sample size).

    Raises:
        PowerLimitationError: If the required reduction would go below min_size.
    """
    current_size = len(data)
    logging.info(f"Current sample size: {current_size}")

    if target_size is not None:
        if target_size >= current_size:
            logging.info("Target size is not smaller than current size. No reduction needed.")
            return data, current_size

        if target_size < min_size:
            raise PowerLimitationError(
                f"Requested target size {target_size} is below minimum {min_size}. "
                f"Power Limitation: Cannot reduce further."
            )

        new_size = target_size
    else:
        new_size = int(current_size * reduction_factor)
        if new_size < min_size:
            raise PowerLimitationError(
                f"Calculated reduced size {new_size} is below minimum {min_size}. "
                f"Power Limitation: Cannot reduce further."
            )

    logging.info(f"Reducing sample size from {current_size} to {new_size}")

    # Perform stratified sampling if 'priority' column exists, else random sample
    if 'priority' in data.columns:
        # Stratified sampling by priority
        sampled_data = data.groupby('priority', group_keys=False).apply(
            lambda x: x.sample(n=min(int(len(x) * (new_size / current_size)), len(x)), random_state=42)
        )
        # Ensure we don't exceed target due to rounding
        if len(sampled_data) > new_size:
            sampled_data = sampled_data.sample(n=new_size, random_state=42)
    else:
        # Random sample
        sampled_data = data.sample(n=new_size, random_state=42)

    logging.info(f"Reduced sample size: {len(sampled_data)}")
    return sampled_data, len(sampled_data)

def main():
    """
    CLI entry point for reducing sample size.
    Usage: python code/tasks/reduce_sample_size.py --input <path> --output <path> [--target <size>]
    """
    parser = argparse.ArgumentParser(description="Reduce dataset sample size on power limit exceedance.")
    parser.add_argument("--input", type=str, required=True, help="Path to input parquet file.")
    parser.add_argument("--output", type=str, required=True, help="Path to output parquet file.")
    parser.add_argument("--target", type=int, default=None, help="Target sample size (optional).")
    parser.add_argument("--min-size", type=int, default=MIN_SAMPLE_SIZE, help="Minimum sample size.")
    parser.add_argument("--factor", type=float, default=REDUCTION_FACTOR, help="Reduction factor if no target.")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        logging.info(f"Loading data from {input_path}")
        df = pd.read_parquet(input_path)
        logging.info(f"Loaded {len(df)} rows")

        reduced_df, new_size = reduce_sample_size(
            df,
            target_size=args.target,
            min_size=args.min_size,
            reduction_factor=args.factor
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        reduced_df.to_parquet(output_path, index=False)
        logging.info(f"Saved reduced dataset ({new_size} rows) to {output_path}")

    except PowerLimitationError as e:
        logging.error(f"Power Limitation Error: {e}")
        # Create a marker file or log entry to indicate failure
        fail_log = output_path.with_suffix('.fail')
        with open(fail_log, 'w') as f:
            f.write(f"Power Limitation: {str(e)}\n")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()