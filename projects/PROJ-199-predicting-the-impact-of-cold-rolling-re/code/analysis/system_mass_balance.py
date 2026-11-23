"""
System-level mass balance verification for texture descriptors.

This module performs an aggregated verification of the mass balance constraint
across the entire dataset in `data/processed/descriptors.csv`. It ensures that
the sum of Brass, Copper, S, Goss, and Random components equals 1.0 ± 0.01
for the aggregated dataset, distinct from per-sample checks.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

# Adjust imports to match the project structure relative to code/
# The API surface shows `code/analysis/mass_balance_verification.py` exists.
# We will reuse the core logic from there if available, or implement inline.
# Given the API surface, `load_descriptors` and `validate_aggregated_mass_balance`
# are expected in `code/analysis/mass_balance_verification`.
# However, to ensure this task is self-contained and runnable, we will
# implement the necessary logic here or import from the existing module if it matches.
# The API surface lists `load_descriptors` in `code/analysis/mass_balance_verification`.
# Let's try to import from there first to extend existing logic.

try:
    from analysis.mass_balance_verification import load_descriptors as mb_load_descriptors
    from analysis.mass_balance_verification import calculate_total_fractions as mb_calc_total
    from analysis.mass_balance_verification import validate_aggregated_mass_balance as mb_validate_agg
    HAS_MB_VERIFICATION = True
except ImportError:
    HAS_MB_VERIFICATION = False
    # Fallback: define local helpers if the module structure is slightly different
    # or if we need to implement the specific "system" aggregation logic here.
    pass

# Configure logging
logger = logging.getLogger(__name__)

DESCRIPTORS_PATH = Path("data/processed/descriptors.csv")
OUTPUT_PATH = Path("data/processed/system_mass_balance_summary.json")
TOLERANCE = 0.01


def load_descriptors_system(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the descriptors CSV file.
    Falls back to the existing utility if available, otherwise implements locally.
    """
    file_path = path or DESCRIPTORS_PATH
    if not file_path.exists():
        raise FileNotFoundError(f"Descriptors file not found at {file_path}. "
                                "Ensure T020a has been executed successfully.")
    
    try:
        df = pd.read_csv(file_path)
        required_cols = ['Brass', 'Copper', 'S', 'Goss', 'Random']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")
        return df
    except Exception as e:
        logger.error(f"Failed to load descriptors from {file_path}: {e}")
        raise


def calculate_aggregated_sum(df: pd.DataFrame) -> float:
    """
    Calculate the mean sum of components across all samples.
    This represents the system-level mass balance.
    """
    component_cols = ['Brass', 'Copper', 'S', 'Goss', 'Random']
    # Calculate the sum for each row
    row_sums = df[component_cols].sum(axis=1)
    # Calculate the mean of these sums
    mean_sum = row_sums.mean()
    return float(mean_sum)


def validate_system_mass_balance(df: pd.DataFrame, tolerance: float = TOLERANCE) -> Dict[str, Any]:
    """
    Validate that the aggregated mass balance is within tolerance.
    Returns a dictionary with the validation result and statistics.
    """
    component_cols = ['Brass', 'Copper', 'S', 'Goss', 'Random']
    row_sums = df[component_cols].sum(axis=1)
    
    mean_sum = row_sums.mean()
    std_sum = row_sums.std()
    min_sum = row_sums.min()
    max_sum = row_sums.max()
    
    is_valid = abs(mean_sum - 1.0) <= tolerance
    
    # Count how many individual samples are out of balance (for diagnostics)
    out_of_balance_count = (abs(row_sums - 1.0) > tolerance).sum()
    total_samples = len(df)
    
    return {
        "is_valid": is_valid,
        "mean_sum": float(mean_sum),
        "std_sum": float(std_sum),
        "min_sum": float(min_sum),
        "max_sum": float(max_sum),
        "tolerance": tolerance,
        "total_samples": total_samples,
        "out_of_balance_samples": int(out_of_balance_count),
        "deviation_from_unity": float(mean_sum - 1.0)
    }


def run_system_mass_balance_verification(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    tolerance: float = TOLERANCE
) -> Dict[str, Any]:
    """
    Main entry point to run the system-level mass balance verification.
    
    1. Load descriptors from `data/processed/descriptors.csv`.
    2. Calculate the aggregated sum of components.
    3. Verify if the mean sum is within 1.0 ± tolerance.
    4. Save the summary report to `data/processed/system_mass_balance_summary.json`.
    """
    input_file = input_path or DESCRIPTORS_PATH
    output_file = output_path or OUTPUT_PATH
    
    logger.info(f"Starting system mass balance verification for {input_file}")
    
    # Load data
    df = load_descriptors_system(input_file)
    logger.info(f"Loaded {len(df)} samples.")
    
    # Validate
    result = validate_system_mass_balance(df, tolerance)
    
    # Add metadata
    result["input_file"] = str(input_file)
    result["output_file"] = str(output_file)
    result["status"] = "PASS" if result["is_valid"] else "FAIL"
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"System mass balance verification complete. Status: {result['status']}")
    logger.info(f"Report saved to {output_file}")
    
    return result


def main():
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        result = run_system_mass_balance_verification()
        if not result["is_valid"]:
            logger.warning(f"System mass balance check FAILED. Mean sum: {result['mean_sum']:.4f}")
            sys.exit(1)
        else:
            logger.info("System mass balance check PASSED.")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Verification failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()