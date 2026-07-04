import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Set up logging configuration."""
    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler if specified
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

def ensure_dir(path: str) -> Path:
    """Ensure directory exists, create if necessary."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def safe_write_csv(df: pd.DataFrame, path: str) -> bool:
    """Safely write a DataFrame to CSV."""
    try:
        ensure_dir(str(Path(path).parent))
        df.to_csv(path, index=False)
        return True
    except Exception as e:
        logging.error(f"Failed to write CSV {path}: {e}")
        return False

def safe_read_csv(path: str) -> Optional[pd.DataFrame]:
    """Safely read a CSV file."""
    try:
        if not os.path.exists(path):
            logging.warning(f"File not found: {path}")
            return None
        return pd.read_csv(path)
    except Exception as e:
        logging.error(f"Failed to read CSV {path}: {e}")
        return None

def calculate_vif(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for columns in a DataFrame.
    
    Args:
        df: DataFrame with numeric columns.
        exclude_cols: Columns to exclude from VIF calculation.
        
    Returns:
        Series with VIF values for each column.
    """
    if exclude_cols is None:
        exclude_cols = []
        
    # Select numeric columns not in exclude list
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cols_to_check = [col for col in numeric_cols if col not in exclude_cols]
    
    if len(cols_to_check) < 2:
        return pd.Series(dtype=float)
        
    X = df[cols_to_check]
    vif_data = pd.Series(index=cols_to_check, dtype=float)
    
    for col in cols_to_check:
        # Regress col against all other cols
        other_cols = [c for c in cols_to_check if c != col]
        if not other_cols:
            continue
            
        y = X[col]
        X_other = X[other_cols]
        
        # Add constant for intercept
        X_other_const = sm.add_constant(X_other) if 'sm' in globals() else X_other
        
        try:
            import statsmodels.api as sm
            model = sm.OLS(y, sm.add_constant(X_other)).fit()
            r_squared = model.rsquared
            vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else np.inf
            vif_data[col] = vif
        except Exception as e:
            logging.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = np.nan
            
    return vif_data

def check_collinearity(df: pd.DataFrame, threshold: float = 5.0) -> bool:
    """
    Check for multicollinearity using VIF.
    
    Args:
        df: DataFrame with predictors.
        threshold: VIF threshold above which collinearity is flagged.
        
    Returns:
        True if collinearity is detected (any VIF > threshold), False otherwise.
    """
    vif_values = calculate_vif(df)
    if vif_values.empty:
        return False
        
    max_vif = vif_values.max()
    if max_vif > threshold:
        logging.warning(f"High collinearity detected: max VIF = {max_vif:.2f} > {threshold}")
        return True
    return False
