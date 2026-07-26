"""
Base test utilities and fixtures for the project.

This module provides common fixtures and helper functions for schema validation.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path

@pytest.fixture
def sample_dataframe():
    """
    Create a sample DataFrame for testing.
    """
    data = {
        "participant_id": ["P1", "P2", "P3"],
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "total_steps": [1000, 2000, 3000],
        "mean_mood": [3.0, 4.0, 5.0],
        "mood_std": [0.5, 0.6, 0.7]
    }
    return pd.DataFrame(data)

def load_schema(schema_path: Path) -> dict:
    """
    Load a YAML schema definition.

    Args:
        schema_path (Path): Path to the schema file.

    Returns:
        dict: The schema definition.
    """
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe(df: pd.DataFrame, schema: dict) -> tuple:
    """
    Validate a DataFrame against a schema.

    Args:
        df (pd.DataFrame): The DataFrame to validate.
        schema (dict): The schema definition.

    Returns:
        tuple: (is_valid, errors)
    """
    errors = []
    
    # Check required columns
    required_columns = schema.get("required", [])
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    # Check types (basic)
    properties = schema.get("properties", {})
    for col, prop in properties.items():
        if col in df.columns:
            if prop.get("type") == "integer" and not np.issubdtype(df[col].dtype, np.integer):
                errors.append(f"Column {col} should be integer")
            elif prop.get("type") == "number" and not np.issubdtype(df[col].dtype, np.number):
                errors.append(f"Column {col} should be number")
            elif prop.get("type") == "string" and not np.issubdtype(df[col].dtype, np.object_):
                errors.append(f"Column {col} should be string")
    
    is_valid = len(errors) == 0
    return is_valid, errors

@pytest.fixture
def schema_validator():
    """
    Provide a schema validator function.
    """
    return validate_dataframe
