import os
import sys
import logging
import pandas as pd
import numpy as np
import yaml

from utils import setup_logging, load_state, update_state, compute_file_hash

# Configure logger
logger = setup_logging(__name__)

class DegenerateDatasetError(Exception):
    """Raised when the dataset has zero variance in the target column."""
    pass

def load_schema(schema_path: str) -> dict:
    """Load the dataset schema from a YAML file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema(df: pd.DataFrame, schema: dict) -> bool:
    """Validate DataFrame against the schema."""
    required_columns = schema.get('required_columns', [])
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column in schema: {col}")
    return True

def check_degenerate_dataset(df: pd.DataFrame, target_col: str = 'porosity', threshold: float = 1e-6):
    """Check if the target column has zero or near-zero variance."""
    variance = df[target_col].var()
    if variance < threshold:
        logger.warning(f"Degenerate dataset detected: {target_col} variance is {variance} (< {threshold})")
        return True
    return False

def handle_ev_fallback(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Volumetric Energy Density (Ev) if not present.
    Formula: Ev = P / (v * h * t)
    Filters out rows with non-positive parameters.
    """
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    
    # Check if Ev already exists
    ev_candidates = [c for c in ['energy_density', 'Ev', 'VolumetricEnergyDensity'] if c in df.columns]
    
    if ev_candidates:
        # Use existing Ev column
        df['energy_density'] = df[ev_candidates[0]]
        logger.info(f"Using existing energy density column: {ev_candidates[0]}")
        return df

    # Check if raw parameters exist
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Cannot calculate Ev. Missing raw parameters: {missing_cols}. "
                       f"Also no existing 'energy_density', 'Ev', or 'VolumetricEnergyDensity' column found.")

    # Filter out invalid rows (division by zero protection)
    valid_mask = (
        (df['scan_speed'] > 0) & 
        (df['hatch_spacing'] > 0) & 
        (df['layer_thickness'] > 0)
    )
    invalid_count = (~valid_mask).sum()
    if invalid_count > 0:
        logger.warning(f"Filtering out {invalid_count} rows with non-positive parameters for Ev calculation.")
    
    df = df[valid_mask].copy()
    
    # Calculate Ev
    # P (W), v (mm/s), h (mm), t (mm) -> Ev (J/mm^3)
    df['energy_density'] = df['laser_power'] / (df['scan_speed'] * df['hatch_spacing'] * df['layer_thickness'])
    logger.info("Calculated 'energy_density' column.")
    
    return df

