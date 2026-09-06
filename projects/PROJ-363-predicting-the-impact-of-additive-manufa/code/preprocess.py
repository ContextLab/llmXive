import os
import sys
import logging
import pandas as pd
import numpy as np
import yaml
import json
from pathlib import Path
from utils import setup_logging, load_state, update_state, compute_file_hash

# Configure logging
logger = setup_logging("preprocess")

class DegenerateDatasetError(Exception):
    """Raised when the dataset has zero variance in the target variable."""
    pass

def load_schema(schema_path: str) -> dict:
    """Load the dataset schema from a YAML file."""
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        return schema
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing schema YAML: {e}")
        raise

def validate_schema(df: pd.DataFrame, schema: dict) -> bool:
    """
    Validate the DataFrame against the schema.
    Checks for required columns and basic type compatibility.
    """
    required_columns = schema.get('required_columns', [])
    column_types = schema.get('column_types', {})

    # Check for required columns
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Check for expected types (basic check: is numeric where expected)
    for col, expected_type in column_types.items():
        if col in df.columns:
            if expected_type == 'float':
                if not pd.api.types.is_numeric_dtype(df[col]):
                    # Attempt conversion or raise error if it fails
                    try:
                        df[col] = pd.to_numeric(df[col], errors='raise')
                    except (ValueError, TypeError):
                        raise ValueError(f"Column '{col}' is expected to be float but contains non-numeric data.")
            # Add more type checks if needed

    logger.info("Schema validation passed.")
    return True

def check_degenerate_dataset(df: pd.DataFrame, target_col: str = 'porosity'):
    """
    Check if the target variable has zero variance.
    If so, write a flag file and update state, then exit gracefully.
    """
    if target_col not in df.columns:
        logger.warning(f"Target column '{target_col}' not found. Skipping degenerate check.")
        return

    variance = df[target_col].var()
    logger.info(f"Variance of {target_col}: {variance}")

    if variance < 1e-6:
        logger.warning("Degenerate dataset detected: Zero porosity variance.")
        flag_file = Path("data/processed/degenerate_flag.json")
        flag_file.parent.mkdir(parents=True, exist_ok=True)
        
        flag_data = {
            "reason": "Zero porosity variance",
            "status": "degenerate",
            "variance": float(variance)
        }
        
        with open(flag_file, 'w') as f:
            json.dump(flag_data, f, indent=2)
        
        logger.info(f"Degenerate flag written to {flag_file}")
        
        # Update state.yaml
        state = load_state()
        state['degenerate'] = True
        update_state(state)
        
        # Exit with code 0 as per T015 requirement
        sys.exit(0)

