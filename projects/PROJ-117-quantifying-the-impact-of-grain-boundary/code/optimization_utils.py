"""
Optimization utilities for vectorized operations in the grain boundary diffusivity pipeline.

This module provides vectorized implementations of common operations to ensure
the pipeline stays within the 6-hour runtime budget on CPU-only hardware.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Callable
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


def benchmark_vectorization(func: Callable) -> Callable:
    """Decorator to benchmark the execution time of a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        logger.info(f"{func.__name__} executed in {elapsed:.4f} seconds")
        return result
    return wrapper


@benchmark_vectorization
def vectorize_miller_indices_calculation(
    normal_vectors: np.ndarray,
    lattice_matrix: np.ndarray
) -> np.ndarray:
    """
    Calculate Miller indices (hkl) for a batch of normal vectors using vectorized operations.
    
    Args:
        normal_vectors: Array of shape (n, 3) containing normal vectors in Cartesian coordinates.
        lattice_matrix: 3x3 matrix representing the lattice basis vectors (rows).
        
    Returns:
        Array of shape (n, 3) containing Miller indices (h, k, l).
    """
    if normal_vectors.ndim == 1:
        normal_vectors = normal_vectors.reshape(1, -1)
    
    # Convert Cartesian normal to reciprocal lattice coordinates
    # hkl = normal * L^(-1) where L is the lattice matrix
    lattice_inv = np.linalg.inv(lattice_matrix)
    miller_indices = normal_vectors @ lattice_inv.T
    
    # Convert to smallest integer ratio
    # Find the greatest common divisor for each row
    abs_indices = np.abs(miller_indices)
    # Avoid division by zero
    abs_indices[abs_indices < 1e-10] = 1e-10
    
    # Normalize by the smallest non-zero element to get integer ratios
    min_vals = np.min(abs_indices, axis=1, keepdims=True)
    normalized = miller_indices / min_vals
    
    # Round to nearest integer
    miller_int = np.round(normalized).astype(int)
    
    # Ensure smallest integer set (divide by GCD)
    def gcd_batch(arr):
        result = arr[:, 0]
        for i in range(1, arr.shape[1]):
            result = np.gcd(result, arr[:, i])
        return result
    
    gcds = gcd_batch(np.abs(miller_int))
    gcds[gcds == 0] = 1  # Avoid division by zero
    
    return miller_int // gcds[:, np.newaxis]


@benchmark_vectorization
def vectorize_sigma_calculation(
    misorientation_angles: np.ndarray,
    crystal_system: str = "cubic"
) -> np.ndarray:
    """
    Calculate Σ value from misorientation angles using vectorized operations.
    
    Args:
        misorientation_angles: Array of shape (n,) containing misorientation angles in degrees.
        crystal_system: Crystal system (currently only "cubic" is supported).
        
    Returns:
        Array of shape (n,) containing Σ values.
    """
    if misorientation_angles.ndim == 0:
        misorientation_angles = np.array([misorientation_angles])
    
    # For cubic crystals, Σ = 1 / (1 - cos(θ/2)) for special angles
    # We use the standard CSL relationship for low-angle boundaries
    theta_rad = np.radians(misorientation_angles / 2.0)
    
    # Calculate Σ using the standard formula for cubic systems
    # Σ = 2 / (1 - cos(θ)) for special boundaries
    # This is an approximation for general boundaries
    cos_theta = np.cos(theta_rad)
    sigma_values = np.round(2.0 / (1.0 - cos_theta + 1e-10)).astype(int)
    
    # Ensure Σ is odd (characteristic of CSL boundaries)
    # If even, find nearest odd number
    sigma_values = np.where(sigma_values % 2 == 0, sigma_values + 1, sigma_values)
    
    # Ensure Σ >= 1
    sigma_values = np.maximum(sigma_values, 1)
    
    return sigma_values


