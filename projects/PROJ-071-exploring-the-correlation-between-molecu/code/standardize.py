import os
import sys
import math
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union
import pandas as pd
import numpy as np

# Import logging utilities from existing project module
from logging_config import get_logger, AnalysisError

# Constants
R_GAS_CONSTANT = 8.314  # J/(mol·K)
STD_TEMP_K = 298.15     # 25°C in Kelvin
STD_PH = 7.4

logger = get_logger(__name__)

def convert_k_to_half_life(k: float, unit: str = 'h') -> float:
    """
    Convert rate constant (k) to half-life (t1/2).
    Formula: t1/2 = ln(2) / k
    
    Args:
        k: Rate constant value
        unit: Time unit of k ('h' for hours, 'd' for days, 's' for seconds)
    
    Returns:
        Half-life in hours
    """
    if k <= 0:
        raise ValueError(f"Rate constant must be positive, got {k}")
    
    ln2 = math.log(2)
    t_half_raw = ln2 / k
    
    # Convert to hours if necessary
    if unit == 'd':
        return t_half_raw * 24
    elif unit == 's':
        return t_half_raw / 3600
    elif unit == 'h':
        return t_half_raw
    else:
        raise ValueError(f"Unsupported time unit: {unit}. Use 'h', 'd', or 's'.")

def normalize_arrhenius(t_half_meas: float, temp_meas: float, 
                       ea: float, temp_std: float = STD_TEMP_K) -> float:
    """
    Normalize half-life to standard temperature using Arrhenius equation.
    t1/2_std = t1/2_meas * exp(Ea/R * (1/T_meas - 1/T_std))
    
    Args:
        t_half_meas: Measured half-life (hours)
        temp_meas: Measurement temperature (Kelvin)
        ea: Activation energy (J/mol)
        temp_std: Standard temperature (Kelvin, default 298.15K / 25°C)
    
    Returns:
        Normalized half-life (hours)
    """
    if temp_meas <= 0 or temp_std <= 0:
        raise ValueError("Temperatures must be positive (Kelvin)")
    if ea < 0:
        raise ValueError("Activation energy must be non-negative")
    
    exponent = (ea / R_GAS_CONSTANT) * (1.0 / temp_meas - 1.0 / temp_std)
    return t_half_meas * math.exp(exponent)

def check_data_coverage(df: pd.DataFrame, threshold: float = 0.5) -> Tuple[bool, float]:
    """
    Check if sufficient data exists for pH and temperature covariates.
    
    Args:
        df: Input DataFrame
        threshold: Minimum fraction of records required (default 0.5)
    
    Returns:
        Tuple of (include_covariates: bool, coverage_percent: float)
    """
    required_cols = ['temperature_k', 'ph']
    if not all(col in df.columns for col in required_cols):
        logger.warning(f"Missing covariate columns. Expected: {required_cols}")
        return False, 0.0
    
    total_rows = len(df)
    if total_rows == 0:
        return False, 0.0
    
    # Count rows with non-null values for both covariates
    valid_rows = df[required_cols].dropna().shape[0]
    coverage = valid_rows / total_rows
    
    include = coverage >= threshold
    logger.info(f"Data coverage check: {coverage:.2%} of records have pH and Temp data. "
                f"Threshold: {threshold:.0%}. Decision: {'Include' if include else 'Exclude'} covariates.")
    
    return include, coverage

