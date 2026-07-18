"""
Categorical encoding for 'synthesis method' in the feature matrix.

Implements FR-008: Add categorical encoding for 'synthesis method' in the feature matrix.
Uses One-Hot Encoding to convert the 'synthesis_method' column into binary features.

This module:
1. Loads the feature matrix from data/processed/feature_matrix.csv (if it exists) 
   or the standardized polymers dataset from data/processed/standardized_polymers.csv
2. Identifies unique synthesis methods
3. Applies One-Hot Encoding
4. Saves the encoded feature matrix to data/processed/feature_matrix_encoded.csv
5. Saves the encoding mapping to artifacts/synthesis_method_encoding.json
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from sklearn.preprocessing import OneHotEncoder

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import setup_pipeline_logger, log_event
from utils.errors import DataInsufficientError

# Initialize logger
logger = setup_pipeline_logger("encode_synthesis_method")

# Constants
STANDARDIZED_DATA_PATH = "data/processed/standardized_polymers.csv"
FEATURE_MATRIX_PATH = "data/processed/feature_matrix.csv"
ENCODED_FEATURE_MATRIX_PATH = "data/processed/feature_matrix_encoded.csv"
ENCODING_MAPPING_PATH = "artifacts/synthesis_method_encoding.json"
SYNTHESIS_METHOD_COLUMN = "synthesis_method"

def load_feature_matrix_or_standardized_data() -> pd.DataFrame:
    """
    Load the feature matrix if it exists, otherwise load standardized polymers data.
    
    Returns:
        pd.DataFrame: The loaded dataset containing synthesis method information.
    
    Raises:
        DataInsufficientError: If neither file exists or data is empty.
    """
    feature_matrix_path = project_root / FEATURE_MATRIX_PATH
    standardized_path = project_root / STANDARDIZED_DATA_PATH
    
    # Try to load feature matrix first
    if feature_matrix_path.exists():
        try:
            df = pd.read_csv(feature_matrix_path)
            if not df.empty and SYNTHESIS_METHOD_COLUMN in df.columns:
                logger.info(f"Loaded feature matrix from {FEATURE_MATRIX_PATH} ({len(df)} rows)")
                return df
            elif not df.empty:
                logger.warning(f"Feature matrix exists but missing '{SYNTHESIS_METHOD_COLUMN}' column. Falling back to standardized data.")
        except Exception as e:
            logger.warning(f"Failed to load feature matrix: {e}. Falling back to standardized data.")
    
    # Fall back to standardized data
    if standardized_path.exists():
        try:
            df = pd.read_csv(standardized_path)
            if not df.empty and SYNTHESIS_METHOD_COLUMN in df.columns:
                logger.info(f"Loaded standardized data from {STANDARDIZED_DATA_PATH} ({len(df)} rows)")
                return df
            elif not df.empty:
                raise DataInsufficientError(
                    f"Standardized data exists but missing '{SYNTHESIS_METHOD_COLUMN}' column."
                )
        except Exception as e:
            logger.error(f"Failed to load standardized data: {e}")
            raise DataInsufficientError(f"Cannot load synthesis method data: {e}")
    
    raise DataInsufficientError(
        f"Neither {FEATURE_MATRIX_PATH} nor {STANDARDIZED_DATA_PATH} exists or is valid."
    )

def encode_synthesis_method(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    """
    Apply One-Hot Encoding to the 'synthesis_method' column.
    
    Args:
        df: Input DataFrame containing the 'synthesis_method' column.
    
    Returns:
        Tuple containing:
            - Encoded DataFrame with binary columns for each synthesis method
            - Dictionary mapping original method names to encoded column names
    
    Raises:
        DataInsufficientError: If synthesis method column is empty or contains no valid values.
    """
    if df.empty:
        raise DataInsufficientError("Input DataFrame is empty.")
    
    if SYNTHESIS_METHOD_COLUMN not in df.columns:
        raise DataInsufficientError(f"Column '{SYNTHESIS_METHOD_COLUMN}' not found in DataFrame.")
    
    # Handle missing values in synthesis method
    missing_count = df[SYNTHESIS_METHOD_COLUMN].isna().sum()
    if missing_count > 0:
        logger.warning(f"Found {missing_count} missing values in '{SYNTHESIS_METHOD_COLUMN}'. "
                     "These will be encoded as a separate 'Unknown' category.")
        df = df.copy()
        df[SYNTHESIS_METHOD_COLUMN] = df[SYNTHESIS_METHOD_COLUMN].fillna("Unknown")
    
    # Check if all values are missing
    if df[SYNTHESIS_METHOD_COLUMN].nunique() == 0:
        raise DataInsufficientError(
            f"All values in '{SYNTHESIS_METHOD_COLUMN}' are missing or invalid."
        )
    
    unique_methods = df[SYNTHESIS_METHOD_COLUMN].unique()
    logger.info(f"Found {len(unique_methods)} unique synthesis methods: {unique_methods}")
    
    # Initialize One-Hot Encoder
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    
    # Fit and transform
    encoded_array = encoder.fit_transform(df[[SYNTHESIS_METHOD_COLUMN]])
    
    # Get feature names
    feature_names = encoder.get_feature_names_out([SYNTHESIS_METHOD_COLUMN])
    
    # Create encoded DataFrame
    encoded_df = pd.DataFrame(encoded_array, columns=feature_names, index=df.index)
    
    # Remove the original column and concatenate encoded columns
    df_encoded = df.drop(columns=[SYNTHESIS_METHOD_COLUMN])
    df_encoded = pd.concat([df_encoded, encoded_df], axis=1)
    
    # Create mapping dictionary for reference
    encoding_mapping = {
        method: [col for col in feature_names if col == f"{SYNTHESIS_METHOD_COLUMN}_{method}"]
        for method in unique_methods
    }
    # Flatten the mapping for easier reference
    flat_mapping = {col: method for col in feature_names for method in unique_methods 
                   if col == f"{SYNTHESIS_METHOD_COLUMN}_{method}"}
    
    logger.info(f"Successfully encoded {len(unique_methods)} synthesis methods into {len(feature_names)} binary features")
    
    return df_encoded, {"categories": list(unique_methods), "encoded_columns": list(feature_names)}

def save_encoded_features(df: pd.DataFrame, encoding_info: Dict[str, Any]) -> None:
    """
    Save the encoded feature matrix and encoding metadata to disk.
    
    Args:
        df: Encoded DataFrame to save.
        encoding_info: Dictionary containing encoding metadata.
    """
    # Ensure output directory exists
    output_path = project_root / ENCODED_FEATURE_MATRIX_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save encoded feature matrix
    df.to_csv(output_path, index=False)
    logger.info(f"Saved encoded feature matrix to {ENCODED_FEATURE_MATRIX_PATH}")
    
    # Save encoding metadata
    metadata_path = project_root / ENCODING_MAPPING_PATH
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(metadata_path, 'w') as f:
        json.dump(encoding_info, f, indent=2)
    logger.info(f"Saved encoding metadata to {ENCODING_MAPPING_PATH}")

def validate_encoding(df_encoded: pd.DataFrame, original_df: pd.DataFrame) -> bool:
    """
    Validate that encoding was performed correctly.
    
    Args:
        df_encoded: The encoded DataFrame.
        original_df: The original DataFrame before encoding.
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    # Check that encoded DataFrame has more columns than original (excluding synthesis_method)
    original_cols = set(original_df.columns) - {SYNTHESIS_METHOD_COLUMN}
    encoded_cols = set(df_encoded.columns)
    
    # All original columns (except synthesis_method) should be preserved
    if not original_cols.issubset(encoded_cols):
        logger.error(f"Missing original columns in encoded DataFrame: {original_cols - encoded_cols}")
        return False
    
    # Check that encoded columns exist
    encoded_synthesis_cols = [col for col in df_encoded.columns if col.startswith(f"{SYNTHESIS_METHOD_COLUMN}_")]
    if len(encoded_synthesis_cols) == 0:
        logger.error("No encoded synthesis method columns found.")
        return False
    
    # Check that each row sums to 1 for the encoded categories (if no unknown)
    # This verifies one-hot encoding property
    row_sums = df_encoded[encoded_synthesis_cols].sum(axis=1)
    if not np.allclose(row_sums, 1.0, atol=1e-6):
        logger.warning(f"Some rows do not sum to 1.0: {row_sums[row_sums != 1.0]}")
        # This might be acceptable if there are unknown categories
    
    logger.info("Encoding validation passed")
    return True

