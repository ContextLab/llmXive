"""
Data loading and validation for the crack propagation prediction pipeline.
"""
import json
import os
from pathlib import Path
import pandas as pd
import yaml
import requests
from code.config import ensure_dirs, RAW_DATA_DIR

def fetch_url_content(url: str) -> str:
    """
    Fetch content from a URL.
    
    Args:
        url: URL to fetch
        
    Returns:
        Content as string
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def load_nasa_data(filepath: str) -> pd.DataFrame:
    """
    Load NASA fracture control database data.
    
    Args:
        filepath: Path to NASA data file
        
    Returns:
        DataFrame with NASA data
    """
    return pd.read_csv(filepath)

def load_nist_data(filepath: str) -> pd.DataFrame:
    """
    Load NIST materials data repository data.
    
    Args:
        filepath: Path to NIST data file
        
    Returns:
        DataFrame with NIST data
    """
    return pd.read_csv(filepath)

def validate_schema(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Validate DataFrame against a JSON schema.
    
    Args:
        df: DataFrame to validate
        schema_path: Path to schema file
        
    Returns:
        True if valid, False otherwise
    """
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_columns = schema.get('required', [])
    for col in required_columns:
        if col not in df.columns:
            return False
    return True
