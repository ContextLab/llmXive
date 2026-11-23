import numpy as np
import os
import warnings
from typing import Any, Union, List, Tuple, Optional, Dict
from scipy import stats
import torch


def enforce_float64(data: Union[np.ndarray, List, float, int, 'pd.DataFrame']) -> np.ndarray:
    """
    Enforce double-precision (float64) arithmetic for all numerical computations.

    This function ensures that all input data is converted to float64 dtype,
    which is critical for numerical stability in statistical computations,
    especially when dealing with confidence intervals and DP noise.

    Args:
        data: Input data that can be an array, list, scalar, or DataFrame

    Returns:
        numpy.ndarray: Data converted to float64 dtype

    Raises:
        TypeError: If data cannot be converted to float64
    """
    # Handle pandas DataFrame/Series if available
    try:
        import pandas as pd
        if isinstance(data, (pd.DataFrame, pd.Series)):
            data = data.values
    except ImportError:
        pass

    # Convert to numpy array if not already
    if not isinstance(data, np.ndarray):
        data = np.array(data)

    # Ensure float64 dtype
    if data.dtype != np.float64:
        data = data.astype(np.float64)

    return data


def ensure_cpu_only() -> bool:
    """
    Ensure all computations are restricted to CPU-only execution.

    This function checks that no GPU acceleration is being used, which is
    critical for:
    1. Reproducibility across different hardware configurations
    2. Avoiding non-deterministic GPU operations that can affect DP noise
    3. Ensuring consistent behavior in CI/CD environments

    Returns:
        bool: True if CPU-only execution is enforced

    Raises:
        EnvironmentError: If GPU is detected or CUDA is available
    """
    # Check if CUDA is available and raise error if so
    if torch.cuda.is_available():
        raise EnvironmentError(
            "GPU execution detected. All computations must be CPU-only for "
            "reproducibility and DP noise consistency. "
            "Please set CUDA_VISIBLE_DEVICES='' or use CPU-only PyTorch."
        )

    # Check if MPS (Apple Silicon) is available
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        raise EnvironmentError(
            "MPS (Metal Performance Shaders) detected. All computations must be "
            "CPU-only for reproducibility and DP noise consistency. "
            "Please set PYTORCH_ENABLE_MPS_FALLBACK=0 or use CPU-only PyTorch."
        )

    # Verify no GPU devices are visible
    if torch.cuda.device_count() > 0:
        raise EnvironmentError(
            f"Detected {torch.cuda.device_count()} CUDA devices. "
            "GPU execution is not permitted. "
            "Set CUDA_VISIBLE_DEVICES='' to enforce CPU-only execution."
        )

    return True


def validate_input_data(data: Union[np.ndarray, List], 
                      min_size: int = 1,
                      allow_nan: bool = False,
                      allow_inf: bool = False) -> bool:
    """
    Validate input data for statistical computations.

    This function performs comprehensive validation to ensure data quality
    before statistical operations, preventing silent failures in CI calculations.

    Args:
        data: Input data to validate
        min_size: Minimum required array size (default: 1)
        allow_nan: Whether NaN values are permitted (default: False)
        allow_inf: Whether infinite values are permitted (default: False)

    Returns:
        bool: True if validation passes

    Raises:
        ValueError: If validation fails
        TypeError: If input is not numeric
    """
    # Convert to float64 array
    data = enforce_float64(data)

    # Check minimum size
    if len(data) < min_size:
        raise ValueError(f"Input data has {len(data)} elements, "
                       f"but minimum required size is {min_size}")

    # Check for NaN values
    if not allow_nan and np.any(np.isnan(data)):
        raise ValueError("Input data contains NaN values. "
                       "NaN values are not permitted in statistical computations.")

    # Check for infinite values
    if not allow_inf and np.any(np.isinf(data)):
        raise ValueError("Input data contains infinite values. "
                       "Infinite values are not permitted in statistical computations.")

    # Check for empty arrays after filtering
    if np.all(np.isnan(data)) or np.all(np.isinf(data)):
        raise ValueError("Input data contains only NaN or infinite values.")

    return True


