import os
import sys
import logging
import pandas as pd
import numpy as np
import yaml
from pathlib import Path

# Custom exceptions
class DegenerateDatasetError(Exception):
    pass

def load_schema(schema_path: str) -> dict:
    """Load the dataset schema from a YAML file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema(df: pd.DataFrame, schema: dict) -> bool:
    """Validate the DataFrame against the schema."""
    required_columns = schema.get('required_columns', [])
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    return True

def normalize_column_synonyms(df: pd.DataFrame) -> pd.DataFrame:
    """Map common column name variations to standard schema names."""
    synonym_map = {
        'P': 'laser_power', 'laser_power': 'laser_power', 'Power': 'laser_power',
        'v': 'scan_speed', 'scan_speed': 'scan_speed', 'Speed': 'scan_speed',
        'h': 'hatch_spacing', 'hatch_spacing': 'hatch_spacing', 'Hatch': 'hatch_spacing',
        't': 'layer_thickness', 'layer_thickness': 'layer_thickness', 'Thickness': 'layer_thickness',
        'Porosity': 'porosity', 'porosity': 'porosity'
    }
    
    # Normalize existing columns
    new_columns = {}
    for col in df.columns:
        if col in synonym_map:
            new_columns[col] = synonym_map[col]
        else:
            # Keep original if no mapping, but check for partial matches if needed
            # For now, strict mapping to avoid confusion
            new_columns[col] = col
    
    df = df.rename(columns=new_columns)
    
    # Check for required columns
    required = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'porosity']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns after mapping: {missing}")
    
    return df

def impute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Impute missing numerical values with the median."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
    return df

def calculate_energy_density(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Volumetric Energy Density (Ev = P / (v * h * t)).
    Handles cases where Ev is already present.
    """
    # Filter out rows with non-positive parameters to prevent division by zero
    mask = (df['scan_speed'] > 0) & (df['hatch_spacing'] > 0) & (df['layer_thickness'] > 0)
    df = df[mask].copy()
    
    if 'energy_density' in df.columns:
        # Case B: Use existing column
        logging.info("Using existing energy_density column.")
    else:
        # Case A: Calculate from raw params
        logging.info("Calculating energy_density from raw parameters.")
        df['energy_density'] = df['laser_power'] / (df['scan_speed'] * df['hatch_spacing'] * df['layer_thickness'])
    
    return df

def check_degenerate_dataset(df: pd.DataFrame, threshold: float = 1e-6) -> bool:
    """Check if the porosity variance is effectively zero."""
    if 'porosity' not in df.columns:
        return False
    variance = df['porosity'].var()
    return variance < threshold

def write_degenerate_flag(output_dir: str, reason: str = "Zero porosity variance") -> None:
    """Write the degenerate flag JSON file."""
    flag_path = Path(output_dir) / "degenerate_flag.json"
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(flag_path, 'w') as f:
        json.dump({"reason": reason, "status": "degenerate"}, f)

def update_state_degenerate(state_path: str) -> None:
    """Update state.yaml to indicate degenerate dataset."""
    if not os.path.exists(state_path):
        return
    with open(state_path, 'r') as f:
        state = yaml.safe_load(f) or {}
    state['degenerate'] = True
    with open(state_path, 'w') as f:
        yaml.dump(state, f)

def normalize_features(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize input features to [0, 1] range."""
    feature_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    for col in feature_cols:
        if col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val - min_val > 0:
                df[col] = (df[col] - min_val) / (max_val - min_val)
            else:
                df[col] = 0.0 # All same value
    return df

def create_feature_subsets(df: pd.DataFrame) -> tuple:
    """Create X_raw (raw params) and X_derived (Ev only) subsets."""
    raw_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    derived_cols = ['energy_density']
    
    # Ensure columns exist
    raw_cols = [c for c in raw_cols if c in df.columns]
    derived_cols = [c for c in derived_cols if c in df.columns]
    
    if not raw_cols:
        raise ValueError("No raw feature columns found for X_raw.")
    if not derived_cols:
        raise ValueError("No derived feature columns found for X_derived.")
    
    X_raw = df[raw_cols].copy()
    X_derived = df[derived_cols].copy()
    
    return X_raw, X_derived

def preprocess_data(input_file: str) -> pd.DataFrame:
    """Main preprocessing pipeline."""
    logger = logging.getLogger(__name__)
    logger.info(f"Starting preprocessing on {input_file}")
    
    df = pd.read_csv(input_file)
    
    # 1. Map columns
    df = normalize_column_synonyms(df)
    
    # 2. Impute
    df = impute_missing_values(df)
    
    # 3. Calculate Energy Density
    df = calculate_energy_density(df)
    
    # 4. Check Degeneracy
    if check_degenerate_dataset(df):
        logger.warning("Degenerate dataset detected (zero porosity variance).")
        base_dir = Path(input_file).parent.parent # Assume data/raw/...
        output_dir = base_dir / "processed"
        write_degenerate_flag(str(output_dir))
        state_path = base_dir.parent / "state" / "state.yaml"
        update_state_degenerate(str(state_path))
        # Exit gracefully as per T015
        sys.exit(0)
    
    # 5. Normalize
    df = normalize_features(df)
    
    # 6. Create Subsets
    X_raw, X_derived = create_feature_subsets(df)
    
    # Save subsets
    processed_dir = Path(input_file).parent.parent / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    X_raw.to_csv(str(processed_dir / "X_raw.csv"), index=False)
    X_derived.to_csv(str(processed_dir / "X_derived.csv"), index=False)
    
    logger.info(f"Saved X_raw and X_derived to {processed_dir}")
    
    # 7. Validate against schema (T017b)
    schema_path = Path(input_file).parent.parent.parent / "contracts" / "dataset.schema.yaml"
    if os.path.exists(schema_path):
        schema = load_schema(str(schema_path))
        validate_schema(df, schema)
        logger.info("Schema validation passed.")
    
    return df

def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    base_dir = Path(__file__).parent.parent
    input_file = str(base_dir / "data" / "raw" / "316L_LPBF_dataset.csv")
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    try:
        df = preprocess_data(input_file)
        logger.info("Preprocessing completed successfully.")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
