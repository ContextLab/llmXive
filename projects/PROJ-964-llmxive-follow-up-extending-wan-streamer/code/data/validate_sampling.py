"""
validate_sampling.py

Validates that the stratified sampling process in preprocess.py preserves the 
distribution of turn-taking events (interruption, pause, normal) as required by FR-015.

This script:
1. Loads the original (pre-sampling) dataset distribution
2. Loads the sampled (post-sampling) dataset distribution
3. Computes and compares the distributions
4. Logs detailed comparison results
5. Validates that the sampling preserved the distribution within acceptable tolerance

FR-015: Stratified sampling must preserve the distribution of turn-taking events.
US-1: Data extraction and preprocessing user story.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd
import numpy as np
from scipy import stats

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_config_summary
from utils.validators import validate_dataframe, ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for validation
DISTRIBUTION_TOLERANCE = 0.05  # 5% tolerance for distribution preservation
MIN_SAMPLE_SIZE = 10000  # Minimum sample size required for validation


def load_config() -> Dict[str, Any]:
    """Load configuration from config.py."""
    config = get_config_summary()
    return config


def load_sampled_data(data_path: Path) -> pd.DataFrame:
    """
    Load the sampled dataset from the specified path.
    
    Args:
        data_path: Path to the sampled Parquet file
        
    Returns:
        DataFrame containing the sampled data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is empty or invalid
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Sampled data file not found: {data_path}")
    
    logger.info(f"Loading sampled data from: {data_path}")
    df = pd.read_parquet(data_path)
    
    if df.empty:
        raise ValueError(f"Sampled data file is empty: {data_path}")
    
    logger.info(f"Loaded {len(df)} rows from sampled data")
    return df


def load_original_distribution(extraction_output_path: Path) -> Dict[str, float]:
    """
    Load and compute the original distribution of turn-taking events from the 
    extraction output (before sampling).
    
    Args:
        extraction_output_path: Path to the raw extraction output Parquet file
        
    Returns:
        Dictionary mapping turn_label to its proportion in the original data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is empty or missing required columns
    """
    if not extraction_output_path.exists():
        raise FileNotFoundError(f"Original extraction output not found: {extraction_output_path}")
    
    logger.info(f"Loading original distribution from: {extraction_output_path}")
    df = pd.read_parquet(extraction_output_path)
    
    if df.empty:
        raise ValueError(f"Original extraction output is empty: {extraction_output_path}")
    
    if 'turn_label' not in df.columns:
        raise ValueError(f"Original extraction output missing 'turn_label' column")
    
    # Compute distribution
    total = len(df)
    distribution = df['turn_label'].value_counts(normalize=True).to_dict()
    
    logger.info(f"Original distribution (n={total}):")
    for label, proportion in distribution.items():
        logger.info(f"  {label}: {proportion:.4f} ({proportion*100:.2f}%)")
    
    return distribution


