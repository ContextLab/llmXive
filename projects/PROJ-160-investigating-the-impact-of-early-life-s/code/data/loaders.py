"""
Data Loading Utilities.
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Union, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_csv(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    logger.info(f"Loading CSV: {path}")
    return pd.read_csv(path, **kwargs)

def load_tsv(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """Load a TSV file into a DataFrame."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    logger.info(f"Loading TSV: {path}")
    return pd.read_csv(path, sep='\t', **kwargs)

def validate_columns(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """Check if required columns exist in the DataFrame."""
    missing = [col for col in required_columns if col not in df.columns]
    return len(missing) == 0, missing

def parse_numeric_columns(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Convert specified columns to numeric, coercing errors to NaN."""
    if columns is None:
        # Try to infer all object columns
        columns = df.select_dtypes(include=['object']).columns.tolist()
    
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df
