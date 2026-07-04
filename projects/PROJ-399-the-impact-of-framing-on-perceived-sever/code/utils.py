"""
Utility functions for the PROJ-399 pipeline.
Includes data validation, configuration loading, and random seed management.
"""
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the config file.

    Returns:
        Dictionary containing configuration values.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, 'r') as f:
        return yaml.safe_load(f)


def set_random_seed(config: Optional[Dict[str, Any]] = None, seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility based on config or explicit argument.

    Args:
        config: Configuration dictionary (optional).
        seed: Explicit seed value (optional). If provided, overrides config.
    """
    if seed is None:
        if config is None:
            config = load_config()
        seed = config.get("random_seed", 42)

    np.random.seed(seed)
    # If pandas uses numpy under the hood, this affects it too.
    # For explicit pandas seed control if available in future versions:
    # pd.options.mode.future_copy_on_write = True # Just a placeholder for future logic


def validate_stimulus_columns(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> bool:
    """
    Validate that a DataFrame contains the required stimulus columns.

    Args:
        df: The DataFrame to validate.
        required_columns: List of required column names. Defaults to
            ['stimulus_id', 'content_domain', 'headline'] if None.

    Returns:
        True if all required columns are present, False otherwise.

    Raises:
        ValueError: If the input is not a DataFrame or is empty.
    """
    if required_columns is None:
        required_columns = ['stimulus_id', 'content_domain', 'headline']

    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required stimulus columns: {missing}")

    return True


def validate_stimulus_data_integrity(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform basic integrity checks on stimulus data beyond column existence.

    Args:
        df: The DataFrame to validate.

    Returns:
        Dictionary with validation results and any found issues.
    """
    results = {
        "is_valid": True,
        "issues": []
    }

    try:
        validate_stimulus_columns(df)
    except ValueError as e:
        results["is_valid"] = False
        results["issues"].append(str(e))
        return results

    # Check for duplicate stimulus_ids if they are supposed to be unique
    if 'stimulus_id' in df.columns:
        duplicates = df['stimulus_id'].duplicated().sum()
        if duplicates > 0:
            results["issues"].append(f"Found {duplicates} duplicate stimulus_ids.")
            # Depending on project needs, this might be a hard failure or just a warning.
            # For now, we flag it.

    # Check for empty strings or NaN in critical text fields
    text_cols = ['content_domain', 'headline']
    for col in text_cols:
        if col in df.columns:
            if df[col].isna().any():
                results["issues"].append(f"Column '{col}' contains missing values (NaN).")
            if df[col].apply(lambda x: isinstance(x, str) and x.strip() == "").any():
                results["issues"].append(f"Column '{col}' contains empty strings.")

    if results["issues"]:
        results["is_valid"] = False

    return results
