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
        
    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If file is not valid YAML.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def set_random_seed(seed: Optional[int] = None, config: Optional[Dict[str, Any]] = None) -> int:
    """
    Set random seed for reproducibility from config or argument.
    
    Args:
        seed: Seed value to use. If None, looks in config.
        config: Optional config dictionary. If None, loads from default path.
        
    Returns:
        The seed value that was set.
        
    Raises:
        ValueError: If no seed found in config or argument.
    """
    if seed is None:
        if config is None:
            config = load_config()
        seed = config.get('random_seed')
        if seed is None:
            raise ValueError("No random seed provided in config or argument")
    
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    return seed

def validate_stimulus_columns(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that a DataFrame contains all required stimulus columns.
    
    Args:
        df: DataFrame to validate.
        required_columns: List of column names that must be present.
        
    Returns:
        True if all required columns are present.
        
    Raises:
        ValueError: If any required column is missing.
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required stimulus columns: {missing}")
    return True

def validate_stimulus_data_integrity(df: pd.DataFrame) -> bool:
    """
    Validate the integrity of stimulus data by checking:
    1. Required columns are present: 'stimulus_id', 'content_domain', 'headline'
    2. No null values in required columns
    3. stimulus_id is unique
    
    Args:
        df: DataFrame containing stimulus data.
        
    Returns:
        True if all validations pass.
        
    Raises:
        ValueError: If any validation fails with a specific message.
    """
    required_cols = ['stimulus_id', 'content_domain', 'headline']
    
    # Check 1: Required columns
    validate_stimulus_columns(df, required_cols)
    
    # Check 2: No nulls in required columns
    for col in required_cols:
        if df[col].isnull().any():
            raise ValueError(f"Column '{col}' contains null values")
    
    # Check 3: Unique stimulus_id
    if df['stimulus_id'].duplicated().any():
        raise ValueError("Duplicate values found in 'stimulus_id' column")
    
    return True