"""
CPU-Only Execution Configuration for Model Training.

This module provides configuration dictionaries that explicitly
disable GPU acceleration and enforce single-threaded CPU execution.
This is critical for running on free-tier CI/CD runners (e.g., GitHub Actions)
which often lack GPU resources or have strict memory limits.
"""
from typing import Dict, Any

def get_cpu_config(model_type: str) -> Dict[str, Any]:
    """
    Retrieve the CPU-only configuration for a specific model type.
    
    Args:
        model_type (str): Either 'xgboost' or 'linear_regression'.
    
    Returns:
        Dict[str, Any]: Configuration dictionary compatible with the respective trainer.
    
    Raises:
        ValueError: If model_type is not recognized.
    """
    if model_type == "xgboost":
        return {
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "objective": "reg:squarederror",
            "random_state": 42,
            # CPU Enforcement
            "device": "cpu",
            "n_jobs": 1,
            "tree_method": "hist",  # Efficient CPU algorithm
            "gpu_id": None,
            "enable_categorical": False
        }
    
    elif model_type == "linear_regression":
        return {
            "fit_intercept": True,
            "normalize": False,  # Deprecated in newer sklearn, using StandardScaler instead
            "copy_X": True,
            "n_jobs": 1,
            # Explicitly ensure no GPU backend is used (sklearn is CPU by default,
            # but this is for documentation and future-proofing if using other backends)
            "gpu_id": None
        }
    
    else:
        raise ValueError(f"Unknown model_type: {model_type}. "
                         f"Supported types: 'xgboost', 'linear_regression'")

def get_xgboost_params() -> Dict[str, Any]:
    """Convenience wrapper for XGBoost CPU params."""
    return get_cpu_config("xgboost")

def get_linear_params() -> Dict[str, Any]:
    """Convenience wrapper for Linear Regression CPU params."""
    return get_cpu_config("linear_regression")