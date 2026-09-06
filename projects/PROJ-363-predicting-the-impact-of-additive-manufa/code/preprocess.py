import os
import sys
import logging
import pandas as pd
import numpy as np
import yaml
from pathlib import Path

from utils import setup_logging, load_state, update_state, compute_file_hash

# Configure logging
logger = setup_logging(__name__)

class DegenerateDatasetError(Exception):
    """Custom exception for degenerate datasets (zero variance)."""
    pass

def load_schema(schema_path: str) -> dict:
    """Load the JSON/YAML schema from disk."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema

def validate_schema(df: pd.DataFrame, schema: dict) -> None:
    """
    Validate the DataFrame against the provided schema.
    
    Checks:
    1. All required columns exist.
    2. All columns have valid numeric types (int/float).
    3. No null values exist in required columns.
    4. Values meet minimum constraints defined in schema.
    
    Raises:
        ValueError: If validation fails.
    """
    required_cols = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # 1. Check required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # 2. Check types and nulls
    for col in required_cols:
        if col not in df.columns:
            continue
        
        # Check for nulls
        if df[col].isnull().any():
            raise ValueError(f"Column '{col}' contains null values")
        
        # Check type (must be numeric)
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"Column '{col}' is not numeric. Found type: {df[col].dtype}")
        
        # Check constraints (e.g., minimum)
        if col in properties:
            prop_def = properties[col]
            if 'minimum' in prop_def:
                min_val = prop_def['minimum']
                if (df[col] < min_val).any():
                    raise ValueError(f"Column '{col}' contains values below minimum {min_val}")
    
    logger.info("Schema validation passed.")

def check_degenerate_dataset(df: pd.DataFrame, target_col: str = 'porosity') -> bool:
    """
    Check if the target column has zero variance (degenerate dataset).
    
    Args:
        df: The DataFrame to check.
        target_col: The name of the target column.
    
    Returns:
        True if the dataset is degenerate (variance < 1e-6), False otherwise.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset")
    
    variance = df[target_col].var()
    logger.info(f"Porosity variance: {variance}")
    
    if variance < 1e-6:
        return True
    return False

