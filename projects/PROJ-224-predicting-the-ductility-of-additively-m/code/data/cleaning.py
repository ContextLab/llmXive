import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required columns for the curated dataset
REQUIRED_COLUMNS = [
    'laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness',
    'ductility', 'alloy_family', 'energy_density'
]

# Elements to map as binary flags
ELEMENT_FLAGS = ['Cr', 'Al', 'Ti', 'Co', 'Mo', 'W']

def convert_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert all raw units to SI (W, mm/s, µm, %).
    
    Args:
        df: Input DataFrame with process parameters
        
    Returns:
        DataFrame with converted units
    """
    logger.info("Converting units to SI standards...")
    df = df.copy()
    
    # Laser Power: Convert to Watts (W)
    if 'laser_power' in df.columns:
        if 'laser_power_unit' in df.columns:
            mask_w = df['laser_power_unit'].str.lower() == 'w'
            mask_kw = df['laser_power_unit'].str.lower() == 'kw'
            df.loc[mask_kw, 'laser_power'] = df.loc[mask_kw, 'laser_power'] * 1000
            df.loc[mask_w, 'laser_power'] = df.loc[mask_w, 'laser_power']
        # Ensure numeric
        df['laser_power'] = pd.to_numeric(df['laser_power'], errors='coerce')
    
    # Scan Speed: Convert to mm/s
    if 'scan_speed' in df.columns:
        if 'scan_speed_unit' in df.columns:
            mask_mm_s = df['scan_speed_unit'].str.lower() == 'mm/s'
            mask_m_s = df['scan_speed_unit'].str.lower() == 'm/s'
            mask_mm_min = df['scan_speed_unit'].str.lower() == 'mm/min'
            
            df.loc[mask_m_s, 'scan_speed'] = df.loc[mask_m_s, 'scan_speed'] * 1000
            df.loc[mask_mm_min, 'scan_speed'] = df.loc[mask_mm_min, 'scan_speed'] / 60.0
            df.loc[mask_mm_s, 'scan_speed'] = df.loc[mask_mm_s, 'scan_speed']
        df['scan_speed'] = pd.to_numeric(df['scan_speed'], errors='coerce')
    
    # Hatch Spacing: Convert to µm
    if 'hatch_spacing' in df.columns:
        if 'hatch_spacing_unit' in df.columns:
            mask_um = df['hatch_spacing_unit'].str.lower() == 'µm'
            mask_mm = df['hatch_spacing_unit'].str.lower() == 'mm'
            mask_m = df['hatch_spacing_unit'].str.lower() == 'm'
            
            df.loc[mask_mm, 'hatch_spacing'] = df.loc[mask_mm, 'hatch_spacing'] * 1000
            df.loc[mask_m, 'hatch_spacing'] = df.loc[mask_m, 'hatch_spacing'] * 1e6
            df.loc[mask_um, 'hatch_spacing'] = df.loc[mask_um, 'hatch_spacing']
        df['hatch_spacing'] = pd.to_numeric(df['hatch_spacing'], errors='coerce')
    
    # Layer Thickness: Convert to µm
    if 'layer_thickness' in df.columns:
        if 'layer_thickness_unit' in df.columns:
            mask_um = df['layer_thickness_unit'].str.lower() == 'µm'
            mask_mm = df['layer_thickness_unit'].str.lower() == 'mm'
            mask_m = df['layer_thickness_unit'].str.lower() == 'm'
            
            df.loc[mask_mm, 'layer_thickness'] = df.loc[mask_mm, 'layer_thickness'] * 1000
            df.loc[mask_m, 'layer_thickness'] = df.loc[mask_m, 'layer_thickness'] * 1e6
            df.loc[mask_um, 'layer_thickness'] = df.loc[mask_um, 'layer_thickness']
        df['layer_thickness'] = pd.to_numeric(df['layer_thickness'], errors='coerce')
    
    # Ductility: Ensure % (if not already)
    if 'ductility' in df.columns:
        if 'ductility_unit' in df.columns:
            mask_pct = df['ductility_unit'].str.lower() == '%'
            mask_decimal = df['ductility_unit'].str.lower() == 'decimal'
            df.loc[mask_decimal, 'ductility'] = df.loc[mask_decimal, 'ductility'] * 100
            df.loc[mask_pct, 'ductility'] = df.loc[mask_pct, 'ductility']
        df['ductility'] = pd.to_numeric(df['ductility'], errors='coerce')
    
    logger.info("Unit conversion complete.")
    return df

def filter_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out records with missing ductility or incomplete process specs.
    Log reasons for exclusion.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Filtered DataFrame
    """
    logger.info("Filtering records with missing values...")
    original_count = len(df)
    df = df.copy()
    
    # Identify missing values in required columns
    missing_mask = pd.DataFrame(False, index=df.index, columns=REQUIRED_COLUMNS)
    
    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            missing_mask[col] = df[col].isna()
        else:
            missing_mask[col] = True  # Column missing entirely
    
    # Combine all missing flags
    any_missing = missing_mask.any(axis=1)
    
    # Log reasons for exclusion
    if any_missing.any():
        excluded_indices = df[any_missing].index.tolist()
        logger.warning(f"Excluding {len(excluded_indices)} records due to missing values.")
        
        # Log specific reasons
        for col in REQUIRED_COLUMNS:
            if col in df.columns:
                count_missing = df[col].isna().sum()
                if count_missing > 0:
                    logger.warning(f"  - Missing '{col}': {count_missing} records")
            else:
                logger.warning(f"  - Column '{col}' is missing entirely")
        
        # Drop rows with any missing required values
        df = df.dropna(subset=REQUIRED_COLUMNS)
    
    final_count = len(df)
    logger.info(f"Filter complete. {original_count - final_count} records excluded. {final_count} records remaining.")
    
    return df

