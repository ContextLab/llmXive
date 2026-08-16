import os
import sys
import csv
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple

# Import from config for paths
try:
    from config import (
        get_project_root,
        get_processed_data_dir,
        get_raw_data_dir,
        get_contracts_dir,
        get_random_seed,
        ensure_directories
    )
except ImportError:
    # Fallback for execution context where config is not in path
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    from config import (
        get_project_root,
        get_processed_data_dir,
        get_raw_data_dir,
        get_contracts_dir,
        get_random_seed,
        ensure_directories
    )

# Import schema validator
try:
    from data.schema_validator import load_schema, validate_csv_schema
except ImportError:
    from data.schema_validator import load_schema, validate_csv_schema

# Constants
RANDOM_SEED = get_random_seed()
np.random.seed(RANDOM_SEED)

# --- Logger Setup ---
def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """Sets up a logger that writes to both console and file."""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    
    # Avoid duplicate handlers if logger is reused
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)
        
    return logger

# --- Core Functions ---

def load_raw_csv(file_path: str) -> pd.DataFrame:
    """Loads a CSV file into a pandas DataFrame."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw data file not found: {file_path}")
    
    logger = logging.getLogger(__name__)
    logger.info(f"Loading raw CSV from {file_path}")
    return pd.read_csv(file_path)

def detect_missing_values(df: pd.DataFrame) -> Dict[str, int]:
    """Detects missing values in the DataFrame."""
    return df.isnull().sum().to_dict()

def compute_medians(df: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
    """Computes the median for each numeric column."""
    return {col: df[col].median() for col in numeric_cols}

def impute_missing_values(df: pd.DataFrame, medians: Dict[str, float]) -> Tuple[pd.DataFrame, int]:
    """Imputes missing values using the provided medians."""
    original_missing = df.isnull().sum().sum()
    for col, median in medians.items():
        if col in df.columns:
            df[col] = df[col].fillna(median)
    imputed_count = original_missing - df.isnull().sum().sum()
    return df, int(imputed_count)

def filter_derived_columns(df: pd.DataFrame, excluded_cols: List[str]) -> pd.DataFrame:
    """Drops excluded columns (derived features) from the DataFrame."""
    cols_to_drop = [c for c in excluded_cols if c in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    return df

def encode_categorical(df: pd.DataFrame, column: str = 'alloy_type') -> pd.DataFrame:
    """One-hot encodes the specified categorical column."""
    if column not in df.columns:
        return df
    
    dummies = pd.get_dummies(df[column], prefix='is')
    df = pd.concat([df.drop(columns=[column]), dummies], axis=1)
    return df

def check_sample_count(df: pd.DataFrame, min_samples: int = 50) -> None:
    """Checks if the sample count is sufficient."""
    n = len(df)
    if n < min_samples:
        raise ValueError(f"Sample count ({n}) is below minimum required ({min_samples}).")

def check_zero_variance(df: pd.DataFrame, logger: logging.Logger) -> List[str]:
    """Detects and drops columns with zero variance."""
    zero_var_cols = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].std() == 0:
            zero_var_cols.append(col)
            logger.warning(f"Column '{col}' has zero variance; dropping to prevent singularity.")
    
    if zero_var_cols:
        df = df.drop(columns=zero_var_cols)
    return zero_var_cols

def split_and_scale(
    df: pd.DataFrame, 
    target_cols: List[str], 
    feature_cols: List[str],
    test_size: float = 0.2
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Dict[str, float]]]:
    """
    Splits data into train/test sets and scales features using MinMaxScaler.
    Fits scaler ONLY on training set.
    """
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import MinMaxScaler

    # Ensure reproducibility
    df_reset = df.reset_index(drop=True)
    
    # Stratify if 'alloy_type' (or encoded versions) exists, otherwise simple split
    stratify_col = None
    if 'alloy_type' in df_reset.columns:
        stratify_col = 'alloy_type'
    elif any(col.startswith('is_') for col in df_reset.columns):
        # Use first encoded column for stratification if available
        encoded_cols = [c for c in df_reset.columns if c.startswith('is_')]
        stratify_col = encoded_cols[0]

    if stratify_col and stratify_col in df_reset.columns:
        train_df, test_df = train_test_split(
            df_reset, 
            test_size=test_size, 
            random_state=RANDOM_SEED, 
            stratify=df_reset[stratify_col]
        )
    else:
        train_df, test_df = train_test_split(
            df_reset, 
            test_size=test_size, 
            random_state=RANDOM_SEED
        )

    # Extract features
    X_train = train_df[feature_cols].values
    X_test = test_df[feature_cols].values

    # Initialize and fit scaler on TRAINING data only
    scaler = MinMaxScaler()
    scaler.fit(X_train)

    # Transform both
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Create bounds dictionary
    bounds = {}
    for i, col in enumerate(feature_cols):
        bounds[col] = {
            "min": float(scaler.data_min_[i]),
            "max": float(scaler.data_max_[i])
        }

    # Update DataFrames with scaled values (optional, but good for debugging)
    # For this task, we primarily need to save the bounds and the split files
    train_df[feature_cols] = X_train_scaled
    test_df[feature_cols] = X_test_scaled

    return train_df, test_df, bounds

def save_normalization_bounds(bounds: Dict[str, Dict[str, float]], output_path: str) -> None:
    """Saves the normalization bounds to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(bounds, f, indent=2)

