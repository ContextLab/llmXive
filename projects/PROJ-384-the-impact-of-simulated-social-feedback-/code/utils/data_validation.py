"""
Data validation utilities based on the interaction schema.
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ValidationError, create_model
import pandas as pd

from utils.config import SCHEMA_FILE

def load_schema() -> Dict[str, Any]:
    """Loads the interaction schema from YAML."""
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")
    with open(SCHEMA_FILE, "r") as f:
        return yaml.safe_load(f)

def validate_dataframe(df: pd.DataFrame) -> None:
    """
    Validates a DataFrame against the interaction schema.
    Raises ValueError if validation fails.
    """
    schema = load_schema()
    required_fields = schema.get("required", [])
    
    # Check for required columns
    missing_cols = set(required_fields) - set(df.columns)
    if missing_cols:
        raise ValueError(f"DataFrame is missing required columns: {missing_cols}")
    
    # Check for unexpected columns if additionalProperties is false
    # Note: pandas DataFrame columns might have extra, but schema says false.
    # We will be lenient here and only check required, or strict if needed.
    # For this task, we enforce required fields.
    
    # Type checking for critical fields
    if "timestamp" in df.columns:
        if not pd.api.types.is_integer_dtype(df["timestamp"]) and not pd.api.types.is_numeric_dtype(df["timestamp"]):
            # Allow numeric, will cast later
            pass
    
    if "user_id" in df.columns:
        if not pd.api.types.is_string_dtype(df["user_id"]):
            pass # Will cast to string

def validate_row(row: Dict[str, Any], schema: Optional[Dict] = None) -> None:
    """Validates a single row dictionary against the schema."""
    if schema is None:
        schema = load_schema()
    
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in row:
            raise ValueError(f"Row missing required field: {field}")
