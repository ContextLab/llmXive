"""
Task T016: Validate unified dataset coverage and handle fallback logic.

Logic:
1. Load the unified timeseries from data/processed/unified_timeseries.csv.
2. Verify date range coverage for 2011-01-01 to 2024-12-31.
3. If coverage < 100%, identify the most populated rigidity bin for each species.
   Log the fallback action and proceed.
4. If coverage < 50% for ALL bins, log a critical error and exit with code 1.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
import pandas as pd

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logging import setup_logger, log_data_gap
from code.utils.config import CONFIG

# Constants
START_DATE = date(2011, 1, 1)
END_DATE = date(2024, 12, 31)
MIN_COVERAGE_CRITICAL = 0.50  # 50%
MIN_COVERAGE_WARNING = 1.00   # 100%

logger = setup_logger("validate_coverage")

def load_unified_data() -> pd.DataFrame:
    """Load the unified timeseries CSV."""
    input_path = Path(CONFIG["data"]["processed_dir"]) / "unified_timeseries.csv"
    if not input_path.exists():
        logger.error(f"Unified timeseries not found at {input_path}. Run main.py first.")
        raise FileNotFoundError(f"Missing input file: {input_path}")
    
    df = pd.read_csv(input_path)
    # Ensure date column is datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df

def calculate_coverage(df: pd.DataFrame, species_col: str, rigidity_col: str) -> Dict[str, float]:
    """
    Calculate coverage percentage for each rigidity bin of a specific species.
    Returns a dict: {rigidity_bin_value: coverage_fraction}
    """
    if species_col not in df.columns or rigidity_col not in df.columns:
        logger.warning(f"Columns {species_col} or {rigidity_col} missing. Skipping coverage calc.")
        return {}

    total_expected_days = (END_DATE - START_DATE).days + 1
    
    # Filter for date range
    mask = (df["date"] >= START_DATE) & (df["date"] <= END_DATE)
    valid_df = df[mask]
    
    if valid_df.empty:
        logger.warning("No data found in the 2011-2024 range.")
        return {}

    coverage_map = {}
    
    # Group by rigidity bin
    unique_rigs = valid_df[rigidity_col].dropna().unique()
    
    for rig in unique_rigs:
        # Count non-null entries for the species in this bin
        # Assuming the species column contains flux values; if NaN, it's missing
        bin_data = valid_df[valid_df[rigidity_col] == rig]
        valid_count = bin_data[species_col].notna().sum()
        
        coverage = valid_count / total_expected_days
        coverage_map[rig] = coverage
        
    return coverage_map

def get_most_populated_bin(coverage_map: Dict[str, float]) -> Optional[float]:
    """Return the rigidity bin with the highest coverage."""
    if not coverage_map:
        return None
    return max(coverage_map, key=coverage_map.get)

def validate_coverage():
    """Main validation logic for T016."""
    logger.info("Starting coverage validation for unified dataset.")
    
    try:
        df = load_unified_data()
    except FileNotFoundError:
        return 1

    # Define species and their corresponding columns based on T014/T015 output
    # Assuming columns: 'proton_flux', 'helium_flux', 'heavy_flux' (or similar)
    # We check the actual columns available
    species_cols = {
        "proton": "proton_flux",
        "helium": "helium_flux",
        "heavy": "heavy_flux"
    }
    
    # Fallback to generic names if specific ones don't exist
    available_cols = df.columns.tolist()
    mapped_species = {}
    for name, col in species_cols.items():
        if col in available_cols:
            mapped_species[name] = col
        else:
            # Try to find a column containing the name
            matches = [c for c in available_cols if name.lower() in c.lower()]
            if matches:
                mapped_species[name] = matches[0]
    
    rigidity_col = "rigidity" # Standard column name from T007/T011
    if rigidity_col not in available_cols:
        # Try to find a rigidity column
        rig_matches = [c for c in available_cols if "rigidity" in c.lower()]
        if rig_matches:
            rigidity_col = rig_matches[0]
        else:
            logger.error("No rigidity column found. Cannot validate coverage per bin.")
            return 1

    overall_coverage = 0.0
    fallback_bins = {}
    
    for species, col in mapped_species.items():
        logger.info(f"Validating coverage for species: {species} (col: {col})")
        coverage_map = calculate_coverage(df, col, rigidity_col)
        
        if not coverage_map:
            logger.warning(f"No valid coverage data for {species}.")
            continue

        best_bin = get_most_populated_bin(coverage_map)
        best_coverage = coverage_map[best_bin] if best_bin else 0.0

        if best_coverage < MIN_COVERAGE_CRITICAL:
            logger.critical(
                f"CRITICAL: Coverage for {species} is {best_coverage:.2%} "
                f"even in the best bin ({best_bin}). Threshold is {MIN_COVERAGE_CRITICAL:.0%}. Exiting."
            )
            return 1
        
        if best_coverage < MIN_COVERAGE_WARNING:
            logger.warning(
                f"WARNING: Coverage for {species} is {best_coverage:.2%}. "
                f"Identified fallback bin: {best_bin} (coverage: {best_coverage:.2%}). "
                f"Proceeding with analysis using this bin."
            )
            # Log the fallback action per Assumptions
            log_data_gap(
                "Coverage Fallback", 
                f"Species {species} coverage {best_coverage:.2%}. Using bin {best_bin}."
            )
        
        fallback_bins[species] = {
            "bin": best_bin,
            "coverage": best_coverage
        }
        
        # Track overall worst-case for reporting
        if best_coverage < overall_coverage or overall_coverage == 0.0:
            overall_coverage = best_coverage

    logger.info("Coverage validation completed successfully.")
    logger.info(f"Fallback bins identified: {fallback_bins}")
    
    # Optional: Save validation summary
    summary_path = Path(CONFIG["data"]["processed_dir"]) / "coverage_validation_summary.json"
    import json
    with open(summary_path, "w") as f:
        json.dump({
            "total_expected_days": (END_DATE - START_DATE).days + 1,
            "fallback_bins": {k: v for k, v in fallback_bins.items()},
            "status": "passed"
        }, f, indent=2)
    
    return 0

def main():
    exit_code = validate_coverage()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()