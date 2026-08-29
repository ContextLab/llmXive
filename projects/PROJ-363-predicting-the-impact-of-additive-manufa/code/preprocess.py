import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import jsonschema
from jsonschema import validate, ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DegenerateDatasetError(Exception):
    """Raised when the dataset has zero porosity variance."""
    pass

def load_schema(schema_path: Path) -> dict:
    """Load the JSON schema from a YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    return schema

def validate_schema(df: pd.DataFrame, schema: dict) -> bool:
    """
    Validate the DataFrame against the provided JSON schema.
    
    Args:
        df: The DataFrame to validate.
        schema: The JSON schema dictionary.
        
    Returns:
        True if valid.
        
    Raises:
        ValidationError: If the data does not match the schema.
    """
    # Convert DataFrame to a list of records for jsonschema validation
    # jsonschema expects a list of objects (rows) when validating a dataset
    data_records = df.to_dict(orient='records')
    
    # Define the schema for the list of records
    # The provided schema describes a single object (row), so we wrap it
    list_schema = {
        "type": "array",
        "items": schema
    }
    
    try:
        validate(instance=data_records, schema=list_schema)
        logger.info("Schema validation passed.")
        return True
    except ValidationError as e:
        logger.error(f"Schema validation failed: {e.message}")
        logger.error(f"Path: {list(e.path)}")
        raise

def check_degenerate_dataset(df: pd.DataFrame, target_col: str = 'porosity') -> None:
    """
    Check if the dataset is degenerate (zero variance in target).
    
    Args:
        df: The DataFrame to check.
        target_col: The name of the target column.
        
    Raises:
        DegenerateDatasetError: If variance is zero.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")
    
    variance = df[target_col].var()
    if variance == 0:
        raise DegenerateDatasetError(
            f"Degenerate Dataset detected: Target column '{target_col}' has zero variance. "
            "Model training would be meaningless."
        )
    logger.info(f"Degenerate check passed. Variance of '{target_col}': {variance:.4f}")