def validate_and_preprocess(
    input_path: str, 
    output_train_path: str, 
    output_test_path: str, 
    log_path: str
) -> None:
    """
    Main preprocessing pipeline:
    1. Load and validate schema.
    2. Check scope (fatigue_life).
    3. Filter derived columns.
    4. Check zero variance.
    5. Impute missing values.
    6. Encode categoricals.
    7. Split and scale.
    8. Save bounds.
    """
    logger = setup_logger("preprocess", log_path)
    logger.info("Starting preprocessing pipeline.")

    # 1. Load Data
    df = load_raw_csv(input_path)
    logger.info(f"Loaded {len(df)} rows.")

    # 2. Schema Validation
    schema_path = os.path.join(get_contracts_dir(), "dataset.schema.yaml")
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Validate schema (this raises ValueError if invalid)
    validate_csv_schema(input_path, schema_path)
    logger.info("Schema validation passed.")

    # 3. Scope Detection
    if 'fatigue_life' not in df.columns:
        logger.warning("[SCOPE] Reduced scope: fatigue_life missing; analysis restricted to yield_strength and ductility. (See Plan Assumption: Dataset-variable fit)")
    else:
        logger.info("Scope: fatigue_life present.")

    # 4. Load Excluded Columns
    excluded_path = os.path.join(get_processed_data_dir(), "excluded_columns.yaml")
    excluded_cols = []
    if os.path.exists(excluded_path):
        import yaml
        with open(excluded_path, 'r') as f:
            data = yaml.safe_load(f)
            if data and 'excluded_columns' in data:
                excluded_cols = data['excluded_columns']
        logger.info(f"Loaded {len(excluded_cols)} excluded columns.")
    else:
        logger.info("No excluded_columns.yaml found; proceeding with all columns.")

    # Filter derived columns
    df = filter_derived_columns(df, excluded_cols)

    # 5. Zero Variance Check
    check_zero_variance(df, logger)

    # 6. Sample Count Check
    check_sample_count(df)

    # 7. Imputation
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    missing_counts = detect_missing_values(df)
    total_missing = sum(missing_counts.values())
    if total_missing > 0:
        logger.info(f"Detected {total_missing} missing values.")
        medians = compute_medians(df, numeric_cols)
        df, imputed_count = impute_missing_values(df, medians)
        logger.info(f"Imputed {imputed_count} missing values using median.")
    else:
        logger.info("No missing values detected.")

    # 8. Encoding
    if 'alloy_type' in df.columns:
        df = encode_categorical(df)
        logger.info("Encoded 'alloy_type' using one-hot encoding.")

    # 9. Split and Scale
    # Define feature and target columns based on schema
    # Required: laser_power, scan_speed, layer_thickness, yield_strength, ductility
    # Optional: fatigue_life
    # Categoricals (encoded) are also features
    
    # Identify numeric features (excluding targets for scaling purposes usually, 
    # but here we scale all numeric inputs. Targets are usually kept separate for modeling 
    # but for the CSV output we keep them. The task asks to save bounds for "each numeric feature".
    # We will scale the process parameters and encoded types.
    
    # Heuristic: Columns that are NOT yield_strength, ductility, fatigue_life are features
    target_names = ['yield_strength', 'ductility', 'fatigue_life']
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in target_names]
    
    if not feature_cols:
        logger.error("No feature columns found for scaling.")
        raise ValueError("No feature columns found.")

    logger.info(f"Features to scale: {feature_cols}")

    train_df, test_df, bounds = split_and_scale(df, target_names, feature_cols)

    # 10. Save Outputs
    ensure_directories()
    processed_dir = get_processed_data_dir()
    
    # Save splits
    train_path = os.path.join(processed_dir, "train.csv")
    test_path = os.path.join(processed_dir, "test.csv")
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    logger.info(f"Saved train data to {train_path}")
    logger.info(f"Saved test data to {test_path}")

    # Save Bounds (Task T019)
    bounds_path = os.path.join(processed_dir, "normalization_bounds.json")
    save_normalization_bounds(bounds, bounds_path)
    logger.info(f"Saved normalization bounds to {bounds_path}")

    logger.info("Preprocessing pipeline completed successfully.")

def main():
    """Entry point for the preprocessing script."""
    # Default paths based on project structure
    input_file = os.path.join(get_raw_data_dir(), "am_data.csv")
    log_file = os.path.join(get_processed_data_dir(), "preprocessing.log")
    
    # Ensure directories exist
    ensure_directories()
    
    if not os.path.exists(input_file):
        # Check if manual data is expected elsewhere or if download failed
        # The download task (T014A) should have placed it here or raised an error.
        # If we are here and file is missing, it's a fatal error for this pipeline.
        print(f"Error: Raw data file not found at {input_file}.")
        print("Please ensure data is placed in data/raw/am_data.csv or run the download step first.")
        sys.exit(1)

    try:
        validate_and_preprocess(
            input_path=input_file,
            output_train_path=os.path.join(get_processed_data_dir(), "train.csv"),
            output_test_path=os.path.join(get_processed_data_dir(), "test.csv"),
            log_path=log_file
        )
    except Exception as e:
        logging.getLogger("preprocess").error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
