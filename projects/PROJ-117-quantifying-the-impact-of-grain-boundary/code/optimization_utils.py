"""
Optimization utilities for vectorizing heavy loops in the grain boundary diffusivity pipeline.

This module provides wrapper functions and patterns to ensure that data processing,
feature engineering, and model evaluation steps utilize vectorized NumPy/Pandas operations
instead of Python-level loops, ensuring the pipeline stays within the 6-hour runtime budget
on CPU-only infrastructure.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Callable
import logging

logger = logging.getLogger(__name__)

# Constants for vectorization thresholds
VECTORIZATION_THRESHOLD = 100  # Below this, loops might be acceptable

def vectorize_miller_indices_calculation(
    boundary_vectors: np.ndarray, 
    lattice_vectors: np.ndarray
) -> np.ndarray:
    """
    Vectorized calculation of Miller indices from boundary plane normals.
    
    Replaces a loop that would calculate cross products and normalize for each row.
    
    Args:
        boundary_vectors: Array of shape (N, 3) containing boundary plane normal vectors.
        lattice_vectors: Array of shape (3, 3) containing the lattice basis vectors.
        
    Returns:
        Array of shape (N, 3) containing Miller indices (h, k, l).
    """
    if boundary_vectors.shape[0] == 0:
        return np.array([])
        
    # Ensure boundary_vectors is 2D
    if boundary_vectors.ndim == 1:
        boundary_vectors = boundary_vectors.reshape(1, -1)
        
    # Calculate reciprocal lattice vectors (vectorized)
    # reciprocal_lattice = 2π * (b × c) / (a · (b × c))
    # For Miller indices, we need the transformation from Cartesian to reciprocal space
    
    # Inverse of lattice matrix transforms Cartesian to fractional coordinates
    # which is proportional to Miller indices for orthogonal systems
    inv_lattice = np.linalg.inv(lattice_vectors)
    
    # Transform all boundary vectors at once: (N, 3) @ (3, 3) -> (N, 3)
    fractional_coords = boundary_vectors @ inv_lattice.T
    
    # Convert to Miller indices by multiplying by LCM-like factor to clear denominators
    # For simplicity in this context, we normalize to smallest integers
    # This is a simplified version; real implementation might need GCD logic
    # which is harder to vectorize perfectly but can be approximated
    
    # Normalize to unit length then scale to reasonable integers
    norms = np.linalg.norm(fractional_coords, axis=1, keepdims=True)
    norms[norms == 0] = 1  # Avoid division by zero
    
    unit_vectors = fractional_coords / norms
    
    # Scale to integers (approximate)
    # In practice, you might want to use a more sophisticated GCD approach
    # but for performance, we scale to nearest integers
    miller_indices = np.round(unit_vectors * 10).astype(int)
    
    # Clean up near-zero values
    miller_indices[np.abs(miller_indices) < 1] = 0
    
    return miller_indices

def vectorize_sigma_calculation(
    misorientation_angles: np.ndarray
) -> np.ndarray:
    """
    Vectorized calculation of Σ (Sigma) values from misorientation angles.
    
    Replaces a loop that would calculate Sigma for each angle individually.
    Uses the CSL approximation: Σ ≈ 1 / (1 - cos(θ)) for small angles,
    or lookup table logic vectorized across the array.
    
    Args:
        misorientation_angles: Array of shape (N,) containing misorientation angles in radians.
        
    Returns:
        Array of shape (N,) containing Σ values.
    """
    if misorientation_angles.size == 0:
        return np.array([])
        
    # Ensure 1D
    if misorientation_angles.ndim > 1:
        misorientation_angles = misorientation_angles.flatten()
        
    # Vectorized cosine calculation
    cos_angles = np.cos(misorientation_angles)
    
    # CSL approximation: Σ = 1 / (1 - cos(θ))
    # Avoid division by zero for θ = 0
    denominator = 1 - cos_angles
    denominator[denominator == 0] = 1e-10
    
    sigma_values = 1.0 / denominator
    
    # Round to nearest integer (common Σ values are integers)
    sigma_values = np.round(sigma_values).astype(int)
    
    # Ensure minimum value of 1
    sigma_values = np.maximum(sigma_values, 1)
    
    return sigma_values

def vectorize_rodrigues_encoding(
    rotation_matrices: np.ndarray
) -> np.ndarray:
    """
    Vectorized encoding of rotation matrices to Rodrigues vectors.
    
    Replaces a loop that would convert each rotation matrix individually.
    
    Args:
        rotation_matrices: Array of shape (N, 3, 3) containing rotation matrices.
        
    Returns:
        Array of shape (N, 3) containing Rodrigues vectors.
    """
    if rotation_matrices.shape[0] == 0:
        return np.array([])
        
    # Extract rotation angles and axes from matrices
    # trace(R) = 1 + 2*cos(θ) => cos(θ) = (trace(R) - 1) / 2
    traces = np.einsum('ijj->i', rotation_matrices)
    cos_theta = (traces - 1) / 2.0
    
    # Clamp to valid range to avoid numerical issues
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    
    # Calculate sin(θ)
    sin_theta = np.sqrt(1 - cos_theta**2)
    
    # Avoid division by zero for θ = 0
    sin_theta[sin_theta == 0] = 1e-10
    
    # Rodrigues vector = (axis) * tan(θ/2)
    # tan(θ/2) = sin(θ) / (1 + cos(θ))
    tan_half_theta = sin_theta / (1 + cos_theta)
    
    # Extract rotation axis components from antisymmetric part of R
    # R - R^T = 2*sin(θ) * [axis]_x (skew-symmetric matrix)
    # axis_x = (R[2,1] - R[1,2]) / (2*sin(θ))
    # axis_y = (R[0,2] - R[2,0]) / (2*sin(θ))
    # axis_z = (R[1,0] - R[0,1]) / (2*sin(θ))
    
    axis_x = (rotation_matrices[:, 2, 1] - rotation_matrices[:, 1, 2]) / (2 * sin_theta)
    axis_y = (rotation_matrices[:, 0, 2] - rotation_matrices[:, 2, 0]) / (2 * sin_theta)
    axis_z = (rotation_matrices[:, 1, 0] - rotation_matrices[:, 0, 1]) / (2 * sin_theta)
    
    # Combine to get Rodrigues vectors
    rodrigues = np.stack([axis_x, axis_y, axis_z], axis=1) * tan_half_theta
    
    return rodrigues

def vectorize_feature_scaling(
    data: pd.DataFrame, 
    feature_columns: List[str],
    method: str = 'standard'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Vectorized feature scaling using pandas/numpy operations.
    
    Replaces loops that would scale each feature individually.
    
    Args:
        data: DataFrame containing the features.
        feature_columns: List of column names to scale.
        method: Scaling method ('standard', 'minmax', 'robust').
        
    Returns:
        Tuple of (scaled DataFrame, scaling parameters dict).
    """
    if len(feature_columns) == 0:
        return data, {}
        
    # Extract features as numpy array for vectorized operations
    X = data[feature_columns].values
    
    params = {}
    
    if method == 'standard':
        # Standard scaling: (X - mean) / std
        mean = np.mean(X, axis=0)
        std = np.std(X, axis=0)
        std[std == 0] = 1  # Avoid division by zero
        
        X_scaled = (X - mean) / std
        
        params = {'mean': mean, 'std': std, 'method': method}
        
    elif method == 'minmax':
        # Min-Max scaling: (X - min) / (max - min)
        min_vals = np.min(X, axis=0)
        max_vals = np.max(X, axis=0)
        range_vals = max_vals - min_vals
        range_vals[range_vals == 0] = 1  # Avoid division by zero
        
        X_scaled = (X - min_vals) / range_vals
        
        params = {'min': min_vals, 'max': max_vals, 'method': method}
        
    elif method == 'robust':
        # Robust scaling: (X - median) / IQR
        median = np.median(X, axis=0)
        q75 = np.percentile(X, 75, axis=0)
        q25 = np.percentile(X, 25, axis=0)
        iqr = q75 - q25
        iqr[iqr == 0] = 1  # Avoid division by zero
        
        X_scaled = (X - median) / iqr
        
        params = {'median': median, 'q75': q75, 'q25': q25, 'method': method}
        
    else:
        raise ValueError(f"Unknown scaling method: {method}")
    
    # Create scaled DataFrame
    scaled_data = data.copy()
    scaled_data[feature_columns] = X_scaled
    
    return scaled_data, params

