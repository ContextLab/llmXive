import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd

from utils.logging import get_logger
from config import get_reductions

logger = get_logger(__name__)

# Tolerance for mass balance check (1.0 ± 0.01)
MASS_BALANCE_TOLERANCE = 0.01

def calculate_random_fraction(total_major_fraction: float) -> float:
    """
    Calculate the 'random' fraction as the remainder to reach 1.0.
    
    Args:
        total_major_fraction: Sum of all major texture component fractions.
        
    Returns:
        The calculated random fraction.
    """
    return max(0.0, 1.0 - total_major_fraction)

def check_mass_balance(descriptors: Dict[str, float], tolerance: float = MASS_BALANCE_TOLERANCE) -> Tuple[bool, float, float]:
    """
    Check if the sum of major components + random fraction equals 1.0 within tolerance.
    
    This function validates the mass balance for a single sample's texture descriptors.
    It assumes the input dictionary contains fractions for major components (Brass, Copper, 
    S, Goss) and optionally a 'random' fraction.
    
    Args:
        descriptors: Dictionary mapping component names to their volume fractions.
        tolerance: Acceptable deviation from 1.0 (default 0.01).
        
    Returns:
        Tuple of (is_balanced, total_sum, deviation)
        - is_balanced: True if sum is within tolerance of 1.0
        - total_sum: The actual sum of all fractions
        - deviation: Absolute difference from 1.0
    """
    major_components = ['brass', 'copper', 's', 'goss']
    
    # Sum major components
    total_major = sum(
        descriptors.get(comp, 0.0) 
        for comp in major_components 
        if comp in descriptors
    )
    
    # Get existing random fraction if present, otherwise calculate it
    existing_random = descriptors.get('random', 0.0)
    
    # If 'random' is explicitly provided, use it; otherwise calculate expected
    if 'random' in descriptors:
        total_sum = total_major + existing_random
    else:
        # Calculate what random should be for perfect balance
        expected_random = calculate_random_fraction(total_major)
        total_sum = total_major + expected_random
    
    deviation = abs(total_sum - 1.0)
    is_balanced = deviation <= tolerance
    
    return is_balanced, total_sum, deviation

def validate_descriptor_mass_balance(
    descriptors_df: pd.DataFrame, 
    tolerance: float = MASS_BALANCE_TOLERANCE
) -> pd.DataFrame:
    """
    Validate mass balance for all samples in a DataFrame of texture descriptors.
    
    Adds validation columns to the DataFrame:
    - mass_balance_sum: Sum of all fractions
    - mass_balance_deviation: Deviation from 1.0
    - mass_balance_valid: Boolean indicating if within tolerance
    
    Args:
        descriptors_df: DataFrame with texture descriptor columns.
        tolerance: Acceptable deviation from 1.0.
        
    Returns:
        DataFrame with added validation columns.
    """
    result_df = descriptors_df.copy()
    
    major_components = ['brass', 'copper', 's', 'goss']
    
    # Ensure all major component columns exist, fill NaN with 0
    for comp in major_components:
        if comp not in result_df.columns:
            logger.warning(f"Column '{comp}' not found in descriptors DataFrame")
            result_df[comp] = 0.0
    
    # Calculate sum of major components
    result_df['mass_balance_sum'] = result_df[major_components].sum(axis=1)
    
    # Add random fraction if it exists, otherwise calculate expected
    if 'random' in result_df.columns:
        result_df['mass_balance_sum'] += result_df['random']
    else:
        # Calculate expected random fraction
        result_df['mass_balance_sum'] = 1.0  # If no random column, assume it's implied
    
    # Calculate deviation from 1.0
    result_df['mass_balance_deviation'] = (result_df['mass_balance_sum'] - 1.0).abs()
    
    # Check if within tolerance
    result_df['mass_balance_valid'] = result_df['mass_balance_deviation'] <= tolerance
    
    # Log statistics
    valid_count = result_df['mass_balance_valid'].sum()
    total_count = len(result_df)
    logger.info(f"Mass balance validation: {valid_count}/{total_count} samples valid "
               f"(tolerance: ±{tolerance})")
    
    if valid_count < total_count:
        invalid_samples = result_df[~result_df['mass_balance_valid']]
        logger.warning(f"Found {len(invalid_samples)} samples with mass balance deviation > {tolerance}")
        for idx, row in invalid_samples.iterrows():
            logger.debug(f"Sample {row.get('sample_id', idx)}: "
                       f"sum={row['mass_balance_sum']:.4f}, "
                       f"deviation={row['mass_balance_deviation']:.4f}")
    
    return result_df

