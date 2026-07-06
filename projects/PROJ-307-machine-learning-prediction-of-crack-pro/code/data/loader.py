"""
Data loading module for NASA and NIST fracture datasets.
"""
import json
import os
from pathlib import Path
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
    """Validate DataFrame against a JSON/YAML schema."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_cols = schema.get('required_columns', [])
    missing = set(required_cols) - set(df.columns)
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True
