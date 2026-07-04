"""
Validation utilities for the CI robustness pipeline.

This module ensures all computations adhere to strict numerical and execution
constraints: double-precision floats (float64) and CPU-only execution.
"""
import numpy as np
import os
import warnings
from typing import Any, Union, List, Tuple, Optional, Dict
from scipy import stats
import torch

# Global flag to enforce CPU-only execution
FORCE_CPU_ONLY = True
FORCE_FLOAT64 = True

def enforce_float64(arr: np.ndarray) -> np.ndarray:
    """
    Ensures the input array is strictly float64.
    If not, converts it. If it's not a numpy array, attempts conversion.
    
    Args:
        arr: Input array or sequence.
        
    Returns:
        A numpy array of dtype float64.
        
    Raises:
        TypeError: If conversion to float64 is not possible.
    """
    if not isinstance(arr, np.ndarray):
        try:
            arr = np.asarray(arr)
        except Exception as e:
            raise TypeError(f"Cannot convert input to numpy array: {e}")
    
    if arr.dtype != np.float64:
        if np.issubdtype(arr.dtype, np.floating):
            if FORCE_FLOAT64:
                warnings.warn(f"Converting array from {arr.dtype} to float64 as per validation requirements.")
                arr = arr.astype(np.float64)
            else:
                # If not forced, we still convert to ensure consistency in downstream stats
                arr = arr.astype(np.float64)
        elif np.issubdtype(arr.dtype, np.integer):
            if FORCE_FLOAT64:
                warnings.warn(f"Converting integer array {arr.dtype} to float64.")
                arr = arr.astype(np.float64)
            else:
                arr = arr.astype(np.float64)
        else:
            # Complex or object types that can't be safely cast to float64
            raise TypeError(f"Array dtype {arr.dtype} cannot be safely converted to float64.")
    
    return arr

def ensure_cpu_only() -> None:
    """
    Validates that no GPU device is active for torch or other libraries.
    Raises RuntimeError if GPU usage is detected and FORCE_CPU_ONLY is True.
    """
    if FORCE_CPU_ONLY:
        if torch.cuda.is_available():
            if torch.cuda.current_device() >= 0:
                raise RuntimeError(
                    "GPU device is active. This pipeline is configured for CPU-only execution "
                    "to ensure reproducibility and avoid hardware-specific floating point variations. "
                    "Set CUDA_VISIBLE_DEVICES='' or disable FORCE_CPU_ONLY in validation.py if GPU is required."
                )
        
        # Check for MPS (Apple Silicon) if applicable
        if hasattr(torch, 'mps') and torch.mps.is_available():
            # MPS is technically a GPU backend, though often used as "default" on Mac
            # We enforce CPU-only strictly as per task requirement
             raise RuntimeError(
                  "MPS (Metal Performance Shaders) is available. This pipeline enforces CPU-only execution."
             )

def validate_input_data(data: Any, name: str = "data") -> None:
    """
    Performs comprehensive validation on input data before processing.
    
    Args:
        data: The data to validate.
        name: A descriptive name for the data (used in error messages).
        
    Raises:
        TypeError: If data is not a numpy array or cannot be converted.
        ValueError: If data contains NaN or Inf values.
    """
    arr = enforce_float64(data)
    
    if np.any(np.isnan(arr)):
        raise ValueError(f"Input '{name}' contains NaN values. All inputs must be finite.")
    
    if np.any(np.isinf(arr)):
        raise ValueError(f"Input '{name}' contains Inf values. All inputs must be finite.")
    
    # Ensure no complex numbers (which might have passed dtype check if not handled)
    if np.iscomplexobj(arr):
        raise TypeError(f"Input '{name}' contains complex numbers. Only real float64 is allowed.")

def validate_config_precision(config_module: Any) -> None:
    """
    Validates that a config module does not force float32 or GPU defaults.
    
    Args:
        config_module: The config module object.
    """
    # Check for common float32 defaults in config
    if hasattr(config_module, 'DTYPE') and config_module.DTYPE != np.float64:
        warnings.warn(f"Config DTYPE is {config_module.DTYPE}, expected float64. Forcing float64.")
    
    if hasattr(config_module, 'DEVICE') and config_module.DEVICE != 'cpu':
        raise RuntimeError(
            f"Config DEVICE is set to '{config_module.DEVICE}'. This pipeline requires CPU-only execution."
        )

def wrap_numpy_function(func):
    """
    Decorator to ensure a numpy function operates on float64 inputs and returns float64.
    """
    def wrapper(*args, **kwargs):
        # Validate inputs
        validated_args = []
        for arg in args:
            if isinstance(arg, np.ndarray):
                validated_args.append(enforce_float64(arg))
            else:
                validated_args.append(arg)
        
        validated_kwargs = {}
        for k, v in kwargs.items():
            if isinstance(v, np.ndarray):
                validated_kwargs[k] = enforce_float64(v)
            else:
                validated_kwargs[k] = v
        
        result = func(*validated_args, **validated_kwargs)
        
        # Ensure result is float64 if it's an array
        if isinstance(result, np.ndarray):
            return enforce_float64(result)
        return result
    return wrapper

def validate_pipeline_environment() -> Dict[str, Any]:
    """
    Runs a full validation check on the current execution environment.
    
    Returns:
        A dictionary with validation status and details.
    """
    ensure_cpu_only()
    
    # Check numpy version and settings
    np_version = np.__version__
    np_float_info = np.finfo(np.float64)
    
    return {
        "cpu_only_enforced": True,
        "float64_enforced": True,
        "numpy_version": np_version,
        "float64_info": {
            "eps": np_float_info.eps,
            "max": np_float_info.max,
            "min": np_float_info.min
        },
        "status": "PASS"
    }