def map_alloy_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map alloy composition to binary flags for specific elements.
    
    Args:
        df: Input DataFrame with composition data
        
    Returns:
        DataFrame with added binary flag columns
    """
    logger.info("Mapping alloy composition to binary flags...")
    df = df.copy()
    
    # Expected composition columns (could be 'Cr', 'Al', etc. or 'Cr_wt', 'Al_wt')
    # We assume the DataFrame has columns named after the elements or with a standard suffix
    
    for element in ELEMENT_FLAGS:
        # Try standard column name first
        col_name = element
        if col_name not in df.columns:
            # Try with '_wt' suffix
            col_name = f"{element}_wt"
        
        if col_name in df.columns:
            # Create binary flag: 1 if present (>0), 0 otherwise
            df[element] = (df[col_name] > 0).astype(int)
            logger.info(f"  - Created flag for {element} from {col_name}")
        else:
            logger.warning(f"  - Column for {element} not found, skipping flag creation")
    
    logger.info("Alloy flag mapping complete.")
    return df

def add_validation_checks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add validation checks for the curated dataset.
    
    - If row count < 50, log critical warning but proceed.
    - Log total excluded records and reasons.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Validated DataFrame
    """
    logger.info("Running validation checks...")
    row_count = len(df)
    
    # Check row count threshold
    if row_count < 50:
        logger.critical(f"Dataset row count ({row_count}) is below the minimum threshold of 50.")
        logger.critical("Proceeding with caution - model performance may be unreliable.")
    else:
        logger.info(f"Dataset row count ({row_count}) meets the minimum threshold of 50.")
    
    # Log summary of excluded records (if any were tracked in previous steps)
    # Note: In a real pipeline, we might track excluded indices across steps
    # For now, we log the current state
    logger.info(f"Validation complete. Final dataset contains {row_count} records.")
    
    # Verify all required columns are present
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

def main():
    """
    Main entry point for data cleaning pipeline.
    """
    logger.info("Starting data cleaning pipeline...")
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / "data" / "raw_builds.csv"  # Assumed input from acquisition
    output_path = project_root / "data" / "curated_builds.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run data acquisition first.")
        return
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records.")
    
    # Step 1: Convert units
    df = convert_units(df)
    
    # Step 2: Filter missing values
    df = filter_missing_values(df)
    
    # Step 3: Map alloy flags
    df = map_alloy_flags(df)
    
    # Step 4: Add validation checks (T019 requirement)
    df = add_validation_checks(df)
    
    # Save output
    logger.info(f"Saving curated dataset to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Data cleaning pipeline complete.")

if __name__ == "__main__":
    main()