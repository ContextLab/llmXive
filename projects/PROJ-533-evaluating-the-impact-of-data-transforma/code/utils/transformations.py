"""
Transformation utilities for normalizing data distributions.

Implements Box-Cox, Yeo-Johnson, and Rank-based Inverse Normal Transformations.
Handles positive-value constraints and logs interventions via the project logger.
"""
import numpy as np
from scipy import stats
from typing import Tuple, Optional, Union, List
import warnings
import logging

from pathlib import Path
from utils.logging_config import setup_pipeline_logger

# Ensure logger is configured
logger = setup_pipeline_logger()

def box_cox_transform(data: Union[np.ndarray, List[float]], 
                      lmbda: Optional[float] = None) -> Tuple[np.ndarray, float]:
    """
    Apply Box-Cox transformation to data.
    
    Box-Cox requires strictly positive data. If data contains zeros or negatives,
    this function raises a ValueError.
    
    Args:
        data: Input array-like data.
        lmbda: Lambda parameter. If None, optimal lambda is estimated.
    
    Returns:
        Tuple of (transformed_data, lambda_value)
    
    Raises:
        ValueError: If data contains non-positive values.
    """
    data_np = np.asarray(data, dtype=float)
    
    if np.any(data_np <= 0):
        raise ValueError("Box-Cox transformation requires strictly positive data. "
                       "Found non-positive values.")
    
    # Suppress convergence warnings from scipy for cleaner logs
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        if lmbda is None:
            transformed_data, lmbda = stats.boxcox(data_np)
        else:
            transformed_data = stats.boxcox(data_np, lmbda=lmbda)
    
    return transformed_data, lmbda

def safe_box_cox(data: Union[np.ndarray, List[float]], 
                 shift: bool = True) -> Tuple[Optional[np.ndarray], Optional[float], str]:
    """
    Safely attempt Box-Cox transformation, handling non-positive data.
    
    If data is not strictly positive, attempts to shift it by adding a constant
    (min_value + 1) to make all values positive before transformation.
    
    Args:
        data: Input array-like data.
        shift: If True, apply log-shift intervention for non-positive data.
    
    Returns:
        Tuple of (transformed_data, lambda_value, status_message)
        - transformed_data: np.ndarray if successful, None if failed.
        - lambda_value: float if successful, None if failed.
        - status_message: 'success', 'shifted', or 'failed'.
    """
    data_np = np.asarray(data, dtype=float)
    
    if np.any(data_np <= 0):
        if shift:
            min_val = np.min(data_np)
            shift_amount = abs(min_val) + 1.0
            shifted_data = data_np + shift_amount
            logger.info(f"Applied log-shift intervention: added {shift_amount} to data "
                      f"(min was {min_val}) to enable Box-Cox.")
            try:
                transformed_data, lmbda = box_cox_transform(shifted_data)
                return transformed_data, lmbda, "shifted"
            except Exception as e:
                logger.error(f"Shifted Box-Cox transformation failed: {e}")
                return None, None, "failed"
        else:
            logger.error("Box-Cox failed: Data contains non-positive values and shift is disabled.")
            return None, None, "failed"
    
    try:
        transformed_data, lmbda = box_cox_transform(data_np)
        return transformed_data, lmbda, "success"
    except Exception as e:
        logger.error(f"Box-Cox transformation failed: {e}")
        return None, None, "failed"

def yeo_johnson_transform(data: Union[np.ndarray, List[float]], 
                          lmbda: Optional[float] = None) -> Tuple[np.ndarray, float]:
    """
    Apply Yeo-Johnson transformation to data.
    
    Yeo-Johnson can handle zero and negative values, making it more flexible
    than Box-Cox.
    
    Args:
        data: Input array-like data.
        lmbda: Lambda parameter. If None, optimal lambda is estimated.
    
    Returns:
        Tuple of (transformed_data, lambda_value)
    """
    data_np = np.asarray(data, dtype=float)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        if lmbda is None:
            transformed_data, lmbda = stats.yeojohnson(data_np)
        else:
            transformed_data = stats.yeojohnson(data_np, lmbda=lmbda)
    
    return transformed_data, lmbda