@benchmark_vectorization
def vectorize_rodrigues_encoding(
    rotation_matrices: np.ndarray
) -> np.ndarray:
    """
    Encode rotation matrices as Rodrigues vectors using vectorized operations.
    
    Args:
        rotation_matrices: Array of shape (n, 3, 3) containing rotation matrices.
        
    Returns:
        Array of shape (n, 3) containing Rodrigues vectors.
    """
    if rotation_matrices.ndim == 2:
        rotation_matrices = rotation_matrices.reshape(1, 3, 3)
    
    n_matrices = rotation_matrices.shape[0]
    rodrigues_vectors = np.zeros((n_matrices, 3))
    
    # Extract rotation angle and axis from each matrix
    # cos(θ) = (trace(R) - 1) / 2
    traces = np.einsum('aii->a', rotation_matrices)
    cos_theta = (traces - 1.0) / 2.0
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    theta = np.arccos(cos_theta)
    
    # For small angles, use different formula to avoid division by zero
    small_angle_mask = theta < 1e-10
    large_angle_mask = ~small_angle_mask
    
    # Calculate rotation axis
    # R - R^T = 2*sin(θ)*K where K is the skew-symmetric matrix of the axis
    R_minus_RT = rotation_matrices - rotation_matrices.transpose(0, 2, 1)
    axis_x = R_minus_RT[:, 2, 1] / 2.0
    axis_y = R_minus_RT[:, 0, 2] / 2.0
    axis_z = R_minus_RT[:, 1, 0] / 2.0
    
    # Rodrigues vector = axis * tan(θ/2)
    tan_half_theta = np.tan(theta / 2.0)
    tan_half_theta[small_angle_mask] = theta[small_angle_mask] / 2.0  # Small angle approximation
    
    rodrigues_vectors[:, 0] = axis_x * tan_half_theta
    rodrigues_vectors[:, 1] = axis_y * tan_half_theta
    rodrigues_vectors[:, 2] = axis_z * tan_half_theta
    
    return rodrigues_vectors


@benchmark_vectorization
def vectorize_feature_scaling(
    features: np.ndarray,
    method: str = "standard"
) -> np.ndarray:
    """
    Scale features using vectorized operations.
    
    Args:
        features: Array of shape (n_samples, n_features).
        method: Scaling method ("standard" for Z-score, "minmax" for 0-1 scaling).
        
    Returns:
        Scaled features array.
    """
    if method == "standard":
        # Z-score normalization: (x - mean) / std
        mean = np.mean(features, axis=0)
        std = np.std(features, axis=0)
        std[std < 1e-10] = 1.0  # Avoid division by zero
        return (features - mean) / std
        
    elif method == "minmax":
        # Min-max scaling: (x - min) / (max - min)
        min_vals = np.min(features, axis=0)
        max_vals = np.max(features, axis=0)
        range_vals = max_vals - min_vals
        range_vals[range_vals < 1e-10] = 1.0  # Avoid division by zero
        return (features - min_vals) / range_vals
        
    else:
        raise ValueError(f"Unknown scaling method: {method}")


@benchmark_vectorization
def vectorize_missing_value_imputation(
    data: pd.DataFrame,
    strategy: str = "mean"
) -> pd.DataFrame:
    """
    Impute missing values using vectorized operations.
    
    Args:
        data: DataFrame with missing values.
        strategy: Imputation strategy ("mean", "median", "most_frequent", or a scalar).
        
    Returns:
        DataFrame with imputed values.
    """
    if isinstance(strategy, (int, float)):
        # Fill with constant value
        return data.fillna(strategy)
    
    elif strategy == "mean":
        means = data.mean(skipna=True)
        return data.fillna(means)
        
    elif strategy == "median":
        medians = data.median(skipna=True)
        return data.fillna(medians)
        
    elif strategy == "most_frequent":
        # For numerical data, this is similar to mode
        modes = data.mode().iloc[0]
        return data.fillna(modes)
        
    else:
        raise ValueError(f"Unknown imputation strategy: {strategy}")