def handle_ev_fallback(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate or fallback to existing energy density column.
    
    Logic:
    1. Calculate Ev = P / (v * h * t) if raw params exist.
    2. If raw params missing but Ev column exists, use it.
    3. If neither, raise error.
    """
    raw_params = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    ev_candidates = ['energy_density', 'Ev', 'VolumetricEnergyDensity']
    
    has_raw = all(col in df.columns for col in raw_params)
    has_ev = any(col in df.columns for col in ev_candidates)
    
    if has_raw:
        # Filter out invalid rows (<= 0) to prevent division by zero
        mask = (df['scan_speed'] > 0) & (df['hatch_spacing'] > 0) & (df['layer_thickness'] > 0)
        if not mask.all():
            logger.warning(f"Filtered out {(~mask).sum()} rows with non-positive parameters.")
            df = df[mask].reset_index(drop=True)
        
        # Calculate Ev
        # Ensure units are consistent (assuming inputs are in Watts, mm/s, mm, mm)
        # Ev = P (W) / (v (mm/s) * h (mm) * t (mm)) = J/mm^3
        df['energy_density'] = df['laser_power'] / (df['scan_speed'] * df['hatch_spacing'] * df['layer_thickness'])
        logger.info("Calculated energy_density from raw parameters.")
    elif has_ev:
        # Find the existing column
        ev_col = next(col for col in ev_candidates if col in df.columns)
        if ev_col != 'energy_density':
            df['energy_density'] = df[ev_col]
            logger.info(f"Using existing {ev_col} column as energy_density.")
        else:
            logger.info("Energy density column already exists.")
    else:
        raise ValueError("Cannot determine energy_density: missing raw parameters and no existing Ev column.")
    
    return df

def normalize_column_synonyms(df: pd.DataFrame) -> pd.DataFrame:
    """Map common column name variations to standard schema."""
    synonym_map = {
        'P': 'laser_power', 'laser_power': 'laser_power', 'Power': 'laser_power',
        'v': 'scan_speed', 'scan_speed': 'scan_speed', 'Speed': 'scan_speed',
        'h': 'hatch_spacing', 'hatch_spacing': 'hatch_spacing', 'Hatch': 'hatch_spacing',
        't': 'layer_thickness', 'layer_thickness': 'layer_thickness', 'Thickness': 'layer_thickness',
        'Porosity': 'porosity', 'porosity': 'porosity',
        'EnergyDensity': 'energy_density', 'Ev': 'energy_density', 'VolumetricEnergyDensity': 'energy_density'
    }
    
    # Identify columns to rename
    rename_map = {}
    for col in df.columns:
        if col in synonym_map and synonym_map[col] != col:
            rename_map[col] = synonym_map[col]
    
    if rename_map:
        logger.info(f"Renaming columns: {rename_map}")
        df = df.rename(columns=rename_map)
    
    return df

def normalize_columns(df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """Normalize feature columns to [0, 1] range."""
    df_norm = df.copy()
    for col in feature_cols:
        if col in df_norm.columns:
            min_val = df_norm[col].min()
            max_val = df_norm[col].max()
            if max_val == min_val:
                logger.warning(f"Column {col} has zero range, skipping normalization.")
                continue
            df_norm[col] = (df_norm[col] - min_val) / (max_val - min_val)
    return df_norm

def create_feature_subsets(df: pd.DataFrame) -> tuple:
    """
    Create distinct feature subsets to enforce FR-010 (no multicollinearity).
    
    Returns:
        X_raw: DataFrame with only raw parameters.
        X_derived: DataFrame with only energy_density.
    """
    raw_features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    derived_features = ['energy_density']
    
    # Ensure columns exist
    missing_raw = [c for c in raw_features if c not in df.columns]
    missing_derived = [c for c in derived_features if c not in df.columns]
    
    if missing_raw:
        raise ValueError(f"Missing raw features for X_raw: {missing_raw}")
    if missing_derived:
        raise ValueError(f"Missing derived features for X_derived: {missing_derived}")
    
    X_raw = df[raw_features].copy()
    X_derived = df[derived_features].copy()
    
    return X_raw, X_derived

def preprocess_data(input_path: str, output_path: str, schema_path: str) -> None:
    """
    Main preprocessing pipeline:
    1. Load raw data.
    2. Normalize column names.
    3. Impute missing values (median).
    4. Handle Energy Density.
    5. Check for degenerate dataset.
    6. Normalize features.
    7. Create feature subsets (X_raw, X_derived).
    8. Validate against schema.
    9. Save outputs.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # 1. Map synonyms
    df = normalize_column_synonyms(df)
    
    # 2. Impute missing values (median)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
            logger.info(f"Imputed {col} with median {median_val}")
    
    # 3. Handle Energy Density
    df = handle_ev_fallback(df)
    
    # 4. Check for degenerate dataset
    if check_degenerate_dataset(df):
        # Write flag and update state, then exit gracefully
        flag_path = os.path.join(os.path.dirname(output_path), 'degenerate_flag.json')
        os.makedirs(os.path.dirname(flag_path), exist_ok=True)
        with open(flag_path, 'w') as f:
            json.dump({"reason": "Zero porosity variance", "status": "degenerate"}, f)
        
        # Update state
        state = load_state()
        state['degenerate'] = True
        update_state(state)
        
        logger.warning("Degenerate dataset detected. Flag written. Exiting gracefully.")
        sys.exit(0)
    
    # 5. Normalize features
    feature_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    df = normalize_columns(df, feature_cols)
    
    # 6. Create feature subsets
    X_raw, X_derived = create_feature_subsets(df)
    
    # Save subsets
    base_dir = os.path.dirname(output_path)
    X_raw_path = os.path.join(base_dir, 'X_raw.csv')
    X_derived_path = os.path.join(base_dir, 'X_derived.csv')
    
    X_raw.to_csv(X_raw_path, index=False)
    X_derived.to_csv(X_derived_path, index=False)
    logger.info(f"Saved feature subsets to {X_raw_path} and {X_derived_path}")
    
    # 7. VALIDATE AGAINST SCHEMA (T017b Core Logic)
    logger.info(f"Loading schema from {schema_path}")
    schema = load_schema(schema_path)
    logger.info("Validating processed data against schema...")
    validate_schema(df, schema)
    
    # 8. Save final dataset
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned dataset to {output_path}")
    
    # Update state with hash
    file_hash = compute_file_hash(output_path)
    state = load_state()
    state['data_hash'] = file_hash
    update_state(state)
    logger.info(f"Updated state with data hash: {file_hash}")

def main():
    """Entry point for preprocessing."""
    # Paths
    input_file = 'data/raw/316L_LPBF_dataset.csv' # Assuming standard raw location
    output_file = 'data/processed/cleaned_316L.csv'
    schema_file = 'contracts/dataset.schema.yaml'
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    os.makedirs(os.path.dirname(schema_file), exist_ok=True)
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Schema file not found: {schema_file}. Please run T004b first.")
    
    try:
        preprocess_data(input_file, output_file, schema_file)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()