def validate_config_precision(config: Any) -> bool:
    """
    Validate that configuration uses appropriate precision settings.

    This function ensures that all numerical parameters in the configuration
    are set to appropriate precision levels for statistical computations.

    Args:
        config: Configuration object or dictionary

    Returns:
        bool: True if validation passes

    Raises:
        ValueError: If precision settings are inadequate
    """
    if isinstance(config, dict):
        # Check for float64-related settings
        for key, value in config.items():
            if 'precision' in key.lower() or 'float' in key.lower():
                if isinstance(value, (float, np.floating)):
                    if np.dtype(type(value)) != np.float64:
                        raise ValueError(
                            f"Configuration parameter '{key}' should use float64 "
                            f"precision, but has dtype {np.dtype(type(value))}"
                        )
    elif hasattr(config, '__dict__'):
        # Check object attributes
        for attr in dir(config):
            if not attr.startswith('_'):
                value = getattr(config, attr)
                if isinstance(value, (float, np.floating)):
                    if np.dtype(type(value)) != np.float64:
                        raise ValueError(
                            f"Configuration attribute '{attr}' should use float64 "
                            f"precision, but has dtype {np.dtype(type(value))}"
                        )

    return True


def wrap_numpy_function(func):
    """
    Decorator to wrap numpy functions with input validation and float64 enforcement.

    This decorator ensures that all numpy functions used in statistical computations
    automatically enforce double-precision arithmetic and validate inputs.

    Args:
        func: Numpy function to wrap

    Returns:
        Wrapped function with validation
    """
    def wrapper(*args, **kwargs):
        # Convert all array-like arguments to float64
        new_args = []
        for arg in args:
            if isinstance(arg, (np.ndarray, list, tuple)):
                new_args.append(enforce_float64(arg))
            else:
                new_args.append(arg)

        # Convert all array-like keyword arguments to float64
        new_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, (np.ndarray, list, tuple)):
                new_kwargs[key] = enforce_float64(value)
            else:
                new_kwargs[key] = value

        # Validate inputs
        for arg in new_args:
            if isinstance(arg, np.ndarray):
                validate_input_data(arg)

        for value in new_kwargs.values():
            if isinstance(value, np.ndarray):
                validate_input_data(value)

        # Execute the function
        result = func(*new_args, **new_kwargs)

        # Ensure result is float64 if it's an array
        if isinstance(result, np.ndarray):
            result = enforce_float64(result)

        return result

    return wrapper


def validate_pipeline_environment() -> bool:
    """
    Comprehensive validation of the entire pipeline environment.

    This function performs a complete check of:
    1. CPU-only execution enforcement
    2. Float64 precision requirements
    3. Available libraries and their versions
    4. Environment variables that might affect computations

    Returns:
        bool: True if all validations pass

    Raises:
        EnvironmentError: If environment validation fails
        ValueError: If configuration validation fails
    """
    # Ensure CPU-only execution
    ensure_cpu_only()

    # Validate configuration precision
    try:
        import config
        validate_config_precision(config)
    except ImportError:
        # If config module doesn't exist, skip this check
        pass

    # Check critical environment variables
    cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', '')
    if cuda_visible:
        warnings.warn(
            "CUDA_VISIBLE_DEVICES is set. This may affect reproducibility. "
            "Consider unsetting it for CPU-only execution."
        )

    # Verify critical libraries are available
    required_libs = ['numpy', 'scipy', 'pandas']
    for lib in required_libs:
        try:
            __import__(lib)
        except ImportError:
            raise EnvironmentError(
                f"Required library '{lib}' is not installed. "
                "Please install it via pip."
            )

    # Verify numpy version supports float64 operations
    if not hasattr(np, 'float64'):
        raise EnvironmentError(
            "NumPy version does not support float64 operations. "
            "Please upgrade NumPy."
        )

    return True
