"""
Data Loader Module for PROJ-263.

Implements FR-002: Parse downloaded UCI datasets and identify continuous numeric variables.
Also includes T017.5: Explicit variable type validation.
"""
import os
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd

from config import get_data_dir, get_log_level

# Configure logging based on project config
logging.basicConfig(
    level=get_log_level(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for type detection
NUMERIC_DTYPES = ['int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64', 'float16', 'float32', 'float64']


def load_uci_dataset_raw(dataset_name: str, delimiter: str = ',') -> pd.DataFrame:
    """
    Load a raw UCI dataset from the data/raw directory.

    Args:
        dataset_name: Name of the dataset (e.g., 'wine', 'ionosphere').
        delimiter: CSV delimiter (default ',').

    Returns:
        DataFrame containing the raw dataset.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
    """
    data_dir = get_data_dir()
    # Handle common naming variations (e.g., 'Wine' vs 'wine')
    search_name = dataset_name.lower().replace(' ', '_')
    
    # Look for common file extensions
    extensions = ['.csv', '.data', '.txt']
    file_path = None

    for ext in extensions:
        candidate = Path(data_dir) / f"{search_name}{ext}"
        if candidate.exists():
            file_path = candidate
            break
        
        # Check for underscore variations if not found immediately
        candidate_underscore = Path(data_dir) / f"{search_name.replace('-', '_')}{ext}"
        if candidate_underscore.exists():
            file_path = candidate_underscore
            break

    if file_path is None:
        raise FileNotFoundError(f"Could not find dataset file for '{dataset_name}' in {data_dir}. Searched: {search_name}.*")

    logger.info(f"Loading raw dataset from: {file_path}")
    
    # Attempt to load, handling potential header issues
    try:
        # First attempt: assume header exists
        df = pd.read_csv(file_path, delimiter=delimiter)
        
        # Check if the first row looks like data (all numeric) but we assumed header
        # This is a heuristic; UCI datasets vary.
        # If the first column is non-numeric but looks like an index or ID, we might need to adjust.
        # For now, we trust the file format or let pandas infer.
        
        # Specific handling for Wine dataset which often lacks headers in raw form
        if 'wine' in search_name and len(df.columns) == 1 and ',' in df.iloc[0, 0]:
            # It might be a single column of comma-separated values
            df = pd.read_csv(file_path, delimiter=',', header=None)
            # Assign generic column names
            df.columns = [f'col_{i}' for i in range(len(df.columns))]
            
        return df
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        raise


def identify_continuous_variables(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Identify continuous numeric variables in the DataFrame.
    
    Implements FR-002: Parse and identify continuous numeric variables.
    
    Args:
        df: The input DataFrame.
        
    Returns:
        A dictionary mapping variable names to their detected type.
        Specifically returns a list of column names that are continuous numeric.
    """
    continuous_cols = []
    categorical_cols = []
    
    for col in df.columns:
        # Check if the column is numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            # Heuristic for continuous vs discrete integer:
            # If it's a float, it's likely continuous.
            # If it's an integer, check if it has many unique values relative to its range.
            # For simplicity in this context, we treat all numeric as candidates, 
            # but we filter out obvious IDs or very low-cardinality integers if needed.
            # Given the task "identify continuous numeric", we assume the user 
            # wants to simulate on the numeric features.
            continuous_cols.append(col)
        else:
            # Check if it can be converted to numeric
            try:
                converted = pd.to_numeric(df[col], errors='raise')
                continuous_cols.append(col)
            except (ValueError, TypeError):
                categorical_cols.append(col)
                
    logger.info(f"Identified {len(continuous_cols)} continuous numeric variables: {continuous_cols}")
    if categorical_cols:
        logger.info(f"Found {len(categorical_cols)} categorical/non-numeric variables: {categorical_cols}")
        
    return {
        "continuous": continuous_cols,
        "categorical": categorical_cols
    }


def validate_variable_type(df: pd.DataFrame, columns: List[str], strict: bool = True) -> Tuple[bool, List[str]]:
    """
    Explicitly validate that selected columns are continuous numeric.
    
    Implements T017.5: Explicit variable type validation.
    
    Args:
        df: The input DataFrame.
        columns: List of column names to validate.
        strict: If True, raise error on invalid type. If False, return list of invalid columns.
        
    Returns:
        Tuple of (is_valid, list_of_invalid_columns)
        
    Raises:
        ValueError: If strict=True and invalid columns are found.
    """
    invalid_cols = []
    
    for col in columns:
        if col not in df.columns:
            invalid_cols.append(f"{col} (missing)")
            continue
        
        if not pd.api.types.is_numeric_dtype(df[col]):
            # Try conversion
            try:
                pd.to_numeric(df[col], errors='raise')
            except (ValueError, TypeError):
                invalid_cols.append(col)
                
    if invalid_cols and strict:
        raise ValueError(f"Columns are not continuous numeric: {invalid_cols}")
        
    return len(invalid_cols) == 0, invalid_cols


def prepare_dataset_for_simulation(dataset_name: str, target_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Main entry point to load and prepare a dataset for simulation.
    
    1. Loads the raw data.
    2. Identifies continuous numeric variables.
    3. Validates types if specific columns are requested.
    4. Returns a DataFrame containing only the continuous numeric variables.
    
    Args:
        dataset_name: Name of the UCI dataset.
        target_columns: Optional list of specific columns to use. If None, uses all continuous numeric.
        
    Returns:
        DataFrame with only continuous numeric variables.
    """
    df = load_uci_dataset_raw(dataset_name)
    
    if target_columns is None:
        # Identify all continuous variables
        types = identify_continuous_variables(df)
        selected_cols = types["continuous"]
        logger.info(f"Auto-selected continuous columns: {selected_cols}")
    else:
        # Validate and use provided columns
        is_valid, invalid = validate_variable_type(df, target_columns, strict=True)
        if not is_valid:
            raise ValueError(f"Requested columns contain non-numeric types: {invalid}")
        selected_cols = target_columns
        
    # Filter the dataframe
    result_df = df[selected_cols].copy()
    
    # Ensure all are actually numeric (pandas might have mixed types in some edge cases)
    result_df = result_df.apply(pd.to_numeric, errors='coerce')
    
    # Drop rows with NaN resulting from coercion (handled in T018, but good to be clean here)
    initial_rows = len(result_df)
    result_df = result_df.dropna()
    if len(result_df) < initial_rows:
        logger.warning(f"Dropped {initial_rows - len(result_df)} rows with non-numeric coercion failures.")
        
    logger.info(f"Prepared dataset '{dataset_name}' with {len(result_df)} rows and {len(result_df.columns)} continuous variables.")
    
    return result_df


def main():
    """
    CLI entry point for testing the data loader.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Load and inspect UCI datasets for simulation.")
    parser.add_argument("--dataset", type=str, required=True, help="Name of the dataset (e.g., wine, ionosphere)")
    parser.add_argument("--columns", type=str, nargs="+", default=None, help="Specific columns to use (optional)")
    
    args = parser.parse_args()
    
    try:
        df = prepare_dataset_for_simulation(args.dataset, args.columns)
        print(f"\nDataset Summary for '{args.dataset}':")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"Data Types:\n{df.dtypes}")
        print(f"\nFirst 5 rows:\n{df.head()}")
        
        # Save a quick summary to processed data for verification
        processed_dir = Path(get_data_dir()) / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "dataset": args.dataset,
            "rows": len(df),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
        
        import json
        summary_path = processed_dir / f"{args.dataset.lower().replace(' ', '_')}_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\nSummary saved to: {summary_path}")
        
    except Exception as e:
        logger.error(f"Failed to process dataset: {e}")
        raise


if __name__ == "__main__":
    main()
