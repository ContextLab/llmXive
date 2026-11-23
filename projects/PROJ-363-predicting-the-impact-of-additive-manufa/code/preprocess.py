import os
import sys
import logging
import pandas as pd
import numpy as np
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Import from utils (existing API)
try:
    from utils import setup_logging, compute_file_hash, load_state, update_state
except ImportError:
    # Fallback if utils.py is not in the same directory or import fails
    # This ensures the script can run in isolation if utils is missing
    import hashlib
    import random

    def setup_logging(level=logging.INFO):
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)

    def compute_file_hash(filepath: str) -> str:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def load_state(state_path: str = "state/state.yaml") -> dict:
        if not os.path.exists(state_path):
            return {"artifact_hashes": {}, "gate_verified": False, "degenerate": False}
        with open(state_path, 'r') as f:
            return yaml.safe_load(f)

    def update_state(state_path: str, updates: dict) -> None:
        state = load_state(state_path)
        state.update(updates)
        with open(state_path, 'w') as f:
            yaml.safe_dump(state, f)

# Constants
REQUIRED_COLUMNS = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'porosity']
SYNONYM_MAP = {
    'p': 'laser_power',
    'laser_power': 'laser_power',
    'v': 'scan_speed',
    'scan_speed': 'scan_speed',
    'h': 'hatch_spacing',
    'hatch_spacing': 'hatch_spacing',
    't': 'layer_thickness',
    'layer_thickness': 'layer_thickness',
    'thickness': 'layer_thickness',
    'power': 'laser_power',
    'speed': 'scan_speed',
    'hatch': 'hatch_spacing',
    'thickness': 'layer_thickness',
    'P': 'laser_power',
    'V': 'scan_speed',
    'H': 'hatch_spacing',
    'T': 'layer_thickness',
    'Power': 'laser_power',
    'Speed': 'scan_speed',
    'Hatch': 'hatch_spacing',
    'Thickness': 'layer_thickness',
    'Ev': 'energy_density',
    'VolumetricEnergyDensity': 'energy_density',
    'energy_density': 'energy_density'
}

class DegenerateDatasetError(Exception):
    """Exception raised when the dataset has zero porosity variance."""
    pass

def load_schema(schema_path: str = "contracts/dataset.schema.yaml") -> dict:
    """Load the dataset schema from YAML file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema(df: pd.DataFrame, schema: dict) -> None:
    """Validate dataframe against schema."""
    required_columns = schema.get('required_columns', [])
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Check for nulls in required columns
    for col in required_columns:
        if df[col].isnull().sum() > 0:
            raise ValueError(f"Column {col} contains null values")

def normalize_column_synonyms(df: pd.DataFrame) -> pd.DataFrame:
    """Map column names to standard schema using synonym map."""
    logger = logging.getLogger(__name__)
    df_renamed = df.copy()
    
    # Normalize column names to lowercase for matching
    df_renamed.columns = [col.strip().lower() for col in df_renamed.columns]
    
    # Map synonyms
    new_columns = {}
    for col in df_renamed.columns:
        if col in SYNONYM_MAP:
            new_columns[col] = SYNONYM_MAP[col]
        else:
            new_columns[col] = col
    
    df_renamed = df_renamed.rename(columns=new_columns)
    
    # Check for missing required columns
    missing = [col for col in REQUIRED_COLUMNS if col not in df_renamed.columns and col != 'porosity']
    # Note: porosity might be mapped differently, we handle it later
    
    # Special handling for porosity synonyms
    porosity_synonyms = ['porosity', 'porosity_percent', 'porosity_pct', 'void_fraction', 'void_percentage']
    porosity_col = None
    for syn in porosity_synonyms:
        if syn in df_renamed.columns:
            porosity_col = syn
            break
    
    if porosity_col and porosity_col != 'porosity':
        df_renamed = df_renamed.rename(columns={porosity_col: 'porosity'})
    
    if porosity_col is None and 'porosity' not in df_renamed.columns:
        # Try to find any column that might be porosity
        for col in df_renamed.columns:
            if 'porosity' in col.lower() or 'void' in col.lower():
                df_renamed = df_renamed.rename(columns={col: 'porosity'})
                porosity_col = 'porosity'
                break
    
    if porosity_col is None:
        raise ValueError("Could not find a porosity column in the dataset")
    
    # Re-check required columns (excluding porosity which we handled)
    missing = [col for col in REQUIRED_COLUMNS if col != 'porosity' and col not in df_renamed.columns]
    
    if missing:
        logger.warning(f"Missing required columns after mapping: {missing}")
        # Check if we have Ev only fallback available
        ev_cols = ['energy_density', 'Ev', 'VolumetricEnergyDensity']
        has_ev = any(col in df_renamed.columns for col in ev_cols)
        
        if not has_ev:
            raise ValueError(f"Required columns missing and no Ev fallback: {missing}")
        else:
            # We can proceed with Ev only
            logger.info("Proceeding with Ev-only mode")
    
    return df_renamed

def impute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Impute missing numerical values with median."""
    logger = logging.getLogger(__name__)
    df_imputed = df.copy()
    
    numerical_cols = df_imputed.select_dtypes(include=[np.number]).columns
    
    for col in numerical_cols:
        if df_imputed[col].isnull().sum() > 0:
            median_val = df_imputed[col].median()
            df_imputed[col] = df_imputed[col].fillna(median_val)
            logger.info(f"Imputed {col} with median: {median_val}")
    
    return df_imputed

