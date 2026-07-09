import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import json
import yaml

# Local imports
from utils import setup_logging, set_seed, compute_file_hash, load_state, update_state

# Configure logging
logger = setup_logging(__name__)

class DegenerateDatasetError(Exception):
    """Raised when the dataset has zero porosity variance."""
    pass

def check_degenerate_dataset(df: pd.DataFrame, target_col: str = 'porosity', threshold: float = 1e-6) -> bool:
    """
    Check if the dataset is degenerate (zero or near-zero variance in target).
    
    Args:
        df: Input dataframe
        target_col: Name of the target column (default: 'porosity')
        threshold: Minimum variance threshold
        
    Returns:
        True if degenerate, False otherwise
        
    Raises:
        DegenerateDatasetError: If dataset is degenerate
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset")
        
    variance = df[target_col].var()
    if variance < threshold:
        raise DegenerateDatasetError(
            f"Degenerate Dataset detected: {target_col} variance ({variance:.6e}) is below threshold ({threshold}). "
            "Cannot train model on constant target."
        )
    return False

def handle_ev_fallback(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle Volumetric Energy Density (Ev) calculation with fallback logic.
    
    Priority:
    1. Check for existing 'VolumetricEnergyDensity' or 'energy_density' column
    2. If not found, calculate from raw parameters (power, speed, hatch, thickness)
    3. Filter invalid rows where parameters <= 0
    4. Assign sentinel value -1.0 for missing raw parameters if Ev is needed
    
    Args:
        df: Input dataframe
        
    Returns:
        DataFrame with 'energy_density' column added or validated
    """
    # Column name variations for Ev
    ev_columns = ['VolumetricEnergyDensity', 'Volumetric_Energy_Density', 'energy_density', 'Ev', 'VED']
    existing_ev_col = None
    
    for col in ev_columns:
        if col in df.columns:
            existing_ev_col = col
            break
    
    if existing_ev_col:
        logger.info(f"Using existing energy density column: {existing_ev_col}")
        # Rename to standard name if needed
        if existing_ev_col != 'energy_density':
            df['energy_density'] = df[existing_ev_col]
            # Drop the original if it was different
            if existing_ev_col != 'energy_density':
                df = df.drop(columns=[existing_ev_col])
        return df
    
    # Calculate Ev from raw parameters if not present
    # Required columns: laser_power (W), scan_speed (mm/s), hatch_spacing (mm), layer_thickness (mm)
    # Formula: Ev = Power / (Speed * Hatch * Thickness) [J/mm^3]
    
    raw_cols = {
        'power': ['laser_power', 'Power', 'P', 'laserPower'],
        'speed': ['scan_speed', 'ScanSpeed', 'v', 'speed'],
        'hatch': ['hatch_spacing', 'HatchSpacing', 'h', 'hatch'],
        'thickness': ['layer_thickness', 'LayerThickness', 't', 'thickness']
    }
    
    # Find actual column names
    actual_cols = {}
    for key, candidates in raw_cols.items():
        for candidate in candidates:
            if candidate in df.columns:
                actual_cols[key] = candidate
                break
    
    # Check if we have all required parameters
    if len(actual_cols) == 4:
        logger.info("Calculating energy density from raw parameters")
        
        # Filter out rows with invalid parameters (<= 0)
        valid_mask = (
            (df[actual_cols['speed']] > 0) &
            (df[actual_cols['hatch']] > 0) &
            (df[actual_cols['thickness']] > 0)
        )
        
        invalid_count = (~valid_mask).sum()
        if invalid_count > 0:
            logger.warning(f"Filtering {invalid_count} rows with invalid parameters (speed, hatch, or thickness <= 0)")
        
        df_valid = df[valid_mask].copy()
        df_invalid = df[~valid_mask].copy()
        
        # Calculate Ev for valid rows
        # Ev = P / (v * h * t)
        df_valid['energy_density'] = (
            df_valid[actual_cols['power']] / 
            (df_valid[actual_cols['speed']] * 
             df_valid[actual_cols['hatch']] * 
             df_valid[actual_cols['thickness']])
        )
        
        # For invalid rows, assign sentinel value -1.0
        df_invalid['energy_density'] = -1.0
        
        # Combine back
        df = pd.concat([df_valid, df_invalid], ignore_index=True)
        
    else:
        logger.warning("Could not calculate energy density: missing raw parameters")
        logger.warning(f"Found columns: {list(df.columns)}")
        logger.warning(f"Looking for: {raw_cols}")
        # Assign sentinel value if we can't calculate
        df['energy_density'] = -1.0
    
    return df