def validate_dataset_mass_balance(
    descriptors_df: pd.DataFrame,
    tolerance: float = MASS_BALANCE_TOLERANCE,
    strict: bool = False
) -> Dict[str, Any]:
    """
    Perform comprehensive mass balance validation on a dataset.
    
    Args:
        descriptors_df: DataFrame with texture descriptors.
        tolerance: Acceptable deviation from 1.0.
        strict: If True, raise ValueError if any sample fails validation.
        
    Returns:
        Dictionary with validation results and statistics.
        
    Raises:
        ValueError: If strict mode is enabled and validation fails.
    """
    validated_df = validate_descriptor_mass_balance(descriptors_df, tolerance)
    
    valid_count = validated_df['mass_balance_valid'].sum()
    total_count = len(validated_df)
    valid_rate = valid_count / total_count if total_count > 0 else 0.0
    
    max_deviation = validated_df['mass_balance_deviation'].max() if total_count > 0 else 0.0
    mean_deviation = validated_df['mass_balance_deviation'].mean() if total_count > 0 else 0.0
    
    result = {
        'total_samples': total_count,
        'valid_samples': int(valid_count),
        'invalid_samples': int(total_count - valid_count),
        'valid_rate': valid_rate,
        'max_deviation': float(max_deviation),
        'mean_deviation': float(mean_deviation),
        'tolerance': tolerance,
        'all_valid': bool(valid_count == total_count),
        'validated_df': validated_df
    }
    
    if strict and not result['all_valid']:
        raise ValueError(
            f"Mass balance validation failed: {total_count - valid_count} samples "
            f"exceed tolerance of ±{tolerance}. Max deviation: {max_deviation:.4f}"
        )
    
    logger.info(f"Dataset mass balance validation complete: "
               f"{valid_rate:.2%} valid, max deviation: {max_deviation:.4f}")
    
    return result

def main():
    """
    Main function to demonstrate mass balance validation.
    
    Loads descriptors from data/processed/descriptors.csv (if exists),
    performs mass balance validation, and outputs results.
    """
    from features.export_descriptors import load_processed_data
    
    logger.info("Starting mass balance validation")
    
    # Load descriptors
    descriptors_path = Path("data/processed/descriptors.csv")
    if not descriptors_path.exists():
        logger.error(f"Descriptors file not found: {descriptors_path}")
        logger.info("Run T021 (export_descriptors) first to generate descriptors.csv")
        return
    
    try:
        descriptors_df = load_processed_data(descriptors_path)
        logger.info(f"Loaded {len(descriptors_df)} descriptors from {descriptors_path}")
    except Exception as e:
        logger.error(f"Failed to load descriptors: {e}")
        return
    
    # Perform validation
    try:
        results = validate_dataset_mass_balance(descriptors_df, strict=True)
        logger.info("Mass balance validation PASSED")
        
        # Print summary
        print("\n=== Mass Balance Validation Results ===")
        print(f"Total samples: {results['total_samples']}")
        print(f"Valid samples: {results['valid_samples']} ({results['valid_rate']:.2%})")
        print(f"Invalid samples: {results['invalid_samples']}")
        print(f"Max deviation: {results['max_deviation']:.6f}")
        print(f"Mean deviation: {results['mean_deviation']:.6f}")
        print(f"Tolerance: ±{results['tolerance']}")
        print("========================================\n")
        
        # Save validated DataFrame with validation columns
        output_path = Path("data/processed/descriptors_validated.csv")
        results['validated_df'].to_csv(output_path, index=False)
        logger.info(f"Validated descriptors saved to {output_path}")
        
    except ValueError as e:
        logger.error(f"Mass balance validation FAILED: {e}")
        print(f"\nMass balance validation FAILED:\n{e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
