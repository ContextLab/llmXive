import os
import sys
import json
import logging
import argparse
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import NotFittedError

# Import config for paths and seeds
try:
    from config import get_config, ensure_dirs
except ImportError:
    # Fallback for direct execution context if config is not in path yet
    # In a real run, this should be resolved via PYTHONPATH or installed package
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import get_config, ensure_dirs

logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> pd.DataFrame:
    """
    Loads the processed dataset (with interaction features already added)
    from the specified CSV path.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Processed data file not found at {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    if df.empty:
        raise ValueError(f"Loaded dataset from {input_path} is empty.")
    
    return df

def generate_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates interaction features between Temperature and composition elements.
    Note: According to task T022, this should have been done prior to normalization.
    This function serves as a verification or re-application step if needed,
    but primarily ensures the data is ready for normalization.
    
    Returns a copy of the dataframe with interaction columns appended.
    """
    # Identify temperature column
    temp_col = 'rolling_temperature'
    if temp_col not in df.columns:
        logger.warning(f"Temperature column '{temp_col}' not found. Skipping interaction generation.")
        return df

    # Identify composition columns (assumed to be numeric columns starting with '%')
    # Or specifically known alloying elements if defined in schema
    # For robustness, we look for columns that are numeric and not the target
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter out target variable 'grain_size' and the temperature itself
    feature_cols = [c for c in numeric_cols if c not in ['grain_size', 'rolling_temperature']]
    
    interaction_cols = []
    
    for col in feature_cols:
        # Create interaction: Temperature * Element
        new_col_name = f"{temp_col}_x_{col}"
        df[new_col_name] = df[temp_col] * df[col]
        interaction_cols.append(new_col_name)
        logger.debug(f"Created interaction feature: {new_col_name}")

    logger.info(f"Generated {len(interaction_cols)} interaction features.")
    return df

def normalize_features(df: pd.DataFrame, target_col: str = 'grain_size') -> tuple:
    """
    Normalizes all numeric features using StandardScaler.
    
    Excludes the target column from normalization.
    
    Args:
        df: Input DataFrame.
        target_col: Name of the target column to exclude.
        
    Returns:
        tuple: (normalized_df, scaler)
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    # Identify numeric columns excluding target
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [c for c in numeric_cols if c != target_col]
    
    if not feature_cols:
        logger.warning("No numeric features found to normalize.")
        return df, None

    scaler = StandardScaler()
    
    logger.info(f"Normalizing {len(feature_cols)} features: {feature_cols}")
    
    # Fit and transform
    try:
        normalized_values = scaler.fit_transform(df[feature_cols])
    except ValueError as e:
        logger.error(f"Error during normalization: {e}")
        raise

    # Create a copy to avoid SettingWithCopyWarning
    df_normalized = df.copy()
    
    # Replace original columns with normalized values
    for i, col in enumerate(feature_cols):
        df_normalized[col] = normalized_values[:, i]
        
    logger.info("Normalization complete.")
    return df_normalized, scaler

def validate_data_quality(df: pd.DataFrame) -> bool:
    """
    Validates that the dataframe has no NaN values in numeric columns
    and that ranges are reasonable.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in numeric_cols:
        if df[col].isnull().any():
            logger.error(f"NaN values found in column: {col}")
            return False
        
        # Check for infinite values
        if np.isinf(df[col]).any():
            logger.error(f"Infinite values found in column: {col}")
            return False

    logger.info("Data quality validation passed.")
    return True

def run_preprocessing_pipeline(input_path: str, output_path: str, save_scaler_path: str = None) -> bool:
    """
    Orchestrates the preprocessing pipeline:
    1. Load data
    2. Generate interactions (if not present)
    3. Validate data
    4. Normalize features
    5. Save results
    """
    try:
        # 1. Load
        df = load_processed_data(input_path)
        
        # 2. Interactions (T022 requirement - ensure they exist)
        # We check if interaction columns exist, if not, generate them.
        # Assuming interaction columns have a specific naming convention or we just generate them.
        # For safety, we generate them if the specific 'Temperature_x_Element' pattern is missing.
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        has_interactions = any('_x_' in c for c in numeric_cols)
        
        if not has_interactions:
            logger.info("Interaction features missing. Generating them now.")
            df = generate_interaction_features(df)
        else:
            logger.info("Interaction features detected. Skipping generation.")

        # 3. Validate
        if not validate_data_quality(df):
            logger.error("Data validation failed. Aborting pipeline.")
            return False

        # 4. Normalize
        df_normalized, scaler = normalize_features(df, target_col='grain_size')

        # 5. Save
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        df_normalized.to_csv(output_path, index=False)
        logger.info(f"Normalized data saved to {output_path}")

        if scaler and save_scaler_path:
            import joblib
            save_scaler_path = Path(save_scaler_path)
            save_scaler_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(scaler, save_scaler_path)
            logger.info(f"Scaler saved to {save_scaler_path}")

        return True

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return False

def main():
    parser = argparse.ArgumentParser(description="Preprocess data: Interactions and Normalization")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV (raw/processed)")
    parser.add_argument("--output", type=str, required=True, help="Path to output normalized CSV")
    parser.add_argument("--scaler", type=str, default=None, help="Path to save the fitted scaler")
    parser.add_argument("--log", type=str, default="INFO", help="Log level")

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log.upper(), logging.INFO))

    # Ensure config directories exist if needed
    ensure_dirs()

    success = run_preprocessing_pipeline(
        input_path=args.input,
        output_path=args.output,
        save_scaler_path=args.scaler
    )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()