def normalize_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Normalize specified columns to [0, 1] range using min-max scaling.
    
    Args:
        df: Input dataframe
        columns: List of column names to normalize
        
    Returns:
        DataFrame with normalized columns
    """
    df_normalized = df.copy()
    
    for col in columns:
        if col not in df_normalized.columns:
            logger.warning(f"Column '{col}' not found, skipping normalization")
            continue
            
        min_val = df_normalized[col].min()
        max_val = df_normalized[col].max()
        
        if max_val == min_val:
            logger.warning(f"Column '{col}' has zero range, setting all values to 0.0")
            df_normalized[col] = 0.0
        else:
            df_normalized[col] = (df_normalized[col] - min_val) / (max_val - min_val)
    
    return df_normalized

def validate_schema(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Validate the dataframe against the JSON schema defined in contracts/dataset.schema.yaml.
    
    Args:
        df: Input dataframe to validate
        schema_path: Path to the schema YAML file
        
    Returns:
        True if validation passes, raises ValueError if it fails
        
    Raises:
        ValueError: If validation fails
    """
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Load schema
    with open(schema_file, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Basic validation: check required columns exist
    required_columns = schema.get('required_columns', [])
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(
            f"Schema validation failed: Missing required columns: {missing_columns}. "
            f"Available columns: {list(df.columns)}"
        )
    
    # Check column types if specified
    column_types = schema.get('column_types', {})
    for col, expected_type in column_types.items():
        if col in df.columns:
            actual_type = str(df[col].dtype)
            # Map pandas dtypes to expected types
            type_map = {
                'float64': 'float', 'float32': 'float',
                'int64': 'int', 'int32': 'int',
                'object': 'string', 'string': 'string'
            }
            actual_type_base = type_map.get(actual_type, actual_type)
            
            if expected_type not in actual_type_base:
                logger.warning(
                    f"Column '{col}' has type '{actual_type}' but schema expects '{expected_type}'"
                )
                # We don't fail on type mismatch for now, just warn
    
    logger.info("Schema validation passed")
    return True

def preprocess_data(input_path: str, output_path: str, schema_path: str) -> None:
    """
    Main preprocessing pipeline:
    1. Load raw data
    2. Map column synonyms
    3. Handle missing values (median imputation)
    4. Check for degenerate dataset
    5. Validate against schema
    6. Normalize features
    7. Calculate energy density
    8. Save cleaned data
    
    Args:
        input_path: Path to raw CSV
        output_path: Path to save cleaned CSV
        schema_path: Path to schema YAML for validation
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    schema_file = Path(schema_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Column mapping (synonyms to standard names)
    column_mapping = {
        'P': 'laser_power',
        'laserPower': 'laser_power',
        'Power': 'laser_power',
        'v': 'scan_speed',
        'ScanSpeed': 'scan_speed',
        'speed': 'scan_speed',
        'h': 'hatch_spacing',
        'HatchSpacing': 'hatch_spacing',
        'hatch': 'hatch_spacing',
        't': 'layer_thickness',
        'LayerThickness': 'layer_thickness',
        'thickness': 'layer_thickness',
        'porosity': 'porosity',
        'Porosity': 'porosity',
        'pores': 'porosity'
    }
    
    # Rename columns
    rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
    if rename_dict:
        logger.info(f"Renaming columns: {rename_dict}")
        df = df.rename(columns=rename_dict)
    
    # Check for required columns
    required = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'porosity']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns after mapping: {missing}")
    
    # Handle missing values with median imputation
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            logger.info(f"Imputing {df[col].isnull().sum()} missing values in '{col}' with median {median_val}")
            df[col] = df[col].fillna(median_val)
    
    # Check for degenerate dataset (zero porosity variance)
    logger.info("Checking for degenerate dataset...")
    check_degenerate_dataset(df, target_col='porosity')
    
    # Validate against schema
    logger.info(f"Validating against schema: {schema_path}")
    validate_schema(df, str(schema_path))
    
    # Normalize input features to [0, 1]
    features_to_normalize = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    df = normalize_columns(df, features_to_normalize)
    logger.info("Normalized input features to [0, 1]")
    
    # Calculate or handle energy density
    df = handle_ev_fallback(df)
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save cleaned data
    logger.info(f"Saving cleaned data to {output_path}")
    df.to_csv(output_file, index=False)
    
    # Update state with new hash
    file_hash = compute_file_hash(str(output_file))
    state = load_state()
    update_state(state, 'processed_data', file_hash, str(output_file))
    logger.info(f"Updated state.yaml with processed data hash: {file_hash[:16]}...")
    
    logger.info("Preprocessing complete")

def main():
    """Main entry point for preprocessing script."""
    # Configuration
    project_root = Path(__file__).parent.parent
    raw_data_path = project_root / 'data' / 'raw' / '316L_LPBF_dataset.csv'
    processed_data_path = project_root / 'data' / 'processed' / 'cleaned_316L.csv'
    schema_path = project_root / 'contracts' / 'dataset.schema.yaml'
    
    # Allow override via command line
    if len(sys.argv) > 1:
        raw_data_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        processed_data_path = Path(sys.argv[2])
    if len(sys.argv) > 3:
        schema_path = Path(sys.argv[3])
    
    logger.info("Starting preprocessing pipeline")
    logger.info(f"Input: {raw_data_path}")
    logger.info(f"Output: {processed_data_path}")
    logger.info(f"Schema: {schema_path}")
    
    try:
        preprocess_data(
            input_path=str(raw_data_path),
            output_path=str(processed_data_path),
            schema_path=str(schema_path)
        )
        logger.info("Preprocessing completed successfully")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except DegenerateDatasetError as e:
        logger.error(f"Degenerate dataset error: {e}")
        sys.exit(2)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(3)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()