def compute_distribution(df: pd.DataFrame, column: str = 'turn_label') -> Dict[str, float]:
    """
    Compute the distribution of values in the specified column.
    
    Args:
        df: DataFrame to analyze
        column: Column name to compute distribution for
        
    Returns:
        Dictionary mapping values to their proportions
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")
    
    distribution = df[column].value_counts(normalize=True).to_dict()
    return distribution


def compare_distributions(
    original: Dict[str, float],
    sampled: Dict[str, float],
    tolerance: float = DISTRIBUTION_TOLERANCE
) -> Tuple[bool, Dict[str, float], Dict[str, float]]:
    """
    Compare two distributions and check if they are within acceptable tolerance.
    
    Args:
        original: Original distribution (before sampling)
        sampled: Sampled distribution (after sampling)
        tolerance: Maximum allowed difference for each category
        
    Returns:
        Tuple of (is_valid, original_sorted, sampled_sorted)
        - is_valid: True if all categories are within tolerance
        - original_sorted: Original distribution sorted by label
        - sampled_sorted: Sampled distribution sorted by label
    """
    # Get all unique labels from both distributions
    all_labels = sorted(set(original.keys()) | set(sampled.keys()))
    
    # Sort distributions by label
    original_sorted = {label: original.get(label, 0.0) for label in all_labels}
    sampled_sorted = {label: sampled.get(label, 0.0) for label in all_labels}
    
    # Compute differences
    differences = {}
    max_diff = 0.0
    invalid_labels = []
    
    logger.info("\nDistribution Comparison:")
    logger.info(f"{'Label':<20} {'Original':>12} {'Sampled':>12} {'Diff':>12} {'Status':>10}")
    logger.info("-" * 70)
    
    for label in all_labels:
        orig_val = original_sorted[label]
        samp_val = sampled_sorted[label]
        diff = abs(orig_val - samp_val)
        differences[label] = diff
        max_diff = max(max_diff, diff)
        
        status = "PASS" if diff <= tolerance else "FAIL"
        if diff > tolerance:
            invalid_labels.append(label)
        
        logger.info(f"{label:<20} {orig_val:>12.4f} {samp_val:>12.4f} {diff:>12.4f} {status:>10}")
    
    # Statistical test (Chi-square goodness of fit)
    # We need counts, not proportions, for chi-square
    # Since we don't have the original counts here, we'll use proportions
    # and a simplified approach
    
    is_valid = len(invalid_labels) == 0 and max_diff <= tolerance
    
    logger.info(f"\nMaximum difference: {max_diff:.4f}")
    logger.info(f"Tolerance: {tolerance:.4f}")
    logger.info(f"Validation result: {'PASS' if is_valid else 'FAIL'}")
    
    if invalid_labels:
        logger.warning(f"Labels exceeding tolerance: {invalid_labels}")
    
    return is_valid, original_sorted, sampled_sorted


def validate_sampling_distribution(
    original_distribution: Dict[str, float],
    sampled_distribution: Dict[str, float],
    tolerance: float = DISTRIBUTION_TOLERANCE,
    min_sample_size: int = MIN_SAMPLE_SIZE
) -> bool:
    """
    Validate that the sampling process preserved the distribution.
    
    Args:
        original_distribution: Distribution before sampling
        sampled_distribution: Distribution after sampling
        tolerance: Maximum allowed difference
        min_sample_size: Minimum required sample size
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValidationError: If validation fails
    """
    # Check sample size
    total_sampled = sum(sampled_distribution.values())
    if total_sampled < min_sample_size:
        raise ValidationError(
            f"Sample size ({total_sampled}) is below minimum required ({min_sample_size})"
        )
    
    # Compare distributions
    is_valid, _, _ = compare_distributions(
        original_distribution, 
        sampled_distribution, 
        tolerance
    )
    
    if not is_valid:
        raise ValidationError(
            "Sampling distribution validation failed: distribution differences exceed tolerance"
        )
    
    return True


def main():
    """
    Main function to validate sampling distribution.
    
    This function:
    1. Loads configuration
    2. Loads original and sampled datasets
    3. Computes distributions
    4. Compares and validates distributions
    5. Logs results
    6. Returns exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description='Validate that stratified sampling preserves turn-taking event distribution'
    )
    parser.add_argument(
        '--extraction-output',
        type=str,
        default=None,
        help='Path to original extraction output (before sampling). '
             'If not provided, uses config default.'
    )
    parser.add_argument(
        '--sampled-data',
        type=str,
        default=None,
        help='Path to sampled data (after sampling). '
             'If not provided, uses config default.'
    )
    parser.add_argument(
        '--tolerance',
        type=float,
        default=DISTRIBUTION_TOLERANCE,
        help=f'Distribution tolerance (default: {DISTRIBUTION_TOLERANCE})'
    )
    parser.add_argument(
        '--min-sample-size',
        type=int,
        default=MIN_SAMPLE_SIZE,
        help=f'Minimum sample size (default: {MIN_SAMPLE_SIZE})'
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        
        # Determine file paths
        extraction_output_path = Path(args.extraction_output) if args.extraction_output else Path(config.get('extraction_output_path', 'data/processed/raw_latents.parquet'))
        sampled_data_path = Path(args.sampled_data) if args.sampled_data else Path(config.get('sampled_data_path', 'data/processed/sampled_latents.parquet'))
        
        # Make paths absolute if relative
        if not extraction_output_path.is_absolute():
            extraction_output_path = PROJECT_ROOT / extraction_output_path
        if not sampled_data_path.is_absolute():
            sampled_data_path = PROJECT_ROOT / sampled_data_path
        
        logger.info(f"Original extraction output: {extraction_output_path}")
        logger.info(f"Sampled data: {sampled_data_path}")
        
        # Load original distribution
        original_distribution = load_original_distribution(extraction_output_path)
        
        # Load sampled data and compute its distribution
        sampled_df = load_sampled_data(sampled_data_path)
        sampled_distribution = compute_distribution(sampled_df)
        
        logger.info(f"\nSampled distribution (n={len(sampled_df)}):")
        for label, proportion in sampled_distribution.items():
            logger.info(f"  {label}: {proportion:.4f} ({proportion*100:.2f}%)")
        
        # Validate distribution preservation
        logger.info("\n" + "="*70)
        logger.info("VALIDATING DISTRIBUTION PRESERVATION")
        logger.info("="*70)
        
        is_valid = validate_sampling_distribution(
            original_distribution,
            sampled_distribution,
            tolerance=args.tolerance,
            min_sample_size=args.min_sample_size
        )
        
        if is_valid:
            logger.info("\n✓ VALIDATION PASSED: Sampling distribution preserved within tolerance")
            logger.info(f"  - All turn-taking event categories within {args.tolerance*100:.1f}% tolerance")
            logger.info(f"  - Sample size: {len(sampled_df)} (≥ {args.min_sample_size} required)")
            return 0
        else:
            logger.error("\n✗ VALIDATION FAILED: Distribution not preserved")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        return 1
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
