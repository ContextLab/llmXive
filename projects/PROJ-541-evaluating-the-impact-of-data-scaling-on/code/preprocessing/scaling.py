"""
Data scaling functions for preprocessing.
Implements Standardization, Min-Max, and Robust scaling.
"""
import numpy as np
import logging
from typing import Union
import pandas as pd

def standardize_data(data: Union[np.ndarray, pd.Series, pd.DataFrame]) -> Union[np.ndarray, pd.Series, pd.DataFrame]:
    """
    Standardize data to mean=0, std=1.
    
    Args:
        data: Input data
    
    Returns:
        Standardized data
    """
    if isinstance(data, (pd.Series, pd.DataFrame)):
        mean = data.mean()
        std = data.std()
        if std == 0:
            logging.warning("Zero standard deviation in standardize_data")
            return data
        return (data - mean) / std
    else:
        data = np.array(data)
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            logging.warning("Zero standard deviation in standardize_data")
            return data
        return (data - mean) / std

def min_max_scale(data: Union[np.ndarray, pd.Series, pd.DataFrame], min_val: float = 0.0, max_val: float = 1.0) -> Union[np.ndarray, pd.Series, pd.DataFrame]:
    """
    Scale data to a range [min_val, max_val].
    
    Args:
        data: Input data
        min_val: Minimum value of the range
        max_val: Maximum value of the range
    
    Returns:
        Scaled data
    """
    if isinstance(data, (pd.Series, pd.DataFrame)):
        data_min = data.min()
        data_max = data.max()
        if data_min == data_max:
            logging.warning("Zero range in min_max_scale")
            return data
        return min_val + (data - data_min) * (max_val - min_val) / (data_max - data_min)
    else:
        data = np.array(data)
        data_min = np.min(data)
        data_max = np.max(data)
        if data_min == data_max:
            logging.warning("Zero range in min_max_scale")
            return data
        return min_val + (data - data_min) * (max_val - min_val) / (data_max - data_min)

def robust_scale(data: Union[np.ndarray, pd.Series, pd.DataFrame]) -> Union[np.ndarray, pd.Series, pd.DataFrame]:
    """
    Scale data using median and IQR.
    
    Args:
        data: Input data
    
    Returns:
        Scaled data
    """
    if isinstance(data, (pd.Series, pd.DataFrame)):
        median = data.median()
        iqr = data.quantile(0.75) - data.quantile(0.25)
        if iqr == 0:
            logging.warning("Zero IQR in robust_scale, skipping iteration")
            return None
        return (data - median) / iqr
    else:
        data = np.array(data)
        median = np.median(data)
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        if iqr == 0:
            logging.warning("Zero IQR in robust_scale, skipping iteration")
            return None
        return (data - median) / iqr