def normalize_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Normalize specified columns to [0, 1] range."""
    df_norm = df.copy()
    for col in columns:
        if col in df_norm.columns:
            min_val = df_norm[col].min()
            max_val = df_norm[col].max()
            if max_val - min_val == 0:
                logger.warning(f"Column {col} has zero range, cannot normalize. Setting to 0.0.")
                df_norm[col] = 0.0
            else:
                df_norm[col] = (df_norm[col] - min_val) / (max_val - min_val)
    return df_norm

def create_feature_subsets(df: pd.DataFrame) -> tuple:
    """
    Create distinct feature subsets to enforce FR-010 (no multicollinearity).
    X_raw: Only raw parameters (laser_power, scan_speed, hatch_spacing, layer_thickness)
    X_derived: Only Volumetric Energy Density (energy_density)
    
    Returns:
        tuple: (X_raw_df, X_derived_df)
    """
    raw_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    
    # Validate raw columns exist
    missing_raw = [c for c in raw_cols if c not in df.columns]
    if missing_raw:
        raise ValueError(f"Missing raw parameter columns for X_raw: {missing_raw}")
    
    # Check for energy density column
    if 'energy_density' not in df.columns:
        raise ValueError("Missing 'energy_density' column for X_derived. Run handle_ev_fallback first.")
    
    # Create X_raw subset
    X_raw = df[raw_cols].copy()
    
    # Create X_derived subset
    X_derived = df[['energy_density']].copy()
    
    logger.info(f"Created X_raw with columns: {list(X_raw.columns)}")
    logger.info(f"Created X_derived with columns: {list(X_derived.columns)}")
    
    return X_raw, X_derived

def preprocess_data(raw_path: str, schema_path: str, output_dir: str) -> None:
    """
    Main preprocessing logic:
    1. Load raw data
    2. Map columns (assumed done or handled here if needed)
    3. Impute missing values (median)
    4. Calculate Ev
    5. Check for degenerate dataset
    6. Normalize input features
    7. Create feature subsets (X_raw, X_derived)
    8. Save outputs
    """
    logger.info(f"Loading raw data from: {raw_path}")
    df = pd.read_csv(raw_path)
    
    # 1. Column Mapping (Basic synonym handling if needed, assuming T014a done)
    # T014a logic would be here, but assuming df is already mapped per task flow.
    # If not, we implement a minimal mapping here for robustness.
    synonym_map = {
        'P': 'laser_power', 'laser_power': 'laser_power', 'Power': 'laser_power',
        'v': 'scan_speed', 'scan_speed': 'scan_speed', 'Speed': 'scan_speed',
        'h': 'hatch_spacing', 'hatch_spacing': 'hatch_spacing', 'Hatch': 'hatch_spacing',
        't': 'layer_thickness', 'layer_thickness': 'layer_thickness', 'Thickness': 'layer_thickness'
    }
    df.rename(columns=synonym_map, inplace=True)
    
    # 2. Imputation (Median)
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
            logger.info(f"Imputed missing values in '{col}' with median: {median_val}")
    
    # 3. Handle Ev Fallback
    df = handle_ev_fallback(df)
    
    # 4. Check Degenerate Dataset
    if check_degenerate_dataset(df, 'porosity'):
        # Write flag and update state, then exit gracefully
        flag_path = os.path.join(output_dir, 'degenerate_flag.json')
        flag_data = {"reason": "Zero porosity variance", "status": "degenerate"}
        with open(flag_path, 'w') as f:
            json.dump(flag_data, f)
        
        # Update state.yaml
        state = load_state('state.yaml')
        state['degenerate'] = True
        update_state(state, 'state.yaml')
        
        logger.warning("Degenerate dataset detected. Flag written. Exiting gracefully.")
        sys.exit(0)

    # 5. Normalize Input Features (Raw Parameters)
    # T016a requirement: Normalize power, speed, hatch, thickness to [0, 1]
    raw_cols_to_norm = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    df = normalize_columns(df, raw_cols_to_norm)
    logger.info("Normalized raw parameter columns to [0, 1].")
    
    # 6. Create Feature Subsets (T016b)
    X_raw, X_derived = create_feature_subsets(df)
    
    # 7. Save Outputs
    os.makedirs(output_dir, exist_ok=True)
    
    x_raw_path = os.path.join(output_dir, 'X_raw.csv')
    x_derived_path = os.path.join(output_dir, 'X_derived.csv')
    
    X_raw.to_csv(x_raw_path, index=False)
    X_derived.to_csv(x_derived_path, index=False)
    
    logger.info(f"Saved X_raw to: {x_raw_path}")
    logger.info(f"Saved X_derived to: {x_derived_path}")
    
    # Update state with hashes
    state = load_state('state.yaml')
    state['artifacts']['X_raw_hash'] = compute_file_hash(x_raw_path)
    state['artifacts']['X_derived_hash'] = compute_file_hash(x_derived_path)
    update_state(state, 'state.yaml')

def main():
    """Entry point for preprocessing script."""
    logger.info("Starting preprocessing pipeline (T016b: Feature Subsets)")
    
    # Paths
    raw_data_path = 'data/raw/316L_LPBF_dataset.csv' # Assumed path from T012
    schema_path = 'contracts/dataset.schema.yaml'
    output_dir = 'data/processed'
    
    # Check if raw data exists
    if not os.path.exists(raw_data_path):
        # Fallback to common location if T012 used a different name
        alt_path = os.path.join('data/raw', os.listdir('data/raw')[0]) if os.path.exists('data/raw') and os.listdir('data/raw') else None
        if alt_path:
            raw_data_path = alt_path
            logger.warning(f"Raw data not found at default path. Using: {raw_data_path}")
        else:
            raise FileNotFoundError(f"Raw data file not found at {raw_data_path} or data/raw/")
    
    try:
        preprocess_data(raw_data_path, schema_path, output_dir)
        logger.info("Preprocessing completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()