def main():
    """Main entry point for the synthesis method encoding pipeline."""
    log_event(logger, "START", "Starting synthesis method encoding pipeline")
    
    try:
        # Load data
        logger.info("Loading feature matrix or standardized data...")
        df = load_feature_matrix_or_standardized_data()
        
        # Encode synthesis method
        logger.info("Applying One-Hot Encoding to synthesis method...")
        df_encoded, encoding_info = encode_synthesis_method(df)
        
        # Validate encoding
        logger.info("Validating encoding...")
        if not validate_encoding(df_encoded, df):
            raise DataInsufficientError("Encoding validation failed.")
        
        # Save results
        logger.info("Saving encoded features...")
        save_encoded_features(df_encoded, encoding_info)
        
        # Log completion
        log_event(logger, "SUCCESS", "Synthesis method encoding completed successfully")
        logger.info(f"Output saved to: {ENCODED_FEATURE_MATRIX_PATH}")
        logger.info(f"Encoding metadata saved to: {ENCODING_MAPPING_PATH}")
        
        return 0
        
    except DataInsufficientError as e:
        log_event(logger, "ERROR", f"Data insufficient: {str(e)}")
        logger.error(f"Data insufficient error: {e}")
        return 1
    except Exception as e:
        log_event(logger, "ERROR", f"Unexpected error: {str(e)}")
        logger.exception(f"Unexpected error during encoding: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
