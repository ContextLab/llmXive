"""
Stability checks for data integrity and resource usage.
Includes NaN/Inf validation and memory monitoring.
"""
import numpy as np
import psutil
import os
import pandas as pd
from typing import Any, Dict, List, Union, Optional
from pathlib import Path

from code.utils.logger import get_pipeline_logger
from code.utils.error_handling import DataProcessingError, handle_error
from code.config import get_config

logger = get_pipeline_logger()

@handle_error
def check_nan_inf(df: pd.DataFrame, column: Optional[str] = None) -> Dict[str, int]:
    """
    Check for NaN and Inf values in a DataFrame or specific column.

    Args:
        df: The DataFrame to check.
        column: Optional specific column name to check.

    Returns:
        Dictionary with counts of NaN and Inf values.

    Raises:
        DataProcessingError: If NaN or Inf values are found in critical columns.
    """
    if df is None:
        raise DataProcessingError("Input DataFrame is None.")

    target = df[column] if column else df

    if isinstance(target, pd.DataFrame):
        nan_count = int(target.isna().sum().sum())
        inf_count = int(np.isinf(target.select_dtypes(include=[np.number])).sum().sum())
    else:
        # Series case
        nan_count = int(target.isna().sum())
        inf_count = int(np.isinf(target.select_dtypes(include=[np.number])).sum())

    result = {"nan_count": nan_count, "inf_count": inf_count}

    if nan_count > 0 or inf_count > 0:
        logger.warning(f"Stability check found {nan_count} NaN and {inf_count} Inf values.")
    
    return result

def get_memory_stats() -> Dict[str, Union[int, float]]:
    """
    Get current memory usage statistics.

    Returns:
        Dictionary with memory usage details.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return {
        "rss_mb": mem_info.rss / (1024 * 1024),
        "vms_mb": mem_info.vms / (1024 * 1024),
        "percent": process.memory_percent()
    }

@handle_error
def check_memory_usage(limit_gb: Optional[float] = None) -> bool:
    """
    Check if current memory usage exceeds a limit.

    Args:
        limit_gb: Limit in GB. If None, uses config default.

    Returns:
        True if within limits, False otherwise.
    """
    stats = get_memory_stats()
    
    if limit_gb is None:
        try:
            config = get_config()
            limit_gb = config.get("memory_limit_gb", 7.0)
        except Exception:
            limit_gb = 7.0

    current_gb = stats["rss_mb"] / 1024.0
    
    if current_gb > limit_gb:
        logger.error(f"Memory usage {current_gb:.2f} GB exceeds limit {limit_gb} GB.")
        return False
    
    logger.debug(f"Memory usage check passed: {current_gb:.2f} GB < {limit_gb} GB.")
    return True

@handle_error
def validate_dataframe(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> None:
    """
    Validate a DataFrame has required columns and no NaN/Inf in numeric cols.

    Args:
        df: DataFrame to validate.
        required_columns: List of column names that must exist.

    Raises:
        DataProcessingError: If validation fails.
    """
    if df is None:
        raise DataProcessingError("DataFrame is None.")
    
    if df.empty:
        raise DataProcessingError("DataFrame is empty.")

    if required_columns:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise DataProcessingError(f"Missing required columns: {missing}")

    # Check numeric columns for NaN/Inf
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        check = check_nan_inf(df, col)
        if check["nan_count"] > 0 or check["inf_count"] > 0:
            logger.warning(f"Column {col} has {check['nan_count']} NaN and {check['inf_count']} Inf values.")

@handle_error
def validate_features(features: Union[np.ndarray, pd.DataFrame]) -> None:
    """
    Validate feature matrix for model training.

    Args:
        features: Feature matrix.

    Raises:
        DataProcessingError: If features are invalid.
    """
    if isinstance(features, pd.DataFrame):
        validate_dataframe(features)
    elif isinstance(features, np.ndarray):
        if features.size == 0:
            raise DataProcessingError("Feature array is empty.")
        if np.any(np.isnan(features)) or np.any(np.isinf(features)):
            raise DataProcessingError("Feature array contains NaN or Inf values.")
    else:
        raise DataProcessingError(f"Unsupported feature type: {type(features)}")