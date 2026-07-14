import numpy as np
import psutil
import os
import pandas as pd
from typing import Any, Dict, List, Union, Optional
from code.utils.logger import get_pipeline_logger
from code.utils.error_handling import DataProcessingError

def check_nan_inf(data: Union[np.ndarray, List, pd.DataFrame], context: str = "Data") -> bool:
    """
    Check for NaN or Inf values in data.
    
    Args:
        data: Numpy array, list, or pandas DataFrame to check
        context: Context description for logging
        
    Returns:
        True if no NaN/Inf found (or non-numeric data), False otherwise
    """
    logger = get_pipeline_logger()
    
    if isinstance(data, pd.DataFrame):
        # Handle DataFrame case
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        has_issues = False
        
        for col in numeric_cols:
            arr = data[col].values
            if np.issubdtype(arr.dtype, np.floating):
                nan_mask = np.isnan(arr)
                inf_mask = np.isinf(arr)
                
                if np.any(nan_mask):
                    nan_count = np.sum(nan_mask)
                    logger.warning(f"{context} column '{col}' contains {nan_count} NaN values")
                    has_issues = True
                
                if np.any(inf_mask):
                    inf_count = np.sum(inf_mask)
                    logger.warning(f"{context} column '{col}' contains {inf_count} Inf values")
                    has_issues = True
        
        return not has_issues
    
    elif isinstance(data, list):
        try:
            data = np.array(data)
        except Exception as e:
            logger.error(f"{context}: Failed to convert list to numpy array: {e}")
            return False
    
    if isinstance(data, np.ndarray):
        if np.issubdtype(data.dtype, np.floating):
            has_nan = np.any(np.isnan(data))
            has_inf = np.any(np.isinf(data))
            
            if has_nan:
                nan_count = np.sum(np.isnan(data))
                logger.warning(f"{context} contains {nan_count} NaN values")
            if has_inf:
                inf_count = np.sum(np.isinf(data))
                logger.warning(f"{context} contains {inf_count} Inf values")
            
            return not (has_nan or has_inf)
    
    # For non-floating types, assume valid
    return True

def check_memory_usage(max_gb: float = 7.0) -> bool:
    """
    Check current process memory usage against a limit.
    
    Args:
        max_gb: Maximum allowed memory in GB
        
    Returns:
        True if usage is within limits, False otherwise
    """
    logger = get_pipeline_logger()
    try:
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        memory_gb = memory_mb / 1024
        
        logger.debug(f"Current memory usage: {memory_gb:.2f} GB / {max_gb:.2f} GB limit")
        
        if memory_gb > max_gb:
            logger.error(f"Memory usage ({memory_gb:.2f} GB) exceeds limit ({max_gb:.2f} GB)")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Failed to check memory usage: {e}")
        # Fail safe: assume OK if we can't check, but log the error
        return True

def validate_dataframe(df: pd.DataFrame, name: str = "DataFrame", strict: bool = False) -> bool:
    """
    Validate a DataFrame for common issues (NaN, Inf, empty, None).
    
    Args:
        df: pandas DataFrame to validate
        name: Name of the DataFrame for logging
        strict: If True, return False on any warning (NaN/Inf); otherwise just log
        
    Returns:
        True if valid, False otherwise
    """
    logger = get_pipeline_logger()
    is_valid = True
    
    if df is None:
        logger.error(f"{name} is None")
        return False
    
    if not isinstance(df, pd.DataFrame):
        logger.error(f"{name} is not a DataFrame (got {type(df).__name__})")
        return False
    
    if df.empty:
        logger.warning(f"{name} is empty")
        if strict:
            return False
    
    # Check for NaN values
    nan_counts = df.isna().sum()
    if nan_counts.any():
        cols_with_nan = nan_counts[nan_counts > 0]
        logger.warning(f"{name} has NaN values in columns: {cols_with_nan.to_dict()}")
        if strict:
            is_valid = False
    
    # Check for infinite values in numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        # Convert to float to safely check inf (integers can't be inf)
        if df[col].dtype in [np.float32, np.float64]:
            inf_count = np.isinf(df[col]).sum()
            if inf_count > 0:
                logger.warning(f"{name} column '{col}' has {inf_count} infinite values")
                if strict:
                    is_valid = False
    
    return is_valid

def get_memory_stats() -> Dict[str, float]:
    """
    Get detailed memory statistics for the current process.
    
    Returns:
        Dictionary with memory stats in GB
    """
    logger = get_pipeline_logger()
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        return {
            "rss_gb": mem_info.rss / 1024 / 1024 / 1024,
            "vms_gb": mem_info.vms / 1024 / 1024 / 1024,
            "percent": process.memory_percent()
        }
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        return {"rss_gb": 0.0, "vms_gb": 0.0, "percent": 0.0}

def validate_features(X: np.ndarray, y: Optional[np.ndarray] = None, name: str = "Features") -> bool:
    """
    Validate feature matrix and optional target vector for ML readiness.
    
    Args:
        X: Feature matrix (2D array or DataFrame)
        y: Optional target vector
        name: Name for logging
        
    Returns:
        True if valid, False otherwise
    """
    logger = get_pipeline_logger()
    is_valid = True
    
    # Check X
    if isinstance(X, pd.DataFrame):
        if not check_nan_inf(X, f"{name} (X)"):
            is_valid = False
        if X.shape[0] == 0:
            logger.error(f"{name} (X) has no samples")
            return False
    elif isinstance(X, np.ndarray):
        if not check_nan_inf(X, f"{name} (X)"):
            is_valid = False
        if X.size == 0:
            logger.error(f"{name} (X) is empty")
            return False
        if X.ndim != 2:
            logger.warning(f"{name} (X) is not 2D (shape: {X.shape})")
    
    # Check y if provided
    if y is not None:
        if isinstance(y, pd.Series):
            if not check_nan_inf(y.values, f"{name} (y)"):
                is_valid = False
        elif isinstance(y, np.ndarray):
            if not check_nan_inf(y, f"{name} (y)"):
                is_valid = False
        else:
            try:
                y_arr = np.array(y)
                if not check_nan_inf(y_arr, f"{name} (y)"):
                    is_valid = False
            except Exception as e:
                logger.error(f"Failed to validate target vector: {e}")
                is_valid = False
    
    return is_valid