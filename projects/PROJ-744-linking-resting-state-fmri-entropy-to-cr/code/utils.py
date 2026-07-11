import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any

def setup_logging(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """Setup logging to file and console."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Ensure directory exists
    ensure_dir(log_file)
    
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

def ensure_dir(file_path: str) -> None:
    """Ensure the directory of a file path exists."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

def safe_read_csv(path: str) -> Optional[pd.DataFrame]:
    """Safely read a CSV file."""
    try:
        return pd.read_csv(path)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to read CSV {path}: {e}")
        return None

def safe_write_csv(df: pd.DataFrame, path: str) -> bool:
    """Safely write a DataFrame to CSV."""
    try:
        ensure_dir(path)
        df.to_csv(path, index=False)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to write CSV {path}: {e}")
        return False

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for predictors."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    vif_data = {}
    X = df[predictors].values
    for i, col in enumerate(predictors):
        vif = variance_inflation_factor(X, i)
        vif_data[col] = vif
    return vif_data

def check_collinearity(df: pd.DataFrame, predictors: List[str], threshold: float = 5.0) -> bool:
    """Check for collinearity among predictors."""
    vif_data = calculate_vif(df, predictors)
    for col, vif in vif_data.items():
        if vif > threshold:
            logging.getLogger(__name__).warning(f"High collinearity detected for {col}: VIF={vif}")
            return True
    return False
