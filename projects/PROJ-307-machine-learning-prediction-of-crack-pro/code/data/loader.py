"""
Data loading module for NASA and NIST fracture datasets.
"""
import json
import os
from pathlib import Path
from typing import Union, Optional
import pandas as pd
import yaml
import requests
import logging

logger = logging.getLogger(__name__)

def fetch_url_content(url: str, timeout: int = 30) -> Optional[str]:
    """Fetch content from a URL."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None

def load_nasa_data(path: Union[str, Path]) -> pd.DataFrame:
    """Load NASA Fracture Control Database."""
    logger.info(f"Loading NASA data from {path}")
    df = pd.read_csv(path)
    return df

def load_nist_data(path: Union[str, Path]) -> pd.DataFrame:
    """Load NIST Materials Data Repository."""
    logger.info(f"Loading NIST data from {path}")
    df = pd.read_csv(path)
    return df

def validate_schema(df: pd.DataFrame, schema_path: Union[str, Path]) -> bool:
    """
    Validate DataFrame against a JSON/YAML schema.
    
    This function consumes `contracts/dataset.schema.yaml` to ensure
    the loaded dataset contains all required columns and meets basic
    type constraints.
    
    Args:
        df: The pandas DataFrame to validate.
        schema_path: Path to the YAML schema file.
        
    Returns:
        bool: True if validation passes, False otherwise.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is malformed.
    """
    schema_path = Path(schema_path)
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return False
        
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Validate required columns
    required_cols = schema.get('required_columns', [])
    missing = set(required_cols) - set(df.columns)
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    
    # Validate type constraints if present
    type_constraints = schema.get('type_constraints', {})
    for col, constraints in type_constraints.items():
        if col not in df.columns:
            continue
        
        col_type = constraints.get('type')
        min_val = constraints.get('min')
        
        if col_type == 'numeric':
            if not pd.api.types.is_numeric_dtype(df[col]):
                logger.error(f"Column '{col}' must be numeric but is {df[col].dtype}")
                return False
            if min_val is not None:
                if (df[col] < min_val).any():
                    logger.error(f"Column '{col}' contains values below minimum {min_val}")
                    return False
        elif col_type == 'string':
            if not pd.api.types.is_string_dtype(df[col]):
                # Allow object dtype which often represents strings
                if df[col].dtype != 'object':
                    logger.error(f"Column '{col}' must be string but is {df[col].dtype}")
                    return False
    
    logger.info("Schema validation passed successfully")
    return True