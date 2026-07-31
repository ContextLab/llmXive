"""
Stability checks for data quality and resource monitoring.

This module provides utilities for:
- NaN/Inf validation in dataframes and arrays
- Memory usage monitoring and thresholds
- Feature validation for model inputs
"""
import numpy as np
import psutil
import os
import pandas as pd
from typing import Any, Dict, List, Union, Optional
from code.utils.logger import get_pipeline_logger

logger = get_pipeline_logger(__name__)


def check_nan_inf(data: Union[np.ndarray, pd.DataFrame, List[float]], 
                 column_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Check for NaN and Inf values in data structures.
    
    Args:
        data: Input data (numpy array, pandas DataFrame, or list)
        column_names: Optional list of column names if data is a list/array
        
    Returns:
        Dictionary with check results:
        - 'has_nan': bool
        - 'has_inf': bool
        - 'nan_count': int
        - 'inf_count': int
        - 'nan_indices': list of indices/columns with NaN
        - 'inf_indices': list of indices/columns with Inf
    """
    result = {
        'has_nan': False,
        'has_inf': False,
        'nan_count': 0,
        'inf_count': 0,
        'nan_indices': [],
        'inf_indices': []
    }
    
    if isinstance(data, pd.DataFrame):
        # Check DataFrame
        nan_mask = data.isna()
        inf_mask = np.isinf(data.select_dtypes(include=[np.number]).values)
        
        result['nan_count'] = int(nan_mask.sum().sum())
        result['inf_count'] = int(np.sum(inf_mask))
        
        if result['nan_count'] > 0:
            result['has_nan'] = True
            # Get column names with NaN
            nan_cols = nan_mask.any(axis=0)
            result['nan_indices'] = list(data.columns[nan_cols])
            logger.warning(f"Found {result['nan_count']} NaN values in columns: {result['nan_indices']}")
        
        if result['inf_count'] > 0:
            result['has_inf'] = True
            # Get column names with Inf
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            inf_cols = pd.Series(inf_mask.any(axis=0), index=numeric_cols)
            result['inf_indices'] = list(inf_cols[inf_cols].index)
            logger.warning(f"Found {result['inf_count']} Inf values in columns: {result['inf_indices']}")
            
    elif isinstance(data, np.ndarray):
        # Check numpy array
        nan_mask = np.isnan(data)
        inf_mask = np.isinf(data)
        
        result['nan_count'] = int(np.sum(nan_mask))
        result['inf_count'] = int(np.sum(inf_mask))
        
        if result['nan_count'] > 0:
            result['has_nan'] = True
            result['nan_indices'] = list(np.argwhere(nan_mask))
            logger.warning(f"Found {result['nan_count']} NaN values in array")
        
        if result['inf_count'] > 0:
            result['has_inf'] = True
            result['inf_indices'] = list(np.argwhere(inf_mask))
            logger.warning(f"Found {result['inf_count']} Inf values in array")
            
    elif isinstance(data, list):
        # Check list
        try:
            arr = np.array(data)
            return check_nan_inf(arr, column_names)
        except (ValueError, TypeError):
            # Handle nested lists or mixed types
            for i, item in enumerate(data):
                try:
                    val = float(item)
                    if np.isnan(val):
                        result['has_nan'] = True
                        result['nan_count'] += 1
                        result['nan_indices'].append(i)
                    elif np.isinf(val):
                        result['has_inf'] = True
                        result['inf_count'] += 1
                        result['inf_indices'].append(i)
                except (ValueError, TypeError):
                    pass
                
            if result['nan_count'] > 0:
                logger.warning(f"Found {result['nan_count']} NaN values in list")
            if result['inf_count'] > 0:
                logger.warning(f"Found {result['inf_count']} Inf values in list")
                
    else:
        logger.warning(f"Unsupported data type for NaN/Inf check: {type(data)}")
        
    return result


def get_memory_stats() -> Dict[str, Any]:
    """
    Get current memory usage statistics.
    
    Returns:
        Dictionary with memory stats:
        - 'process_memory_mb': Current process memory usage in MB
        - 'total_memory_mb': Total system memory in MB
        - 'available_memory_mb': Available system memory in MB
        - 'percent_used': Percentage of total memory used by process
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    system_mem = psutil.virtual_memory()
    
    return {
        'process_memory_mb': mem_info.rss / (1024 * 1024),
        'total_memory_mb': system_mem.total / (1024 * 1024),
        'available_memory_mb': system_mem.available / (1024 * 1024),
        'percent_used': (mem_info.rss / system_mem.total) * 100
    }


def check_memory_usage(max_memory_mb: float = 6000.0) -> Dict[str, Any]:
    """
    Check if current memory usage is within acceptable limits.
    
    Args:
        max_memory_mb: Maximum allowed memory usage in MB (default 6000MB for 7GB limit)
        
    Returns:
        Dictionary with check results:
        - 'within_limit': bool
        - 'current_usage_mb': Current memory usage
        - 'max_allowed_mb': Maximum allowed memory
        - 'margin_mb': Remaining memory margin
        - 'warning': str (warning message if approaching limit)
    """
    stats = get_memory_stats()
    current_usage = stats['process_memory_mb']
    
    result = {
        'within_limit': current_usage < max_memory_mb,
        'current_usage_mb': current_usage,
        'max_allowed_mb': max_memory_mb,
        'margin_mb': max_memory_mb - current_usage,
        'warning': None
    }
    
    if current_usage > max_memory_mb:
        result['warning'] = f"CRITICAL: Memory usage ({current_usage:.1f} MB) exceeds limit ({max_memory_mb:.1f} MB)"
        logger.error(result['warning'])
    elif current_usage > max_memory_mb * 0.9:
        result['warning'] = f"WARNING: Memory usage ({current_usage:.1f} MB) is above 90% of limit ({max_memory_mb:.1f} MB)"
        logger.warning(result['warning'])
    elif current_usage > max_memory_mb * 0.8:
        result['warning'] = f"INFO: Memory usage ({current_usage:.1f} MB) is above 80% of limit ({max_memory_mb:.1f} MB)"
        logger.info(result['warning'])
        
    return result


def validate_dataframe(df: pd.DataFrame, 
                     required_columns: Optional[List[str]] = None,
                     max_memory_mb: float = 6000.0,
                     allow_nan: bool = False,
                     allow_inf: bool = False) -> Dict[str, Any]:
    """
    Comprehensive validation of a DataFrame for pipeline readiness.
    
    Args:
        df: Input DataFrame to validate
        required_columns: Optional list of columns that must be present
        max_memory_mb: Maximum allowed memory usage
        allow_nan: Whether NaN values are allowed
        allow_inf: Whether Inf values are allowed
        
    Returns:
        Dictionary with validation results:
        - 'valid': bool (True if all checks pass)
        - 'checks': dict with individual check results
        - 'errors': list of error messages
        - 'warnings': list of warning messages
    """
    result = {
        'valid': True,
        'checks': {},
        'errors': [],
        'warnings': []
    }
    
    # Check 1: Required columns
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            result['valid'] = False
            error_msg = f"Missing required columns: {missing_cols}"
            result['errors'].append(error_msg)
            logger.error(error_msg)
        else:
            result['checks']['required_columns'] = True
            logger.debug("All required columns present")
            
    # Check 2: NaN/Inf values
    nan_inf_result = check_nan_inf(df)
    result['checks']['nan_inf'] = nan_inf_result
    
    if not allow_nan and nan_inf_result['has_nan']:
        result['valid'] = False
        error_msg = f"DataFrame contains {nan_inf_result['nan_count']} NaN values"
        result['errors'].append(error_msg)
        logger.error(error_msg)
        
    if not allow_inf and nan_inf_result['has_inf']:
        result['valid'] = False
        error_msg = f"DataFrame contains {nan_inf_result['inf_count']} Inf values"
        result['errors'].append(error_msg)
        logger.error(error_msg)
        
    # Check 3: Memory usage
    memory_result = check_memory_usage(max_memory_mb)
    result['checks']['memory'] = memory_result
    
    if not memory_result['within_limit']:
        result['valid'] = False
        error_msg = f"Memory usage exceeds limit: {memory_result['current_usage_mb']:.1f} MB > {max_memory_mb:.1f} MB"
        result['errors'].append(error_msg)
        logger.error(error_msg)
        
    # Check 4: Empty DataFrame
    if df.empty:
        result['valid'] = False
        error_msg = "DataFrame is empty"
        result['errors'].append(error_msg)
        logger.error(error_msg)
        
    # Check 5: Data types (ensure numeric columns for modeling)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    
    if len(numeric_cols) == 0:
        result['warnings'].append("No numeric columns found in DataFrame")
        logger.warning("No numeric columns found in DataFrame")
        
    result['checks']['data_types'] = {
        'numeric_columns': len(numeric_cols),
        'non_numeric_columns': len(non_numeric_cols)
    }
    
    return result


def validate_features(X: Union[np.ndarray, pd.DataFrame], 
                    feature_names: Optional[List[str]] = None,
                    min_samples: int = 100,
                    max_memory_mb: float = 6000.0) -> Dict[str, Any]:
    """
    Validate feature matrix for model training.
    
    Args:
        X: Feature matrix (numpy array or DataFrame)
        feature_names: Optional list of feature names
        min_samples: Minimum number of samples required
        max_memory_mb: Maximum allowed memory usage
        
    Returns:
        Dictionary with validation results:
        - 'valid': bool
        - 'checks': dict with individual check results
        - 'errors': list of error messages
        - 'warnings': list of warning messages
    """
    result = {
        'valid': True,
        'checks': {},
        'errors': [],
        'warnings': []
    }
    
    # Convert to DataFrame if numpy array
    if isinstance(X, np.ndarray):
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        X_df = pd.DataFrame(X, columns=feature_names)
    elif isinstance(X, pd.DataFrame):
        X_df = X
        if feature_names is None:
            feature_names = X_df.columns.tolist()
    else:
        result['valid'] = False
        error_msg = f"Unsupported feature type: {type(X)}"
        result['errors'].append(error_msg)
        logger.error(error_msg)
        return result
        
    # Check 1: NaN/Inf
    nan_inf_result = check_nan_inf(X_df)
    result['checks']['nan_inf'] = nan_inf_result
    
    if nan_inf_result['has_nan']:
        result['warnings'].append(f"Features contain {nan_inf_result['nan_count']} NaN values")
        
    if nan_inf_result['has_inf']:
        result['warnings'].append(f"Features contain {nan_inf_result['inf_count']} Inf values")
        
    # Check 2: Sample count
    n_samples = X_df.shape[0]
    if n_samples < min_samples:
        result['valid'] = False
        error_msg = f"Insufficient samples: {n_samples} < {min_samples}"
        result['errors'].append(error_msg)
        logger.error(error_msg)
    else:
        result['checks']['sample_count'] = n_samples
        logger.debug(f"Sample count OK: {n_samples}")
        
    # Check 3: Feature count
    n_features = X_df.shape[1]
    if n_features == 0:
        result['valid'] = False
        error_msg = "No features found in feature matrix"
        result['errors'].append(error_msg)
        logger.error(error_msg)
    else:
        result['checks']['feature_count'] = n_features
        logger.debug(f"Feature count OK: {n_features}")
        
    # Check 4: Memory usage
    memory_result = check_memory_usage(max_memory_mb)
    result['checks']['memory'] = memory_result
    
    if not memory_result['within_limit']:
        result['valid'] = False
        error_msg = f"Feature matrix memory usage exceeds limit"
        result['errors'].append(error_msg)
        logger.error(error_msg)
        
    return result