def filter_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows with non-positive parameters to prevent division by zero."""
    logger = logging.getLogger(__name__)
    df_filtered = df.copy()
    
    # Filter for positive values in key parameters
    params_to_check = ['scan_speed', 'hatch_spacing', 'layer_thickness']
    initial_rows = len(df_filtered)
    
    for param in params_to_check:
        if param in df_filtered.columns:
            before = len(df_filtered)
            df_filtered = df_filtered[df_filtered[param] > 0]
            after = len(df_filtered)
            if before != after:
                logger.info(f"Filtered {before - after} rows with non-positive {param}")
    
    final_rows = len(df_filtered)
    if final_rows == 0:
        raise ValueError("No valid rows remaining after filtering")
    
    logger.info(f"Filtered from {initial_rows} to {final_rows} rows")
    return df_filtered

def calculate_energy_density(df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[str]]:
    """Calculate Volumetric Energy Density: Ev = P / (v * h * t)"""
    logger = logging.getLogger(__name__)
    df_calc = df.copy()
    ev_source = None
    
    # Check if raw parameters exist
    has_power = 'laser_power' in df_calc.columns
    has_speed = 'scan_speed' in df_calc.columns
    has_hatch = 'hatch_spacing' in df_calc.columns
    has_thickness = 'layer_thickness' in df_calc.columns
    
    has_raw = has_power and has_speed and has_hatch and has_thickness
    
    # Check if Ev already exists
    has_ev = 'energy_density' in df_calc.columns
    
    if has_raw:
        # Calculate Ev from raw parameters
        # Ev = P / (v * h * t)
        # Ensure no division by zero (already filtered)
        df_calc['energy_density'] = df_calc['laser_power'] / (
            df_calc['scan_speed'] * df_calc['hatch_spacing'] * df_calc['layer_thickness']
        )
        ev_source = "calculated"
        logger.info("Calculated energy_density from raw parameters")
    elif has_ev:
        # Use existing Ev column
        ev_source = "provided_column"
        logger.info("Using provided energy_density column")
    else:
        # Cannot calculate Ev
        raise ValueError("Cannot calculate energy_density: missing raw parameters and no Ev column")
    
    return df_calc, ev_source

def check_degenerate_dataset(df: pd.DataFrame, threshold: float = 1e-6) -> bool:
    """Check if dataset has zero porosity variance (degenerate)."""
    if 'porosity' not in df.columns:
        return False
    
    variance = df['porosity'].var()
    return variance < threshold

def write_degenerate_flag(output_dir: str, reason: str = "Zero porosity variance") -> None:
    """Write degenerate flag file."""
    os.makedirs(output_dir, exist_ok=True)
    flag_path = os.path.join(output_dir, "degenerate_flag.json")
    with open(flag_path, 'w') as f:
        json.dump({"reason": reason, "status": "degenerate"}, f, indent=2)
    logging.getLogger(__name__).info(f"Wrote degenerate flag to {flag_path}")

def update_state_degenerate(state_path: str, is_degenerate: bool) -> None:
    """Update state.yaml with degenerate status."""
    state = load_state(state_path)
    state['degenerate'] = is_degenerate
    update_state(state_path, state)

def normalize_features(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """Normalize features to [0, 1] range."""
    logger = logging.getLogger(__name__)
    df_norm = df.copy()
    
    for col in feature_cols:
        if col in df_norm.columns:
            min_val = df_norm[col].min()
            max_val = df_norm[col].max()
            if max_val - min_val > 0:
                df_norm[col] = (df_norm[col] - min_val) / (max_val - min_val)
                logger.info(f"Normalized {col} to [0, 1]")
            else:
                # All values are the same, set to 0.5
                df_norm[col] = 0.5
                logger.warning(f"Column {col} has constant value, set to 0.5")
    
    return df_norm

def create_feature_subsets(df: pd.DataFrame, ev_source: Optional[str] = None) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Create X_raw and X_derived feature subsets."""
    logger = logging.getLogger(__name__)
    
    X_raw = None
    X_derived = None
    
    raw_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    derived_cols = ['energy_density']
    
    # If Ev was provided (not calculated), skip X_raw
    if ev_source == "provided_column":
        logger.info("Ev provided externally, skipping X_raw creation")
        if all(col in df.columns for col in derived_cols):
            X_derived = df[derived_cols].copy()
        else:
            raise ValueError("Ev column missing for derived subset")
    else:
        # Create both subsets
        if all(col in df.columns for col in raw_cols):
            X_raw = df[raw_cols].copy()
            logger.info("Created X_raw subset")
        else:
            logger.warning("Raw parameters missing, cannot create X_raw")
        
        if all(col in df.columns for col in derived_cols):
            X_derived = df[derived_cols].copy()
            logger.info("Created X_derived subset")
        else:
            raise ValueError("Energy density column missing for X_derived")
    
    return X_raw, X_derived

