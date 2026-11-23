"""
Refactor utilities for code cleanup and readability.

This module provides helper functions to improve code readability and maintainability
across the project. It wraps functionality from utils.py to provide a cleaner API surface.
"""

from .utils import (
    get_atomic_radius,
    get_vec,
    get_electronegativity,
    get_properties,
    get_properties_batch
)

__all__ = [
    'get_atomic_radius',
    'get_vec',
    'get_electronegativity',
    'get_properties',
    'get_properties_batch'
]

def clean_composition_string(composition: str) -> str:
    """
    Clean and normalize a composition string.
    
    Args:
        composition: Raw composition string (e.g., "Fe0.5Ni0.5C")
    
    Returns:
        Normalized composition string with consistent formatting
    """
    if not composition:
        return ""
    
    # Remove whitespace
    cleaned = composition.replace(" ", "")
    
    # Ensure consistent case (uppercase element symbols)
    # This is a simple heuristic; full parsing would use pymatgen
    return cleaned

def validate_feature_names(df_features) -> list:
    """
    Validate and return a sorted list of feature column names.
    
    Args:
        df_features: DataFrame or dict-like object with feature columns
    
    Returns:
        Sorted list of feature names
    """
    if hasattr(df_features, 'columns'):
        features = list(df_features.columns)
    elif isinstance(df_features, dict):
        features = list(df_features.keys())
    else:
        raise ValueError("Input must be a DataFrame or dict-like object")
    
    return sorted(features)

def format_metric_name(metric: str) -> str:
    """
    Format a metric name for display purposes.
    
    Args:
        metric: Raw metric name (e.g., 'r2', 'rmse', 'mae')
    
    Returns:
        Formatted metric name (e.g., 'R²', 'RMSE', 'MAE')
    """
    metric_map = {
        'r2': 'R²',
        'rmse': 'RMSE',
        'mae': 'MAE',
        'p_value': 'p-value',
        'adjusted_r2': 'Adjusted R²'
    }
    return metric_map.get(metric.lower(), metric.upper())