def standardize_dataset(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main orchestration function for standardization and stratification.
    
    1. Loads merged dataset.
    2. Converts rate constants to half-lives (hours).
    3. Applies Arrhenius normalization if Ea is available.
    4. Checks data coverage for covariates.
    5. Stratifies data into 'standard_subset' and 'descriptive_table'.
    
    Args:
        input_path: Path to merged CSV (data/processed/merged_drugs.csv)
        output_path: Path to save standardization results (JSON)
    
    Returns:
        Dictionary containing file paths and metadata
    """
    logger.info(f"Starting standardization pipeline for {input_path}")
    
    # Load data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    
    # Step 1: Convert k to t1/2 (hours)
    # Assuming input has 'rate_constant' and 'rate_unit' columns
    # If 'half_life' already exists, we might skip, but spec says convert k
    if 'rate_constant' in df.columns and 'rate_unit' in df.columns:
        try:
            df['half_life_hours'] = df.apply(
                lambda row: convert_k_to_half_life(row['rate_constant'], row['rate_unit']), 
                axis=1
            )
            logger.info("Converted rate constants to half-life (hours).")
        except Exception as e:
            logger.error(f"Error converting rate constants: {e}")
            raise AnalysisError(f"Rate constant conversion failed: {e}")
    elif 'half_life' in df.columns:
        # Assume it's already in hours or handle unit column if present
        if 'half_life_unit' in df.columns:
            df['half_life_hours'] = df.apply(
                lambda row: convert_k_to_half_life(row['half_life'], row['half_life_unit']),
                axis=1
            )
        else:
            df['half_life_hours'] = df['half_life']
        logger.info("Using existing half-life column.")
    else:
        raise AnalysisError("Neither 'rate_constant' nor 'half_life' found in dataset.")
    
    # Step 2: Arrhenius Normalization
    # Check if Ea (activation energy) is available
    if 'activation_energy' in df.columns and 'temperature_k' in df.columns:
        def apply_normalization(row):
            ea = row.get('activation_energy')
            temp = row.get('temperature_k')
            t_half = row['half_life_hours']
            
            if pd.isna(ea) or pd.isna(temp) or ea == 0:
                return t_half, 'unnormalized'
            
            try:
                norm_val = normalize_arrhenius(t_half, temp, ea)
                return norm_val, 'normalized'
            except ValueError as e:
                logger.warning(f"Normalization failed for row: {e}")
                return t_half, 'unnormalized'
        
        df[['normalized_half_life', 'norm_status']] = df.apply(
            apply_normalization, axis=1, result_type='expand'
        )
        logger.info("Applied Arrhenius normalization.")
    else:
        logger.warning("Activation energy or Temperature missing. Skipping normalization.")
        df['normalized_half_life'] = df['half_life_hours']
        df['norm_status'] = 'unnormalized'
    
    # Step 3: Data Coverage Check (T021a)
    # This determines if we *could* use covariates in regression, but T021 focuses on stratification
    include_covariates, coverage = check_data_coverage(df)
    
    # Step 4: Stratification Logic (T021)
    # Filter for "Standard" conditions (25°C, pH 7.4) OR records normalized to standard
    # Exclude 'Unnormalized' records (missing Ea) from standard_subset
    
    # Define standard condition thresholds
    TEMP_STD = 298.15  # 25C
    TEMP_TOL = 1.0     # +/- 1C tolerance
    PH_STD = 7.4
    PH_TOL = 0.2       # +/- 0.2 pH tolerance
    
    mask_standard = (
        (df['temperature_k'].between(TEMP_STD - TEMP_TOL, TEMP_STD + TEMP_TOL)) &
        (df['ph'].between(PH_STD - PH_TOL, PH_STD + PH_TOL))
    )
    
    mask_normalized = (df['norm_status'] == 'normalized')
    
    # Standard subset: Either standard conditions OR successfully normalized
    # Exclude records where norm_status is 'unnormalized' (missing Ea)
    # Note: If a record is 'standard' but 'unnormalized' (missing Ea), it should be excluded 
    # based on "Exclude 'Unnormalized' records (missing Ea) from the standard_subset"
    # However, if it's already at standard conditions, normalization isn't needed?
    # Spec says: "Filter for Standard conditions ... OR records normalized ... Exclude 'Unnormalized' records"
    # Interpretation: If it's not at standard conditions, it MUST be normalized. If it's not normalized, it's out.
    # If it IS at standard conditions, is it allowed even if unnormalized? 
    # "Exclude 'Unnormalized' records (missing Ea) from the standard_subset" implies ALL unnormalized are out.
    # Let's follow the strict instruction: Exclude unnormalized from standard_subset.
    
    mask_valid_for_standard = mask_standard | mask_normalized
    mask_unnormalized = df['norm_status'] == 'unnormalized'
    
    # Final mask for standard_subset: Valid logic AND not unnormalized
    # Actually, if it's unnormalized, mask_normalized is False. 
    # If it's standard but unnormalized, mask_standard is True, mask_unnormalized is True.
    # Logic: (Standard OR Normalized) AND (NOT Unnormalized)
    # If unnormalized, (Standard OR False) AND False -> False.
    # So any unnormalized record is excluded.
    
    mask_final = mask_valid_for_standard & (~mask_unnormalized)
    
    standard_subset = df[mask_final].copy()
    descriptive_table = df[~mask_final].copy()
    
    logger.info(f"Stratification complete.")
    logger.info(f"  Standard Subset (for regression): {len(standard_subset)} records")
    logger.info(f"  Descriptive Table (excluded): {len(descriptive_table)} records")
    
    # Save outputs
    # We save the split data as CSVs for downstream tasks (T022, T023)
    # And a summary JSON
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_std_path = str(output_dir / "standard_subset.csv")
    csv_desc_path = str(output_dir / "descriptive_table.csv")
    
    standard_subset.to_csv(csv_std_path, index=False)
    descriptive_table.to_csv(csv_desc_path, index=False)
    
    results = {
        "input_file": input_path,
        "standard_subset_path": csv_std_path,
        "descriptive_table_path": csv_desc_path,
        "standard_subset_count": len(standard_subset),
        "descriptive_table_count": len(descriptive_table),
        "covariate_inclusion_decision": include_covariates,
        "covariate_coverage": coverage,
        "total_records": len(df),
        "status": "complete"
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Standardization results saved to {output_path}")
    return results

def main():
    """Entry point for the standardization script."""
    # Default paths relative to project root
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "data" / "processed" / "merged_drugs.csv"
    output_file = base_dir / "data" / "processed" / "standardization_results.json"
    
    # Allow override via command line
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
        
    try:
        standardize_dataset(str(input_file), str(output_file))
        print(f"Success. Results written to {output_file}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()