def handle_ev_fallback(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Volumetric Energy Density (Ev) if not present.
    Ev = P / (v * h * t)
    """
    if 'energy_density' not in df.columns:
        # Check for raw parameters
        required_params = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        if all(col in df.columns for col in required_params):
            # Filter out rows with non-positive parameters to avoid division by zero
            mask = (
                (df['scan_speed'] > 0) & 
                (df['hatch_spacing'] > 0) & 
                (df['layer_thickness'] > 0)
            )
            
            if not mask.any():
                raise ValueError("No valid rows found to calculate energy density (all parameters <= 0).")
            
            df_valid = df[mask].copy()
            df_valid['energy_density'] = df_valid['laser_power'] / (
                df_valid['scan_speed'] * df_valid['hatch_spacing'] * df_valid['layer_thickness']
            )
            
            # Update original df with calculated values for valid rows
            df.loc[mask, 'energy_density'] = df_valid['energy_density']
            logger.info("Calculated energy_density for valid rows.")
        else:
            raise ValueError("Cannot calculate energy_density: missing required raw parameters and no existing energy_density column.")
    else:
        logger.info("energy_density column already present.")
    
    return df

def normalize_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Normalize specified columns to [0, 1] range.
    """
    df_normalized = df.copy()
    for col in columns:
        if col in df_normalized.columns:
            min_val = df_normalized[col].min()
            max_val = df_normalized[col].max()
            if max_val - min_val > 0:
                df_normalized[col] = (df_normalized[col] - min_val) / (max_val - min_val)
            else:
                df_normalized[col] = 0.0  # Or handle as constant
            logger.info(f"Normalized column: {col}")
        else:
            logger.warning(f"Column {col} not found for normalization.")
    return df_normalized

def create_feature_subsets(df: pd.DataFrame) -> tuple:
    """
    Create distinct feature subsets:
    X_raw: raw parameters (laser_power, scan_speed, hatch_spacing, layer_thickness)
    X_derived: derived parameter (energy_density)
    """
    raw_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    derived_cols = ['energy_density']
    
    # Ensure target is not included in features
    target_col = 'porosity'
    
    X_raw = df[raw_cols].copy()
    X_derived = df[derived_cols].copy()
    
    # Save subsets to disk
    X_raw_path = Path("data/processed/X_raw.csv")
    X_derived_path = Path("data/processed/X_derived.csv")
    
    X_raw.to_csv(X_raw_path, index=False)
    X_derived.to_csv(X_derived_path, index=False)
    
    logger.info(f"Saved X_raw to {X_raw_path}")
    logger.info(f"Saved X_derived to {X_derived_path}")
    
    return X_raw, X_derived

def normalize_column_synonyms(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map column synonyms to standard schema names.
    """
    synonym_map = {
        'P': 'laser_power',
        'laser_power': 'laser_power',
        'v': 'scan_speed',
        'scan_speed': 'scan_speed',
        'h': 'hatch_spacing',
        'hatch_spacing': 'hatch_spacing',
        't': 'layer_thickness',
        'layer_thickness': 'layer_thickness',
        'Power': 'laser_power',
        'Speed': 'scan_speed',
        'Hatch': 'hatch_spacing',
        'Thickness': 'layer_thickness'
    }
    
    # Rename columns
    df_renamed = df.rename(columns=synonym_map)
    
    # Check for required columns after renaming
    required = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'porosity']
    missing = set(required) - set(df_renamed.columns)
    if missing:
        raise ValueError(f"Missing required columns after mapping: {missing}")
    
    return df_renamed

def preprocess_data(input_path: str, output_path: str, schema_path: str) -> pd.DataFrame:
    """
    Main preprocessing pipeline:
    1. Load raw data
    2. Map column synonyms
    3. Impute missing values (median)
    4. Calculate/verify energy density
    5. Check for degenerate dataset
    6. Normalize input features
    7. Validate against schema
    8. Create feature subsets
    9. Save final cleaned data
    """
    # 1. Load raw data
    logger.info(f"Loading raw data from {input_path}")
    df = pd.read_csv(input_path)
    
    # 2. Map column synonyms
    logger.info("Mapping column synonyms...")
    df = normalize_column_synonyms(df)
    
    # 3. Impute missing values (median)
    logger.info("Imputing missing values with median...")
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    for col in numerical_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
            logger.info(f"Imputed {col} with median {median_val}")
    
    # 4. Handle energy density
    logger.info("Handling energy density calculation...")
    df = handle_ev_fallback(df)
    
    # 5. Check for degenerate dataset
    logger.info("Checking for degenerate dataset...")
    check_degenerate_dataset(df, target_col='porosity')
    
    # 6. Normalize input features
    logger.info("Normalizing input features...")
    features_to_normalize = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    df = normalize_columns(df, features_to_normalize)
    
    # 7. Validate against schema
    logger.info(f"Validating data against schema: {schema_path}")
    schema = load_schema(schema_path)
    validate_schema(df, schema)
    
    # 8. Create feature subsets
    logger.info("Creating feature subsets...")
    create_feature_subsets(df)
    
    # 9. Save final cleaned data
    logger.info(f"Saving cleaned data to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Update state with hash
    state = load_state()
    state['data_hash'] = compute_file_hash(output_path)
    update_state(state)
    
    logger.info("Preprocessing completed successfully.")
    return df

def main():
    """
    Entry point for the preprocessing script.
    """
    input_path = "data/raw/316L_LPBF_dataset.csv" # Assuming raw file location
    output_path = "data/processed/cleaned_316L.csv"
    schema_path = "contracts/dataset.schema.yaml"
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)
    
    try:
        preprocess_data(input_path, output_path, schema_path)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()