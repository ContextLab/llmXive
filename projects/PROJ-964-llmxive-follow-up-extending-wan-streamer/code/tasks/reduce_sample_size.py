"""
Module: reduce_sample_size.py
Task: T016
Purpose: Reduce dataset sample size on power limit exceedance or fail with "Power Limitation" error.

This module provides the logic to gracefully degrade dataset size when computational
resources (memory/time) are exceeded. It enforces a minimum sample size constraint
to ensure statistical validity.

Dependencies:
- pandas: For DataFrame manipulation
- utils.config: For seed pinning (set_seed)
- utils.validators: For schema validation
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import set_seed
from utils.validators import validate_dataframe, ValidationError

# Constants
DEFAULT_MIN_SAMPLE_SIZE = 10000  # Minimum frames required for statistical validity
DEFAULT_REDUCTION_FACTOR = 0.5   # Reduce by 50% on each step
REDUCTION_STEP = 0.1             # 10% reduction steps if factor is not used
MAX_REDUCTION_ATTEMPTS = 10      # Safety limit to prevent infinite loops

class PowerLimitationError(Exception):
    """
    Raised when the dataset cannot be reduced below the minimum sample size
    and the power/resource limit is still exceeded.
    """
    def __init__(self, message: str, current_size: int, min_size: int):
        super().__init__(message)
        self.current_size = current_size
        self.min_size = min_size
        self.message = message

def reduce_sample_size(
    df: pd.DataFrame,
    target_size: Optional[int] = None,
    reduction_factor: float = DEFAULT_REDUCTION_FACTOR,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    stratify_column: Optional[str] = None,
    seed: int = 42
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Reduce the sample size of a DataFrame.
    
    Args:
        df: Input DataFrame.
        target_size: If provided, reduce to exactly this size. 
                     If None, reduce by `reduction_factor`.
        reduction_factor: Fraction to keep (e.g., 0.5 keeps 50%). Used if target_size is None.
        min_sample_size: Absolute minimum number of rows allowed.
        stratify_column: If provided, perform stratified sampling to preserve distribution.
        seed: Random seed for reproducibility.
    
    Returns:
        Tuple of (reduced DataFrame, metadata dict with original_size, new_size, reduction_ratio)
    
    Raises:
        PowerLimitationError: If reducing further would violate min_sample_size.
        ValueError: If input is invalid.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    
    original_size = len(df)
    
    if original_size <= min_sample_size:
        # Already at or below minimum, cannot reduce further without violating constraints
        # Return as-is if it's already small enough, or raise if we are forced to reduce
        if target_size is not None and target_size < min_sample_size:
            raise PowerLimitationError(
                f"Target size {target_size} is below minimum allowed {min_sample_size}. "
                "Power Limitation: Cannot reduce further.",
                current_size=original_size,
                min_size=min_sample_size
            )
        return df, {
            "original_size": original_size,
            "new_size": original_size,
            "reduction_ratio": 1.0,
            "reason": "Already at or below minimum size"
        }
    
    # Determine target size
    if target_size is not None:
        new_size = target_size
    else:
        new_size = int(original_size * reduction_factor)
    
    # Enforce minimum
    if new_size < min_sample_size:
        # If the requested reduction goes below minimum, we must fail
        raise PowerLimitationError(
            f"Requested reduction to {new_size} violates minimum sample size of {min_sample_size}. "
            "Power Limitation: Cannot satisfy resource constraints without invalidating statistical power.",
            current_size=original_size,
            min_size=min_sample_size
        )
    
    # Perform sampling
    set_seed(seed)
    
    if stratify_column and stratify_column in df.columns:
        # Stratified sampling
        counts = df[stratify_column].value_counts()
        # Calculate proportional sample sizes for each group
        new_counts = (counts * (new_size / original_size)).round().astype(int)
        # Ensure at least 1 sample per group if possible, but respect global min
        # If a group would become 0, we might need to adjust, but for now let's drop groups < 1
        new_counts = new_counts.clip(lower=0)
        
        # If total is less than min_sample_size due to rounding, adjust up slightly
        if new_counts.sum() < min_sample_size:
            # Simple adjustment: add to largest groups
            diff = min_sample_size - new_counts.sum()
            for idx in new_counts.sort_values(ascending=False).index[:diff]:
                new_counts[idx] += 1
        
        sampled_dfs = []
        for label, count in new_counts.items():
            if count > 0:
                group_df = df[df[stratify_column] == label]
                if len(group_df) >= count:
                    sampled_dfs.append(group_df.sample(n=count, random_state=seed))
                else:
                    # If group is smaller than requested, take all
                    sampled_dfs.append(group_df)
        
        reduced_df = pd.concat(sampled_dfs, ignore_index=True)
    else:
        # Random sampling
        reduced_df = df.sample(n=new_size, random_state=seed)
    
    # Final check
    final_size = len(reduced_df)
    if final_size < min_sample_size:
        # Should not happen due to checks above, but safety net
        raise PowerLimitationError(
            f"Sampling resulted in {final_size} samples, below minimum {min_sample_size}.",
            current_size=original_size,
            min_size=min_sample_size
        )
    
    return reduced_df, {
        "original_size": original_size,
        "new_size": final_size,
        "reduction_ratio": final_size / original_size,
        "method": "stratified" if stratify_column else "random"
    }

def main():
    """
    CLI entry point for testing the reduction logic.
    Expects input file via --input, output via --output.
    """
    parser = argparse.ArgumentParser(description="Reduce dataset sample size")
    parser.add_argument("--input", type=str, required=True, help="Path to input Parquet/CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output file")
    parser.add_argument("--target-size", type=int, default=None, help="Target sample size")
    parser.add_argument("--reduction-factor", type=float, default=0.5, help="Fraction to keep (if target-size not set)")
    parser.add_argument("--min-size", type=int, default=DEFAULT_MIN_SAMPLE_SIZE, help="Minimum sample size")
    parser.add_argument("--stratify", type=str, default=None, help="Column to stratify by")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Load data
    if input_path.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    elif input_path.suffix in ['.csv', '.tsv']:
        df = pd.read_csv(input_path, sep='\t' if input_path.suffix == '.tsv' else ',')
    else:
        print(f"Error: Unsupported file format: {input_path.suffix}")
        sys.exit(1)
    
    print(f"Loaded {len(df)} rows from {input_path}")
    
    try:
        reduced_df, metadata = reduce_sample_size(
            df,
            target_size=args.target_size,
            reduction_factor=args.reduction_factor,
            min_sample_size=args.min_size,
            stratify_column=args.stratify,
            seed=args.seed
        )
        
        # Save output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.suffix == '.parquet':
            reduced_df.to_parquet(output_path, index=False)
        elif output_path.suffix == '.csv':
            reduced_df.to_csv(output_path, index=False)
        else:
            # Default to parquet
            reduced_df.to_parquet(output_path.with_suffix('.parquet'), index=False)
            output_path = output_path.with_suffix('.parquet')
        
        print(f"Reduced dataset to {metadata['new_size']} rows ({metadata['reduction_ratio']:.2%} of original)")
        print(f"Saved to {output_path}")
        print(f"Metadata: {metadata}")
        
    except PowerLimitationError as e:
        print(f"CRITICAL: Power Limitation Error - {e.message}")
        print(f"Current size: {e.current_size}, Minimum allowed: {e.min_size}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during reduction: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