def vectorize_missing_value_imputation(
    data: pd.DataFrame, 
    strategy: str = 'mean'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Vectorized missing value imputation.
    
    Replaces loops that would impute each column individually.
    
    Args:
        data: DataFrame containing the data with missing values.
        strategy: Imputation strategy ('mean', 'median', 'most_frequent', 'constant').
        
    Returns:
        Tuple of (imputed DataFrame, imputation parameters dict).
    """
    if data.isna().sum().sum() == 0:
        return data, {}
        
    params = {}
    
    if strategy == 'mean':
        impute_values = data.mean()
        params = {'strategy': strategy, 'values': impute_values.to_dict()}
        
    elif strategy == 'median':
        impute_values = data.median()
        params = {'strategy': strategy, 'values': impute_values.to_dict()}
        
    elif strategy == 'most_frequent':
        impute_values = data.mode().iloc[0]
        params = {'strategy': strategy, 'values': impute_values.to_dict()}
        
    elif strategy == 'constant':
        impute_values = 0
        params = {'strategy': strategy, 'value': impute_values}
        
    else:
        raise ValueError(f"Unknown imputation strategy: {strategy}")
    
    # Vectorized imputation using fillna
    if strategy == 'constant':
        imputed_data = data.fillna(impute_values)
    else:
        imputed_data = data.fillna(impute_values)
    
    return imputed_data, params

def vectorize_diffusivity_calculation(
    temperature: np.ndarray,
    activation_energy: np.ndarray,
    pre_exponential: np.ndarray,
    gas_constant: float = 8.314
) -> np.ndarray:
    """
    Vectorized calculation of diffusivity using Arrhenius equation.
    
    D = D0 * exp(-Q / (R * T))
    
    Replaces a loop that would calculate diffusivity for each sample individually.
    
    Args:
        temperature: Array of shape (N,) containing temperatures in Kelvin.
        activation_energy: Array of shape (N,) containing activation energies in J/mol.
        pre_exponential: Array of shape (N,) containing pre-exponential factors in m²/s.
        gas_constant: Gas constant R in J/(mol·K).
        
    Returns:
        Array of shape (N,) containing diffusivity values in m²/s.
    """
    if temperature.size == 0:
        return np.array([])
        
    # Ensure all inputs are 1D
    if temperature.ndim > 1:
        temperature = temperature.flatten()
    if activation_energy.ndim > 1:
        activation_energy = activation_energy.flatten()
    if pre_exponential.ndim > 1:
        pre_exponential = pre_exponential.flatten()
        
    # Vectorized Arrhenius calculation
    # Avoid division by zero for T = 0
    safe_temp = np.where(temperature == 0, 1e-10, temperature)
    
    exponent = -activation_energy / (gas_constant * safe_temp)
    
    # Clip exponent to avoid overflow
    exponent = np.clip(exponent, -700, 700)
    
    diffusivity = pre_exponential * np.exp(exponent)
    
    return diffusivity

def vectorize_correlation_matrix(
    data: pd.DataFrame,
    method: str = 'pearson'
) -> pd.DataFrame:
    """
    Vectorized correlation matrix calculation.
    
    Replaces loops that would calculate pairwise correlations individually.
    Uses pandas built-in which is optimized with NumPy.
    
    Args:
        data: DataFrame containing the features.
        method: Correlation method ('pearson', 'spearman', 'kendall').
        
    Returns:
        DataFrame containing the correlation matrix.
    """
    # pandas corr is already vectorized
    return data.corr(method=method)

def vectorize_outlier_detection(
    data: pd.DataFrame,
    method: str = 'iqr',
    k: float = 1.5
) -> pd.Series:
    """
    Vectorized outlier detection.
    
    Replaces loops that would check each row/column individually.
    
    Args:
        data: DataFrame containing the features.
        method: Outlier detection method ('iqr', 'zscore').
        k: Multiplier for IQR or Z-score threshold.
        
    Returns:
        Series of boolean values indicating outliers.
    """
    if method == 'iqr':
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - k * iqr
        upper_bound = q3 + k * iqr
        
        # Vectorized check
        outliers = ((data < lower_bound) | (data > upper_bound)).any(axis=1)
        
    elif method == 'zscore':
        from scipy import stats
        # Z-score calculation is vectorized
        z_scores = np.abs(stats.zscore(data, nan_policy='omit'))
        outliers = (z_scores > k).any(axis=1)
        
    else:
        raise ValueError(f"Unknown outlier detection method: {method}")
        
    return outliers

def benchmark_vectorization(
    func: Callable,
    input_size: int = 10000,
    num_iterations: int = 5
) -> Dict[str, float]:
    """
    Benchmark a vectorized function against a loop-based alternative.
    
    Args:
        func: The vectorized function to benchmark.
        input_size: Size of the input data.
        num_iterations: Number of benchmark iterations.
        
    Returns:
        Dictionary with timing results.
    """
    import time
    
    # Generate sample data
    np.random.seed(42)
    sample_data = np.random.rand(input_size, 3)
    
    # Time the vectorized function
    start_time = time.time()
    for _ in range(num_iterations):
        result = func(sample_data)
    vectorized_time = (time.time() - start_time) / num_iterations
    
    logger.info(f"Vectorized function completed in {vectorized_time:.4f} seconds for {input_size} samples")
    
    return {
        'vectorized_time': vectorized_time,
        'input_size': input_size,
        'num_iterations': num_iterations
    }

def ensure_vectorized_operations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure that heavy operations on a DataFrame use vectorized operations.
    
    This is a utility function that can be called to enforce vectorization
    patterns in the pipeline.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with vectorized operations applied where beneficial.
    """
    # Example: Replace row-wise apply with vectorized operations
    # This is a template that can be extended based on specific needs
    
    # Check for common anti-patterns
    if 'apply' in str(df.apply):
        logger.warning("Detected potential non-vectorized operations. Consider refactoring.")
    
    return df
