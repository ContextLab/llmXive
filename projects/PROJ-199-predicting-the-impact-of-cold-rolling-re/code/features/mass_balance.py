import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd

from utils.logging import get_logger
from data.models import TextureDescriptor

logger = get_logger(__name__)

# Define the major components expected in FCC cold-rolling texture
# These match the components calculated in T018 (descriptors.py)
MAJOR_COMPONENTS = [
    "brass",
    "copper",
    "s_component",
    "goss"
]

# Tolerance for mass balance check (1.0 ± 0.01)
MASS_BALANCE_TOLERANCE = 0.01


def calculate_random_fraction(component_volumes: Dict[str, float]) -> float:
    """
    Calculate the 'random' fraction as the remainder of the volume fractions.
    
    Args:
        component_volumes: Dictionary mapping component names to their volume fractions.
        
    Returns:
        The calculated random fraction (1.0 - sum of known components).
    """
    known_sum = sum(
        component_volumes.get(comp, 0.0) 
        for comp in MAJOR_COMPONENTS
    )
    return max(0.0, 1.0 - known_sum)


def check_mass_balance(
    component_volumes: Dict[str, float], 
    tolerance: float = MASS_BALANCE_TOLERANCE
) -> Tuple[bool, float, str]:
    """
    Verify that the sum of major components + 'random' equals 1.0 within tolerance.
    
    Args:
        component_volumes: Dictionary of volume fractions for texture components.
        tolerance: Maximum allowed deviation from 1.0 (default 0.01).
        
    Returns:
        Tuple of (is_valid, deviation, message)
        - is_valid: True if mass balance holds within tolerance
        - deviation: Absolute difference from 1.0
        - message: Human-readable status message
    """
    # Calculate random fraction
    random_frac = calculate_random_fraction(component_volumes)
    
    # Sum all components including random
    total_sum = sum(
        component_volumes.get(comp, 0.0) 
        for comp in MAJOR_COMPONENTS
    ) + random_frac
    
    deviation = abs(total_sum - 1.0)
    is_valid = deviation <= tolerance
    
    if is_valid:
        status = "PASS"
        message = f"Mass balance check PASSED: Sum = {total_sum:.4f} (deviation: {deviation:.4f})"
    else:
        status = "FAIL"
        message = f"Mass balance check FAILED: Sum = {total_sum:.4f} (deviation: {deviation:.4f}), exceeds tolerance {tolerance}"
        
    logger.info(f"{status}: {message}")
    return is_valid, deviation, message


def validate_descriptor_mass_balance(
    descriptor: TextureDescriptor
) -> Tuple[bool, float, str]:
    """
    Validate mass balance for a single TextureDescriptor object.
    
    Args:
        descriptor: A TextureDescriptor instance containing volume fractions.
        
    Returns:
        Tuple of (is_valid, deviation, message)
    """
    # Extract volume fractions from the descriptor
    # Assuming the descriptor has attributes or a dict for component volumes
    # Based on T018 implementation, we expect a structure like:
    # descriptor.volume_fractions = {"brass": ..., "copper": ..., ...}
    
    if not hasattr(descriptor, 'volume_fractions'):
        msg = "Descriptor missing 'volume_fractions' attribute"
        logger.error(msg)
        return False, 1.0, msg
        
    volumes = descriptor.volume_fractions
    
    # Ensure all major components are present (default to 0 if missing)
    component_volumes = {
        comp: volumes.get(comp, 0.0) 
        for comp in MAJOR_COMPONENTS
    }
    
    return check_mass_balance(component_volumes)


def validate_dataset_mass_balance(
    df: pd.DataFrame,
    volume_col_prefix: str = "vol_"
) -> pd.DataFrame:
    """
    Validate mass balance for a DataFrame of texture descriptors.
    
    Args:
        df: DataFrame containing volume fraction columns.
        volume_col_prefix: Prefix for volume fraction columns (e.g., "vol_").
        
    Returns:
        DataFrame with added 'mass_balance_valid' and 'mass_balance_deviation' columns.
    """
    results = []
    
    for idx, row in df.iterrows():
        component_volumes = {
            comp: row.get(f"{volume_col_prefix}{comp}", 0.0)
            for comp in MAJOR_COMPONENTS
        }
        
        is_valid, deviation, _ = check_mass_balance(component_volumes)
        results.append({
            "index": idx,
            "mass_balance_valid": is_valid,
            "mass_balance_deviation": deviation
        })
        
    result_df = pd.DataFrame(results)
    df = df.copy()
    df["mass_balance_valid"] = result_df["mass_balance_valid"]
    df["mass_balance_deviation"] = result_df["mass_balance_deviation"]
    
    return df


def main():
    """
    Main entry point for mass balance validation.
    
    This function:
    1. Loads the processed descriptors from data/processed/descriptors.csv
    2. Validates mass balance for each sample
    3. Reports summary statistics
    4. Saves validation results to data/processed/descriptors_validated.csv
    """
    logger.info("Starting mass balance validation for texture descriptors...")
    
    # Define paths
    input_path = Path("data/processed/descriptors.csv")
    output_path = Path("data/processed/descriptors_validated.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T021 has generated descriptors.csv first.")
        sys.exit(1)
    
    # Load descriptors
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} descriptors from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load descriptors: {e}")
        sys.exit(1)
    
    # Validate mass balance
    validated_df = validate_dataset_mass_balance(df)
    
    # Summary statistics
    valid_count = validated_df["mass_balance_valid"].sum()
    total_count = len(validated_df)
    pass_rate = valid_count / total_count if total_count > 0 else 0.0
    max_deviation = validated_df["mass_balance_deviation"].max()
    
    logger.info(f"Mass Balance Summary:")
    logger.info(f"  Total samples: {total_count}")
    logger.info(f"  Passed: {valid_count} ({pass_rate:.2%})")
    logger.info(f"  Failed: {total_count - valid_count}")
    logger.info(f"  Max deviation: {max_deviation:.4f}")
    
    # Save validated results
    validated_df.to_csv(output_path, index=False)
    logger.info(f"Validation results saved to {output_path}")
    
    # Exit with error if any samples failed mass balance check
    if pass_rate < 1.0:
        logger.warning(f"{total_count - valid_count} samples failed mass balance check!")
        sys.exit(1)
    else:
        logger.info("All samples passed mass balance check.")
        sys.exit(0)


if __name__ == "__main__":
    main()