def handle_ev_fallback(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle Volumetric Energy Density (Ev) calculation or fallback.
    
    Logic:
    1. Check if 'energy_density' or 'VolumetricEnergyDensity' exists.
    2. If not, calculate from power, speed, hatch, thickness.
    3. Filter rows with invalid parameters (<=0).
    4. Assign -1.0 for missing raw parameters if Ev is used but raw params missing.
    """
    # Normalize column names to lowercase for checking
    cols_lower = {col.lower(): col for col in df.columns}
    
    ev_col = None
    if 'energy_density' in cols_lower:
        ev_col = cols_lower['energy_density']
    elif 'volumetricenergydensity' in cols_lower:
        ev_col = cols_lower['volumetricenergydensity']
    
    if ev_col:
        logger.info(f"Using existing Energy Density column: {ev_col}")
        # Ensure it's numeric
        df[ev_col] = pd.to_numeric(df[ev_col], errors='coerce')
        return df
    
    # Need to calculate
    raw_params = ['power', 'speed', 'hatch', 'thickness']
    # Map common synonyms if necessary, assuming standard names after preprocessing
    # If synonyms exist, they should be mapped before this step.
    
    # Check for required columns
    missing_params = [p for p in raw_params if p not in df.columns]
    if missing_params:
        logger.warning(f"Missing raw parameters for Ev calculation: {missing_params}. "
                       "Cannot calculate Ev. Assigning -1.0.")
        df['energy_density'] = -1.0
        return df

    # Filter valid rows for calculation
    valid_mask = (
        (df['speed'] > 0) & 
        (df['hatch'] > 0) & 
        (df['thickness'] > 0)
    )
    
    # Ev = Power / (Speed * Hatch * Thickness)
    # Units: Power (W), Speed (mm/s), Hatch (mm), Thickness (mm) -> J/mm^3
    df['energy_density'] = np.nan
    
    if valid_mask.any():
        df.loc[valid_mask, 'energy_density'] = (
            df.loc[valid_mask, 'power'] / 
            (df.loc[valid_mask, 'speed'] * 
             df.loc[valid_mask, 'hatch'] * 
             df.loc[valid_mask, 'thickness'])
        )
    
    # Handle invalid rows (where speed, hatch, or thickness <= 0)
    invalid_mask = ~valid_mask
    if invalid_mask.any():
        logger.warning(f"Filtering out {invalid_mask.sum()} rows with invalid parameters for Ev calculation.")
        # Assign sentinel for rows where we couldn't calculate but might need to keep them if target exists
        # Per task: "Assign sentinel value -1.0 for missing raw parameters if Ev is used"
        df.loc[invalid_mask, 'energy_density'] = -1.0
        
    return df

def normalize_columns(df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """
    Normalize input features to [0, 1] range.
    
    Args:
        df: The DataFrame.
        feature_cols: List of column names to normalize.
        
    Returns:
        DataFrame with normalized columns.
    """
    df_norm = df.copy()
    for col in feature_cols:
        if col not in df_norm.columns:
            logger.warning(f"Feature column {col} not found, skipping normalization.")
            continue
        
        min_val = df_norm[col].min()
        max_val = df_norm[col].max()
        
        if max_val == min_val:
            logger.warning(f"Column {col} has zero range. Setting all to 0.0.")
            df_norm[col] = 0.0
        else:
            df_norm[col] = (df_norm[col] - min_val) / (max_val - min_val)
            
    return df_norm

def preprocess_data(raw_path: Path, output_path: Path, schema_path: Path) -> pd.DataFrame:
    """
    Main preprocessing pipeline.
    1. Load raw data.
    2. Map column synonyms (handled in loader or here if needed).
    3. Handle Ev fallback.
    4. Check degenerate dataset.
    5. Normalize features.
    6. Validate against schema.
    7. Save output.
    """
    logger.info(f"Loading raw data from {raw_path}")
    df = pd.read_csv(raw_path)
    
    # Ensure column names are lowercase for consistency
    df.columns = df.columns.str.strip().str.lower()
    
    # Handle Ev
    df = handle_ev_fallback(df)
    
    # Check for degenerate dataset
    check_degenerate_dataset(df, target_col='porosity')
    
    # Normalize features
    feature_cols = ['power', 'speed', 'hatch', 'thickness']
    df = normalize_columns(df, feature_cols)
    
    # Ensure energy_density is in the dataframe if calculated or present
    if 'energy_density' not in df.columns:
        df['energy_density'] = -1.0
        
    # Validate Schema
    logger.info(f"Validating data against schema: {schema_path}")
    schema = load_schema(schema_path)
    validate_schema(df, schema)
    
    # Save processed data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")
    
    return df

def main():
    """Entry point for preprocessing script."""
    # Define paths
    base_dir = Path(__file__).parent.parent
    raw_data_path = base_dir / "data" / "raw" / "316L_raw.csv" # Assuming standard location
    processed_data_path = base_dir / "data" / "processed" / "cleaned_316L.csv"
    schema_path = base_dir / "contracts" / "dataset.schema.yaml"
    
    # If raw data path doesn't exist, try to find it or use a default
    # In a real scenario, this might be passed as an argument
    if not raw_data_path.exists():
        # Fallback to a generic name if the specific one isn't found
        raw_candidates = list((base_dir / "data" / "raw").glob("*.csv"))
        if raw_candidates:
            raw_data_path = raw_candidates[0]
            logger.warning(f"Raw data not found at {raw_data_path}, using {raw_data_path}")
        else:
            logger.error("No raw CSV data found in data/raw/. Exiting.")
            sys.exit(1)

    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}. Exiting.")
        sys.exit(1)

    try:
        preprocess_data(raw_data_path, processed_data_path, schema_path)
    except DegenerateDatasetError as e:
        logger.critical(str(e))
        sys.exit(1)
    except ValidationError as e:
        logger.critical(f"Data validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during preprocessing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()