def rank_inverse_normal_transform(data: Union[np.ndarray, List[float]], 
                                  method: str = 'average') -> np.ndarray:
    """
    Apply Rank-based Inverse Normal Transformation (RINT).
    
    This transformation ranks the data and maps the ranks to quantiles of
    the standard normal distribution. It is robust to outliers and does not
    assume a specific distribution shape.
    
    Args:
        data: Input array-like data.
        method: Method for handling ties in ranking ('average', 'min', 'max', 'dense', 'ordinal').
                Default is 'average'.
    
    Returns:
        Transformed array with standard normal distribution properties.
    """
    data_np = np.asarray(data, dtype=float)
    
    # Handle NaN values by replacing with NaN in output (or could impute before calling)
    mask = ~np.isnan(data_np)
    ranks = np.empty_like(data_np, dtype=float)
    ranks[~mask] = np.nan
    
    # Compute ranks for valid data
    valid_data = data_np[mask]
    _, ranks_valid = stats.rankdata(valid_data, method=method), None
    
    # Map ranks to normal quantiles
    # Using Blom's formula: (rank - 0.375) / (n + 0.25)
    n = len(valid_data)
    if n == 0:
        return np.zeros_like(data_np)
        
    probs = (ranks_valid - 0.375) / (n + 0.25)
    
    # Ensure probabilities are within (0, 1) to avoid inf in norm.ppf
    probs = np.clip(probs, 1e-10, 1 - 1e-10)
    
    transformed_valid = stats.norm.ppf(probs)
    
    ranks[mask] = transformed_valid
    
    return ranks

def apply_transformation(data: Union[np.ndarray, List[float]], 
                         transform_type: str = 'yeo_johnson',
                         **kwargs) -> Tuple[np.ndarray, dict]:
    """
    Apply a specified transformation to data.
    
    Args:
        data: Input array-like data.
        transform_type: Type of transformation ('box_cox', 'yeo_johnson', 'rank_inverse_normal').
        **kwargs: Additional arguments passed to the specific transformation function.
    
    Returns:
        Tuple of (transformed_data, metadata_dict)
        metadata_dict contains:
            - 'transform_type': str
            - 'lambda': float (if applicable)
            - 'status': str ('success', 'shifted', 'failed')
            - 'message': str (details about the transformation)
    """
    data_np = np.asarray(data, dtype=float)
    metadata = {
        'transform_type': transform_type,
        'lambda': None,
        'status': 'success',
        'message': 'Transformation applied successfully'
    }
    
    if transform_type == 'box_cox':
        try:
            transformed, lmbda = box_cox_transform(data_np)
            metadata['lambda'] = lmbda
        except ValueError as e:
            metadata['status'] = 'failed'
            metadata['message'] = str(e)
            raise
            
    elif transform_type == 'yeo_johnson':
        transformed, lmbda = yeo_johnson_transform(data_np, lmbda=kwargs.get('lmbda'))
        metadata['lambda'] = lmbda
        
    elif transform_type == 'rank_inverse_normal':
        transformed = rank_inverse_normal_transform(data_np, method=kwargs.get('method', 'average'))
        metadata['message'] = 'Rank-based inverse normal transformation applied'
        
    else:
        raise ValueError(f"Unknown transformation type: {transform_type}")
    
    return transformed, metadata

# Convenience functions for specific use cases
def transform_to_normality(data: Union[np.ndarray, List[float]], 
                           preferred_order: List[str] = None) -> Tuple[np.ndarray, str, dict]:
    """
    Attempt to normalize data by trying transformations in a preferred order.
    
    Args:
        data: Input data.
        preferred_order: List of transformation names to try in order.
                        Default: ['yeo_johnson', 'rank_inverse_normal', 'box_cox']
    
    Returns:
        Tuple of (transformed_data, successful_transform_type, metadata)
    """
    if preferred_order is None:
        preferred_order = ['yeo_johnson', 'rank_inverse_normal', 'box_cox']
    
    for transform_type in preferred_order:
        try:
            transformed, metadata = apply_transformation(data, transform_type)
            logger.info(f"Successfully transformed data using {transform_type}")
            return transformed, transform_type, metadata
        except Exception as e:
            logger.warning(f"Transformation {transform_type} failed: {e}")
            continue
    
    raise RuntimeError(f"All attempted transformations failed for data with {len(data)} points.")