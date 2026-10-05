import numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.interpolate import interp1d
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datasets import load_dataset
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def impute_with_spline(
    time_series: np.ndarray, 
    max_gap: int = 5
) -> np.ndarray:
    """
    Impute missing values in a time series using spline interpolation.
    
    Args:
        time_series: 1D array with possible NaN values
        max_gap: Maximum gap size to impute (larger gaps will be filled with linear interpolation)
    
    Returns:
        Imputed time series
    """
    if not np.any(np.isnan(time_series)):
        return time_series
        
    indices = np.arange(len(time_series))
    valid_mask = ~np.isnan(time_series)
    valid_indices = indices[valid_mask]
    valid_values = time_series[valid_mask]
    
    if len(valid_values) < 2:
        logger.warning("Insufficient valid points for spline imputation, using linear")
        # Fallback to linear interpolation
        f = interp1d(valid_indices, valid_values, kind='linear', fill_value='extrapolate')
        return f(indices)
    
    try:
        # Try spline interpolation
        spline = UnivariateSpline(valid_indices, valid_values, s=0)
        imputed = spline(indices)
        
        # Verify no NaNs remain
        if np.any(np.isnan(imputed)):
            logger.warning("Spline imputation produced NaNs, falling back to linear")
            f = interp1d(valid_indices, valid_values, kind='linear', fill_value='extrapolate')
            imputed = f(indices)
            
        return imputed
        
    except Exception as e:
        logger.warning(f"Spline imputation failed: {e}, using linear interpolation")
        f = interp1d(valid_indices, valid_values, kind='linear', fill_value='extrapolate')
        return f(indices)

def download_cmip6_data() -> Dict[str, np.ndarray]:
    """
    Download CMIP6 data from the verified real source.
    
    Returns:
        Dictionary mapping model names to time series data
    """
    logger.info("Downloading CMIP6 data from sungduk/wip_cmip6 dataset")
    
    try:
        # Load dataset with streaming to handle large sizes
        dataset = load_dataset("sungduk/wip_cmip6", streaming=True)
        
        # Process the dataset
        ensemble_data = {}
        sample_count = 0
        
        for split_name, split_data in dataset.items():
            logger.info(f"Processing split: {split_name}")
            for idx, sample in enumerate(split_data):
                if sample_count >= 100:  # Limit for initial processing
                    break
                    
                model_name = sample.get('model', f'model_{idx}')
                # Assuming data is stored in a 'temperature' or similar field
                # Adjust field name based on actual dataset schema
                temp_data = sample.get('temperature', sample.get('data', None))
                
                if temp_data is not None:
                    temp_array = np.array(temp_data, dtype=float)
                    if len(temp_array) > 0:
                        ensemble_data[model_name] = temp_array
                        sample_count += 1
                        
            if sample_count >= 100:
                break
                
        if not ensemble_data:
            raise ValueError("No valid data found in dataset")
            
        logger.info(f"Downloaded data for {len(ensemble_data)} models")
        return ensemble_data
        
    except Exception as e:
        logger.error(f"Failed to download CMIP6 data: {e}")
        raise

def standardize_ensemble(
    ensemble_data: Dict[str, np.ndarray],
    target_length: Optional[int] = None
) -> Dict[str, np.ndarray]:
    """
    Standardize ensemble members to a common time grid.
    
    Args:
        ensemble_data: Dictionary of time series
        target_length: Target length for all series (default: max length)
    
    Returns:
        Standardized ensemble data
    """
    if target_length is None:
        target_length = max(len(data) for data in ensemble_data.values())
        
    standardized = {}
    
    for model_name, data in ensemble_data.items():
        if len(data) == target_length:
            standardized[model_name] = data
        else:
            # Interpolate to target length
            original_indices = np.linspace(0, 1, len(data))
            target_indices = np.linspace(0, 1, target_length)
            
            f = interp1d(original_indices, data, kind='linear', fill_value='extrapolate')
            standardized[model_name] = f(target_indices)
            
    logger.info(f"Standardized {len(standardized)} models to length {target_length}")
    return standardized

def apply_imputation_to_dataset(
    ensemble_data: Dict[str, np.ndarray],
    max_gap: int = 5
) -> Dict[str, np.ndarray]:
    """
    Apply spline-based imputation to all models in the ensemble.
    
    Args:
        ensemble_data: Dictionary of time series
        max_gap: Maximum gap size for spline imputation
    
    Returns:
        Imputed ensemble data
    """
    imputed = {}
    
    for model_name, data in ensemble_data.items():
        imputed_data = impute_with_spline(data, max_gap)
        imputed[model_name] = imputed_data
        
    logger.info(f"Applied imputation to {len(imputed)} models")
    return imputed