def preprocess_data(input_file: str, output_dir: str, schema_path: str = "contracts/dataset.schema.yaml", state_path: str = "state/state.yaml") -> None:
    """Main preprocessing pipeline."""
    logger = setup_logging()
    logger.info(f"Starting preprocessing of {input_file}")
    
    # Step 1: Load raw data
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} rows from {input_file}")
    
    # Step 2: Column mapping
    df = normalize_column_synonyms(df)
    logger.info("Column mapping completed")
    
    # Step 3: Imputation
    df = impute_missing_values(df)
    logger.info("Imputation completed")
    
    # Step 4: Filtering
    df = filter_invalid_rows(df)
    logger.info("Filtering completed")
    
    # Step 5: Calculate Ev
    df, ev_source = calculate_energy_density(df)
    logger.info(f"Energy density calculation completed (source: {ev_source})")
    
    # Step 6: Degenerate detection
    if check_degenerate_dataset(df):
        logger.warning("Degenerate dataset detected (zero porosity variance)")
        write_degenerate_flag(output_dir)
        update_state_degenerate(state_path, True)
        # Create minimal outputs even for degenerate case
        os.makedirs(output_dir, exist_ok=True)
        df.to_csv(os.path.join(output_dir, "cleaned_316L.csv"), index=False)
        return
    
    update_state_degenerate(state_path, False)
    logger.info("Degenerate check passed")
    
    # Step 7: Write ev_source.json if fallback was used
    if ev_source == "provided_column":
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "ev_source.json"), 'w') as f:
            json.dump({"source": "provided_column", "column_name": "energy_density"}, f, indent=2)
        logger.info("Wrote ev_source.json")
    
    # Step 8: Normalization
    feature_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    # Only normalize if columns exist
    existing_feature_cols = [col for col in feature_cols if col in df.columns]
    if existing_feature_cols:
        df = normalize_features(df, existing_feature_cols)
        logger.info("Normalization completed")
    
    # Step 9: Validation
    if os.path.exists(schema_path):
        schema = load_schema(schema_path)
        validate_schema(df, schema)
        logger.info("Schema validation passed")
    
    # Step 10: Create feature subsets
    X_raw, X_derived = create_feature_subsets(df, ev_source)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save X_raw if it exists
    if X_raw is not None:
        X_raw_path = os.path.join(output_dir, "X_raw.csv")
        X_raw.to_csv(X_raw_path, index=False)
        logger.info(f"Saved X_raw to {X_raw_path}")
    else:
        logger.info("X_raw not created (Ev-only mode)")
    
    # Save X_derived
    if X_derived is not None:
        X_derived_path = os.path.join(output_dir, "X_derived.csv")
        X_derived.to_csv(X_derived_path, index=False)
        logger.info(f"Saved X_derived to {X_derived_path}")
    else:
        raise ValueError("X_derived not created")
    
    # Step 11: Save final dataset
    output_file = os.path.join(output_dir, "cleaned_316L.csv")
    df.to_csv(output_file, index=False)
    logger.info(f"Saved final dataset to {output_file}")
    
    # Update state with hash
    file_hash = compute_file_hash(output_file)
    update_state(state_path, {"artifact_hashes": {"cleaned_316L.csv": file_hash}})
    logger.info(f"Updated state with hash: {file_hash}")

def main():
    """Main entry point."""
    logger = setup_logging()
    
    # Paths
    input_file = "data/raw/316L_LPBF_dataset.csv"
    output_dir = "data/processed"
    schema_path = "contracts/dataset.schema.yaml"
    state_path = "state/state.yaml"
    
    try:
        preprocess_data(input_file, output_dir, schema_path, state_path)
        logger.info("Preprocessing completed successfully")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
