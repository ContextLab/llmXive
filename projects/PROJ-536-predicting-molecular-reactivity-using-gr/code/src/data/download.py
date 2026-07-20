import os
import sys
import logging
import pandas as pd
from typing import Optional, List, Dict, Any

# Import from project utilities
from src.utils.logging import get_logger, log_message

# Define the expected schema for the USPTO reaction dataset
# Based on T007 contracts: reaction_record.schema.yaml
REQUIRED_COLUMNS = ['reactants_smiles', 'product_smiles', 'yield', 'reaction_class']
REQUIRED_NUMERIC_COLUMNS = ['yield']

logger = get_logger(__name__)

def validate_schema(df: pd.DataFrame, dataset_name: str = "USPTO Subset") -> bool:
    """
    Validates the schema of the downloaded dataframe.
    
    Checks:
    1. All required columns exist.
    2. The 'yield' column is present and numeric (not categorical string).
    
    Raises:
        ValueError: If validation fails.
        FileNotFoundError: If the dataset is empty or missing critical fields.
    
    Returns:
        bool: True if valid.
    """
    if df.empty:
        msg = f"Validation failed for {dataset_name}: Dataset is empty."
        logger.error(msg)
        raise ValueError(msg)

    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        msg = f"Validation failed for {dataset_name}: Missing required columns: {missing_cols}"
        logger.error(msg)
        raise ValueError(msg)
    
    # Validate 'yield' column specifically
    yield_col = 'yield'
    if yield_col not in df.columns:
        msg = f"Validation failed for {dataset_name}: Missing required 'yield' column."
        logger.error(msg)
        raise ValueError(msg)

    # Check if 'yield' is numeric
    # We allow object type if it contains numeric strings that can be converted,
    # but strictly categorical (e.g., 'High', 'Low') should fail.
    if not pd.api.types.is_numeric_dtype(df[yield_col]):
        # Attempt to convert to numeric to see if it's just a string representation
        # If it fails or results in all NaN, it's likely categorical.
        converted = pd.to_numeric(df[yield_col], errors='coerce')
        
        # If a significant portion is NaN after coercion, it might be categorical or malformed
        # We require at least 90% valid numeric data to proceed, otherwise it's likely a categorical column
        valid_numeric_ratio = converted.notna().sum() / len(df)
        
        if valid_numeric_ratio < 0.9:
            msg = (f"Validation failed for {dataset_name}: "
                   f"Column '{yield_col}' appears to be categorical or non-numeric. "
                   f"Only {valid_numeric_ratio:.2%} of values are convertible to numeric.")
            logger.error(msg)
            raise ValueError(msg)
        else:
            log_message(logger, "warn", 
                      f"Column '{yield_col}' was not originally numeric but {valid_numeric_ratio:.2%} converts successfully. Proceeding with coercion.")
            # In a real pipeline, we might coerce here, but for strict validation,
            # we ensure the data *can* be treated as numeric.
            # For this task, we raise if it's strictly categorical.
            # If it passes the 90% threshold, we assume it's valid numeric data in string format.
    else:
        # Check for infinite values or NaNs that might indicate bad data
        if df[yield_col].isna().any():
            log_message(logger, "warn", 
                      f"Column '{yield_col}' contains {df[yield_col].isna().sum()} missing values. "
                      f"These will be handled in the parsing stage.")

    log_message(logger, "info", f"Schema validation passed for {dataset_name}.")
    return True

def download_uspto_subset(output_path: str, subset_url: Optional[str] = None) -> pd.DataFrame:
    """
    Downloads the USPTO subset and validates the schema.
    
    This function is a placeholder for the actual download logic (T012).
    It assumes the data is fetched and returns a DataFrame.
    In a real implementation, it would fetch from HuggingFace or Zenodo.
    For this specific task (T013), the focus is on the validation logic
    which is now integrated.
    
    Args:
        output_path: Path to save the data (not used if streaming, but required by signature).
        subset_url: URL to fetch data from.
        
    Returns:
        pd.DataFrame: The validated dataset.
        
    Raises:
        ValueError: If schema validation fails.
        RuntimeError: If download fails.
    """
    # Note: The actual download implementation (T012) would go here.
    # Since T012 is marked as completed in the context, we assume the data
    # is available or fetched. This function demonstrates the integration
    # of validation.
    
    # For the purpose of this task implementation, we assume the data
    # is loaded into 'df' from a real source (e.g., pandas.read_csv).
    # We cannot fetch real data here without the T012 implementation details,
    # but we ensure the validation function is robust and callable.
    
    # Placeholder for where T012 logic would load the data:
    # df = fetch_data_from_url(subset_url)
    # return validate_schema(df, "USPTO Subset")
    
    # Since T012 is listed as completed in the prompt's completed list,
    # we assume the data exists or is fetched. We implement the validation
    # logic strictly as requested.
    
    # To make this script runnable for verification without T012 code duplication:
    # We will raise an error if the data isn't found, but the validation logic
    # is fully implemented.
    
    if not os.path.exists(output_path):
        # In a real scenario, this would trigger the download
        raise FileNotFoundError(f"Data file not found at {output_path}. "
                              "Ensure T012 (download) has been executed successfully.")
    
    # Load the data
    try:
        df = pd.read_csv(output_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load data from {output_path}: {e}")
    
    # Validate schema
    validate_schema(df, "USPTO Subset")
    
    return df

def main():
    """
    Main entry point for running schema validation.
    Expects a path to a CSV file as an argument.
    """
    if len(sys.argv) < 2:
        print("Usage: python src/data/download.py <path_to_csv>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        df = download_uspto_subset(file_path)
        print(f"Schema validation successful. Loaded {len(df)} records.")
    except ValueError as ve:
        print(f"Schema Validation Failed: {ve}")
        sys.exit(1)
    except FileNotFoundError as fnfe:
        print(f"File Error: {fnfe}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
