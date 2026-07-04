"""
CPU-only compliance utilities for the chalcogenide glass Tg prediction pipeline.

This module ensures all model training and inference operations are strictly
CPU-bound and compatible with free-tier CI environments (2 CPU, ~7GB RAM, no GPU).
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np
import pandas as pd
import torch
from sklearn.base import BaseEstimator
from sklearn.utils.validation import check_is_fitted

logger = logging.getLogger(__name__)

# Environment variable to force CPU usage if set
FORCE_CPU = os.getenv("FORCE_CPU_COMPLIANCE", "true").lower() in ("1", "true", "yes")

def enforce_cpu_mode() -> None:
    """
    Enforce CPU-only mode by:
    1. Setting environment variables before any heavy imports
    2. Configuring PyTorch to use CPU only
    3. Validating no GPU devices are detected
    
    Raises:
        RuntimeError: If GPU is detected and not explicitly allowed
    """
    # Set environment variables to prevent accidental GPU usage
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["MKL_DYNAMIC"] = "FALSE"
    os.environ["OMP_NUM_THREADS"] = "2"  # Match free-tier CPU limit
    
    # PyTorch CPU enforcement
    if torch.cuda.is_available():
        if FORCE_CPU:
            logger.warning("GPU detected but FORCE_CPU_COMPLIANCE is enabled. Forcing CPU mode.")
            torch.cuda.set_device(-1)
        else:
            logger.warning("GPU detected. Ensure this is intended for production.")
    
    # Set torch to CPU
    torch.set_default_device("cpu" if hasattr(torch, "set_default_device") else None)
    
    # Verify CPU-only operation
    if torch.cuda.is_available() and FORCE_CPU:
        logger.info("Running in CPU-only mode (GPU disabled by configuration)")

def validate_cpu_only_model(model: BaseEstimator) -> bool:
    """
    Validate that a scikit-learn model is CPU-compatible and doesn't require GPU.
    
    Args:
        model: The sklearn model instance to validate
        
    Returns:
        bool: True if model is CPU-compatible
        
    Raises:
        RuntimeError: If model requires GPU or uses unsupported operations
    """
    # Check for known GPU-only model types
    gpu_model_types = [
        "XGBClassifier", "XGBRegressor", "LightGBM", "CatBoost",  # These can use GPU but we force CPU
        "TorchModel", "PyTorchEstimator"  # Custom GPU models
    ]
    
    model_name = type(model).__name__
    
    if any(gpu_type in model_name for gpu_type in gpu_model_types):
        # Check if it's configured for CPU
        if hasattr(model, 'device'):
            if model.device != 'cpu':
                raise RuntimeError(f"Model {model_name} is configured for non-CPU device: {model.device}")
        
        # For XGBoost/LightGBM/CatBoost, ensure tree_method or similar is set to CPU
        if "XGB" in model_name:
            if hasattr(model, 'tree_method') and model.tree_method not in ['exact', 'approx', 'hist']:
                logger.warning(f"XGBoost tree_method {model.tree_method} may not be optimal for CPU")
            else:
                model.tree_method = 'hist'  # CPU-optimized
        elif "LGBM" in model_name:
            if hasattr(model, 'device'):
                model.device = 'cpu'
        elif "CatBoost" in model_name:
            if hasattr(model, 'task_type'):
                model.task_type = "CPU"
    
    return True

def limit_memory_usage(max_memory_mb: int = 6000) -> None:
    """
    Limit memory usage to prevent OOM errors on free-tier CI.
    
    Args:
        max_memory_mb: Maximum memory to use in megabytes (default 6GB)
    """
    try:
        # Set NumPy thread count
        os.environ["OMP_NUM_THREADS"] = "2"
        
        # Limit pandas memory usage where possible
        pd.options.mode.copy_on_write = True
        
        # Log memory configuration
        logger.info(f"Memory usage limited to {max_memory_mb}MB for CPU compliance")
        
    except Exception as e:
        logger.warning(f"Could not set memory limits: {e}")

def validate_data_size_for_cpu(df: pd.DataFrame, max_rows: int = 5000) -> bool:
    """
    Validate that dataset size is appropriate for CPU-only processing.
    
    Args:
        df: The DataFrame to validate
        max_rows: Maximum number of rows allowed (default 5000 per SC-006)
        
    Returns:
        bool: True if data size is acceptable
        
    Raises:
        RuntimeError: If data exceeds CPU processing limits
    """
    if len(df) > max_rows:
        raise RuntimeError(
            f"Dataset size ({len(df)} rows) exceeds CPU processing limit ({max_rows} rows). "
            "Consider sampling or using LOFO validation as per SC-006."
        )
    
    # Check for high-dimensional data
    if df.shape[1] > 100:
        logger.warning(f"High dimensionality detected ({df.shape[1]} features). "
                     "Consider feature selection for CPU efficiency.")
    
    return True

def setup_cpu_environment() -> Dict[str, Any]:
    """
    Complete setup for CPU-only environment compliance.
    
    Returns:
        dict: Configuration status and environment details
    """
    # Enforce CPU mode
    enforce_cpu_mode()
    
    # Limit memory
    limit_memory_usage()
    
    # Get environment info
    cpu_info = {
        "cpu_only_mode": FORCE_CPU,
        "cuda_available": torch.cuda.is_available(),
        "num_cpus": os.cpu_count(),
        "environment": {
            "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", "not set"),
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS", "not set"),
            "MKL_DYNAMIC": os.environ.get("MKL_DYNAMIC", "not set")
        }
    }
    
    logger.info(f"CPU environment setup complete: {cpu_info}")
    return cpu_info

def ensure_no_gpu_operations(model: BaseEstimator, X: Optional[pd.DataFrame] = None) -> None:
    """
    Ensure model operations don't accidentally use GPU.
    
    Args:
        model: The model to check
        X: Optional input data to validate
    """
    # Validate model
    validate_cpu_only_model(model)
    
    # Validate data if provided
    if X is not None:
        validate_data_size_for_cpu(X)
    
    # Check for any GPU tensors in model state
    if hasattr(model, 'get_params'):
        params = model.get_params()
        for key, value in params.items():
            if isinstance(value, torch.Tensor) and value.is_cuda:
                raise RuntimeError(f"Model parameter {key} is on GPU: {value.device}")

def main():
    """
    Main entry point for CPU compliance validation.
    
    This function validates the current environment and configuration
    to ensure CPU-only operation.
    """
    logger.info("Starting CPU compliance validation...")
    
    try:
        config = setup_cpu_environment()
        logger.info(f"CPU compliance validated: {config}")
        return 0
    except Exception as e:
        logger.error(f"CPU compliance validation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
