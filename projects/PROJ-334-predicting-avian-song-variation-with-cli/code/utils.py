import logging
import os
import sys
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from pyproj import Transformer

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema definition from disk.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_schema(df: pd.DataFrame, schema_path: str) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against a JSON/YAML schema definition.
    
    Checks:
    1. Required columns exist.
    2. Column data types match expected types (basic checks).
    3. No null values in required fields.
    
    Args:
        df: The DataFrame to validate.
        schema_path: Path to the schema file (YAML).
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError as e:
        return False, [str(e)]
    
    if not isinstance(schema, dict):
        return False, ["Invalid schema format: expected a dictionary"]

    required_columns = schema.get("required_columns", [])
    column_types = schema.get("column_types", {})
    unique_columns = schema.get("unique_columns", [])

    # Check required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")

    # Check data types
    for col, expected_type in column_types.items():
        if col in df.columns:
            if expected_type == "integer":
                if not pd.api.types.is_integer_dtype(df[col]):
                    # Allow float if it contains integers, but warn if mixed
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        errors.append(f"Column '{col}' should be integer, got {df[col].dtype}")
            elif expected_type == "float":
                if not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(f"Column '{col}' should be numeric, got {df[col].dtype}")
            elif expected_type == "string":
                if not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                    # Often object is used for strings in pandas
                    pass 
            elif expected_type == "datetime":
                if not pd.api.types.is_datetime64_any_dtype(df[col]):
                    errors.append(f"Column '{col}' should be datetime, got {df[col].dtype}")

    # Check for nulls in required columns
    for col in required_columns:
        if col in df.columns and df[col].isnull().any():
            errors.append(f"Column '{col}' contains null values")

    # Check uniqueness
    for col in unique_columns:
        if col in df.columns:
            if df[col].duplicated().any():
                errors.append(f"Column '{col}' contains duplicate values")

    return len(errors) == 0, errors

def reproject_coordinates(df: pd.DataFrame, 
                          source_crs: str = "EPSG:4326", 
                          target_crs: str = "EPSG:4326",
                          lon_col: str = "lon", 
                          lat_col: str = "lat") -> pd.DataFrame:
    """
    Reproject coordinates in a DataFrame.
    
    Args:
        df: Input DataFrame.
        source_crs: Source coordinate reference system.
        target_crs: Target coordinate reference system.
        lon_col: Name of the longitude/longitude column.
        lat_col: Name of the latitude/latitude column.
        
    Returns:
        DataFrame with updated coordinates if transformation occurred.
    """
    if source_crs == target_crs:
        return df

    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    
    def transform_row(row):
        try:
            new_x, new_y = transformer.transform(row[lon_col], row[lat_col])
            return pd.Series({lon_col: new_x, lat_col: new_y})
        except Exception:
            return pd.Series({lon_col: row[lon_col], lat_col: row[lat_col]})

    # Only apply if columns exist
    if lon_col in df.columns and lat_col in df.columns:
        transformed = df.apply(transform_row, axis=1)
        df[lon_col] = transformed[lon_col]
        df[lat_col] = transformed[lat_col]
    
    return df

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Perform division safely, returning a default value if denominator is zero.
    """
    if denominator == 0:
        return default
    return numerator / denominator

def format_bytes(num_bytes: float) -> str:
    """
    Format a byte count into a human-readable string.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"

def validate_song_record(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against the SongRecord schema.
    """
    schema_path = Path("contracts/song_record.schema.yaml")
    if not schema_path.exists():
        # Fallback if path is relative to project root but run from elsewhere
        schema_path = Path("contracts/song_record.schema.yaml").resolve()
    return validate_schema(df, str(schema_path))

def validate_climate_snapshot(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against the ClimateSnapshot schema.
    """
    schema_path = Path("contracts/climate_snapshot.schema.yaml")
    return validate_schema(df, str(schema_path))

def validate_analysis_dataset(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against the AnalysisDataset schema.
    """
    schema_path = Path("contracts/analysis_dataset.schema.yaml")
    return validate_schema(df, str(schema_path))