@benchmark_vectorization
def vectorize_diffusivity_calculation(
    temperature: np.ndarray,
    activation_energy: np.ndarray,
    pre_exponential: np.ndarray
) -> np.ndarray:
    """
    Calculate diffusivity using Arrhenius equation with vectorized operations.
    
    D = D0 * exp(-Q / (R * T))
    
    Args:
        temperature: Array of shape (n,) containing temperatures in Kelvin.
        activation_energy: Array of shape (n,) containing activation energies in J/mol.
        pre_exponential: Array of shape (n,) containing pre-exponential factors in m²/s.
        
    Returns:
        Array of shape (n,) containing diffusivity values in m²/s.
    """
    R = 8.314  # Gas constant in J/(mol·K)
    return pre_exponential * np.exp(-activation_energy / (R * temperature))


@benchmark_vectorization
def vectorize_correlation_matrix(
    data: np.ndarray,
    method: str = "pearson"
) -> np.ndarray:
    """
    Calculate correlation matrix using vectorized operations.
    
    Args:
        data: Array of shape (n_samples, n_features).
        method: Correlation method ("pearson", "spearman", "kendall").
        
    Returns:
        Correlation matrix of shape (n_features, n_features).
    """
    if method == "pearson":
        # Center the data
        data_centered = data - np.mean(data, axis=0)
        # Calculate covariance
        n_samples = data.shape[0]
        cov = (data_centered.T @ data_centered) / (n_samples - 1)
        # Calculate standard deviations
        std = np.std(data, axis=0, ddof=1)
        std[std < 1e-10] = 1.0
        # Calculate correlation
        std_outer = np.outer(std, std)
        corr = cov / std_outer
        return corr
        
    elif method == "spearman":
        # Convert to ranks
        ranks = np.argsort(np.argsort(data, axis=0), axis=0) + 1
        return vectorize_correlation_matrix(ranks, method="pearson")
        
    else:
        raise ValueError(f"Unknown correlation method: {method}")


@benchmark_vectorization
def vectorize_outlier_detection(
    data: np.ndarray,
    method: str = "iqr",
    k: float = 1.5
) -> np.ndarray:
    """
    Detect outliers using vectorized operations.
    
    Args:
        data: Array of shape (n_samples, n_features).
        method: Outlier detection method ("iqr", "zscore").
        k: Threshold parameter (IQR multiplier or Z-score threshold).
        
    Returns:
        Boolean array of shape (n_samples,) indicating outliers.
    """
    if method == "iqr":
        q1 = np.percentile(data, 25, axis=0)
        q3 = np.percentile(data, 75, axis=0)
        iqr = q3 - q1
        lower_bound = q1 - k * iqr
        upper_bound = q3 + k * iqr
        
        # Outlier if any feature is outside bounds
        outlier_mask = np.any((data < lower_bound) | (data > upper_bound), axis=1)
        return outlier_mask
        
    elif method == "zscore":
        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        std[std < 1e-10] = 1.0
        z_scores = np.abs((data - mean) / std)
        outlier_mask = np.any(z_scores > k, axis=1)
        return outlier_mask
        
    else:
        raise ValueError(f"Unknown outlier detection method: {method}")


def ensure_vectorized_operations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure all numerical operations on the DataFrame use vectorized methods.
    
    This function applies vectorized imputation and scaling to numerical columns
    to optimize performance for large datasets.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with optimized numerical operations.
    """
    logger.info("Ensuring vectorized operations for performance optimization")
    
    # Identify numerical columns
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numerical_cols) == 0:
        logger.warning("No numerical columns found for vectorization")
        return df
    
    # Apply vectorized imputation
    df[numerical_cols] = vectorize_missing_value_imputation(df[numerical_cols], strategy="mean")
    
    # Apply vectorized scaling
    df[numerical_cols] = vectorize_feature_scaling(df[numerical_cols].values, method="standard")
    
    logger.info(f"Vectorized operations applied to {len(numerical_cols)} columns")
    return df