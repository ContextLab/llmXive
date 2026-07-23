import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)

# Define the schema contract for per_sample_errors.csv
# This schema MUST be adhered to by T014 (pipeline.py) before statistical testing (T024/T025)
PER_SAMPLE_ERRORS_SCHEMA = {
    "columns": [
        "sample_id",       # Unique identifier for the sample (string or int)
        "method",          # Name of the UQ method (string)
        "prediction",      # Point prediction (float)
        "lower_bound",     # Lower bound of uncertainty interval (float)
        "upper_bound",     # Upper bound of uncertainty interval (float)
        "ground_truth",    # Actual observed value (float)
        "dataset"          # Name of the dataset used (string)
    ],
    "dtypes": {
        "sample_id": "object",
        "method": "object",
        "prediction": "float64",
        "lower_bound": "float64",
        "upper_bound": "float64",
        "ground_truth": "float64",
        "dataset": "object"
    }
}

def validate_per_sample_errors(df: pd.DataFrame) -> bool:
    """
    Validates that a DataFrame matches the per_sample_errors schema contract.
    
    Args:
        df: The DataFrame to validate.
        
    Returns:
        True if valid, raises ValueError if invalid.
    """
    required_cols = set(PER_SAMPLE_ERRORS_SCHEMA["columns"])
    actual_cols = set(df.columns)
    
    if not required_cols.issubset(actual_cols):
        missing = required_cols - actual_cols
        raise ValueError(f"Schema validation failed: Missing columns {missing}. "
                         f"Expected columns: {PER_SAMPLE_ERRORS_SCHEMA['columns']}")
    
    # Check dtypes for numeric columns
    for col, dtype in PER_SAMPLE_ERRORS_SCHEMA["dtypes"].items():
        if col in df.columns:
            if not np.issubdtype(df[col].dtype, np.floating) and col != "sample_id" and col != "method" and col != "dataset":
                # Allow object for string columns, float for numeric
                if dtype == "float64" and not np.issubdtype(df[col].dtype, np.floating):
                    raise ValueError(f"Schema validation failed: Column '{col}' must be float64, got {df[col].dtype}")
    
    # Check for NaNs in critical numeric columns
    critical_numeric = ["prediction", "lower_bound", "upper_bound", "ground_truth"]
    for col in critical_numeric:
        if df[col].isna().any():
            raise ValueError(f"Schema validation failed: Column '{col}' contains NaN values.")
    
    logger.info("Schema validation passed for per_sample_errors DataFrame.")
    return True

def save_schema_contract(output_dir: str = "results") -> str:
    """
    Saves the schema definition to a JSON file in the results directory
    to serve as the contract for downstream tasks (T014, T024).
    
    Args:
        output_dir: Directory to save the schema file.
        
    Returns:
        Path to the saved schema file.
    """
    os.makedirs(output_dir, exist_ok=True)
    schema_path = Path(output_dir) / "per_sample_errors_schema.json"
    
    import json
    with open(schema_path, "w") as f:
        json.dump(PER_SAMPLE_ERRORS_SCHEMA, f, indent=2)
    
    logger.info(f"Schema contract saved to {schema_path}")
    return str(schema_path)

def create_empty_schema_example(output_dir: str = "results") -> str:
    """
    Creates an empty CSV file with the correct headers to serve as a 
    template/contract example.
    
    Args:
        output_dir: Directory to save the example CSV.
        
    Returns:
        Path to the saved example CSV.
    """
    os.makedirs(output_dir, exist_ok=True)
    example_path = Path(output_dir) / "per_sample_errors_schema_example.csv"
    
    # Create an empty DataFrame with the correct schema
    df = pd.DataFrame(columns=PER_SAMPLE_ERRORS_SCHEMA["columns"])
    # Ensure correct dtypes explicitly
    for col, dtype in PER_SAMPLE_ERRORS_SCHEMA["dtypes"].items():
        df[col] = df[col].astype(dtype)
    
    df.to_csv(example_path, index=False)
    logger.info(f"Schema example saved to {example_path}")
    return str(example_path)
