import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np
import pandas as pd
from compositional import compositions

# Import from project modules
from config import get_config
from logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

def load_raw_data(raw_data_path: Path) -> pd.DataFrame:
    """Load raw data from JSON file."""
    logger.info(f"Loading raw data from {raw_data_path}")
    try:
        with open(raw_data_path, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        logger.info(f"Loaded {len(df)} records")
        return df
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        raise

def verify_measurement_independence(df: pd.DataFrame) -> pd.DataFrame:
    """Verify and filter for computational independence of Poisson's ratio measurements."""
    logger.info("Verifying measurement independence")
    
    # Filter out entries where measurement_method is calculated, derived, or missing
    valid_methods = ['experimental', 'measured', 'test']
    independent_df = df[df['measurement_method'].isin(valid_methods)].copy()
    
    dropped_count = len(df) - len(independent_df)
    logger.info(f"Dropped {dropped_count} entries due to non-independent measurement methods")
    
    # Add source verification field
    independent_df['measurement_source'] = 'verified_independent'
    
    return independent_df

def filter_monolithic_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for monolithic alloys with complete property records."""
    logger.info("Filtering for monolithic alloys")
    
    required_cols = ['poissons_ratio', 'youngs_modulus', 'Cu', 'Mg', 'Si', 'Zn', 'Mn']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter out rows with missing values in required columns
    filtered_df = df.dropna(subset=required_cols).copy()
    
    logger.info(f"Filtered to {len(filtered_df)} monolithic alloys with complete records")
    return filtered_df

def check_major_element_sum(df: pd.DataFrame, threshold: float = 0.95) -> pd.DataFrame:
    """Check and exclude entries where major element sum is below threshold."""
    logger.info("Checking major element sum")
    
    major_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    df['major_element_sum'] = df[major_elements].sum(axis=1)
    
    valid_df = df[df['major_element_sum'] >= threshold].copy()
    dropped_count = len(df) - len(valid_df)
    
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} entries with major element sum < {threshold}")
    
    return valid_df

def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize units: convert elastic constants to GPa, calculate atomic fractions."""
    logger.info("Normalizing units")
    
    # Convert Young's modulus to GPa if in MPa
    if 'youngs_modulus_unit' in df.columns:
        mask = df['youngs_modulus_unit'] == 'MPa'
        df.loc[mask, 'youngs_modulus'] = df.loc[mask, 'youngs_modulus'] / 1000.0
        df.loc[mask, 'youngs_modulus_unit'] = 'GPa'
    
    # Calculate atomic fractions summing to unity
    composition_cols = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    df['composition_sum'] = df[composition_cols].sum(axis=1)
    
    for col in composition_cols:
        df[f'{col}_atomic_fraction'] = df[col] / df['composition_sum']
    
    logger.info("Units normalized successfully")
    return df

def apply_ilr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """Apply ILR transformation to Cu, Mg, Si, Zn, Mn atomic fractions using compositional package."""
    logger.info("Applying ILR transformation to compositional data")
    
    # Get atomic fraction columns
    atomic_fraction_cols = ['Cu_atomic_fraction', 'Mg_atomic_fraction', 'Si_atomic_fraction', 
                           'Zn_atomic_fraction', 'Mn_atomic_fraction']
    
    # Check if all required columns exist
    missing_cols = [col for col in atomic_fraction_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing atomic fraction columns for ILR: {missing_cols}")
    
    # Extract composition matrix
    composition_matrix = df[atomic_fraction_cols].values
    
    # Ensure no zeros (add small epsilon if needed)
    epsilon = 1e-10
    composition_matrix = np.where(composition_matrix == 0, epsilon, composition_matrix)
    
    # Create compositions object
    comp = compositions(composition_matrix)
    
    # Apply ILR transformation
    try:
        ilr_transformed = comp.ilr()
        ilr_values = ilr_transformed.data
        
        # Create column names for ILR coordinates
        ilr_col_names = [f'ILR_{i}' for i in range(ilr_values.shape[1])]
        
        # Add ILR coordinates to dataframe
        for i, col_name in enumerate(ilr_col_names):
            df[col_name] = ilr_values[:, i]
        
        logger.info(f"ILR transformation completed. Added {len(ilr_col_names)} ILR coordinates")
        
    except Exception as e:
        logger.error(f"ILR transformation failed: {e}")
        raise
    
    return df

def clean_data(input_path: Path, output_path: Path) -> pd.DataFrame:
    """Main data cleaning pipeline."""
    logger.info(f"Starting data cleaning pipeline from {input_path} to {output_path}")
    
    # Load raw data
    df = load_raw_data(input_path)
    
    # Verify measurement independence
    df = verify_measurement_independence(df)
    
    # Filter for monolithic alloys
    df = filter_monolithic_alloys(df)
    
    # Check major element sum
    df = check_major_element_sum(df)
    
    # Normalize units
    df = normalize_units(df)
    
    # Apply ILR transformation
    df = apply_ilr_transformation(df)
    
    # Save cleaned data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Cleaned data saved to {output_path}")
    logger.info(f"Final dataset contains {len(df)} records")
    
    return df

def run_cleaning_pipeline(config: Optional[Dict[str, Any]] = None):
    """Run the full cleaning pipeline with configuration."""
    logger.info("Running data cleaning pipeline")
    
    cfg = get_config()
    if config:
        cfg.update(config)
    
    raw_data_path = cfg.get('raw_data_path', 'data/raw/filtered_alloys.json')
    processed_data_path = cfg.get('processed_data_path', 'data/processed/filtered_alloys.csv')
    
    # Load the filtered alloys from the extraction/cleaning step
    # This assumes T016 has already run and produced the intermediate file
    # If the input is already filtered, we just need to apply ILR
    
    try:
        # Check if input file exists
        input_path = Path(raw_data_path)
        if not input_path.exists():
            # Try alternative path from T016 output
            input_path = Path('data/processed/filtered_alloys_raw.csv')
            if not input_path.exists():
                raise FileNotFoundError(f"Input data file not found: {raw_data_path} or {input_path}")
        
        df = clean_data(input_path, Path(processed_data_path))
        return df
        
    except Exception as e:
        logger.error(f"Cleaning pipeline failed: {e}")
        raise

def main():
    """Entry point for data cleaning script."""
    logger.info("Data cleaning script started")
    
    try:
        df = run_cleaning_pipeline()
        logger.info("Data cleaning completed successfully")
    except Exception as e:
        logger.error(f"Data cleaning failed: {e}")
        raise

if __name__ == "__main__":
    main()