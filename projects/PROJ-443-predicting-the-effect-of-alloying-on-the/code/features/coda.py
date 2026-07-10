"""
Compositional Data Analysis (CoDA) utilities for High-Entropy Alloy (HEA) research.

This module provides the Isometric Log-Ratio (ILR) transformation and its inverse.
ILR is used to transform compositional data (which sums to 1) into Euclidean space
for use in linear models and other statistical techniques that assume unconstrained inputs.

References:
- Aitchison, J. (1986). The Statistical Analysis of Compositional Data.
- Egozcue, J. J., et al. (2003). Isometric logratio transformations for compositional data analysis.
"""
import numpy as np
from typing import Union, List, Optional
import pandas as pd

def ilr_transform(composition: Union[np.ndarray, pd.Series, List[float]]) -> np.ndarray:
    """
    Compute the Isometric Log-Ratio (ILR) transformation for a single composition.
    
    The ILR transformation maps a composition from the simplex (D parts) to 
    Euclidean space (D-1 dimensions) using an orthonormal basis derived from 
    a sequential binary partition (pivoting coordinates).
    
    Formula used:
    y_i = sqrt((i+1)/(i+2)) * ln( (geometric_mean(x_0...x_i)) / x_{i+1} )
    for i = 0 to D-2.
    
    Parameters
    ----------
    composition : array-like
        1D array of positive real numbers representing the composition.
        The sum of components should be 1.0 (or close to it).
        
    Returns
    -------
    np.ndarray
        1D array of D-1 real numbers representing the ILR coordinates.
        
    Raises
    ------
    ValueError
        If the composition has fewer than 2 parts or contains non-positive values.
    """
    x = np.asarray(composition, dtype=float)
    
    if x.ndim != 1:
        raise ValueError("Composition must be a 1D array.")
    
    D = len(x)
    if D < 2:
        raise ValueError("Composition must have at least 2 parts for ILR transformation.")
    
    # Ensure strictly positive values to avoid log(0)
    # If a value is 0, it's invalid for log-ratio transforms.
    if np.any(x <= 0):
        # Check for very small values that might be effectively zero
        if np.any(x <= 1e-15):
            raise ValueError("Composition contains non-positive values (<= 1e-15). ILR requires strictly positive inputs.")
        # If small but positive, proceed (log is defined)
    
    coords = np.zeros(D - 1)
    
    for i in range(D - 1):
        # i corresponds to the coordinate index (0 to D-2)
        # The basis vector involves the first i+1 components vs the (i+1)-th component.
        # k = i + 1 (number of components in the numerator group)
        k = i + 1
        
        # Geometric mean of the first k components: (prod(x_0...x_{k-1}))^(1/k)
        # log(geometric_mean) = (1/k) * sum(log(x_0...x_{k-1}))
        log_prod = np.sum(np.log(x[:k]))
        log_geom_mean = log_prod / k
        
        # Log of the denominator component
        log_denom = np.log(x[k])
        
        # Coefficient: sqrt(k / (k+1))
        coeff = np.sqrt(k / (k + 1))
        
        coords[i] = coeff * (log_geom_mean - log_denom)
        
    return coords

def ilr_inverse(ilr_coords: np.ndarray) -> np.ndarray:
    """
    Compute the inverse ILR transformation to reconstruct the original composition.
    
    This function reverses the ILR transformation, mapping D-1 Euclidean coordinates
    back to the D-part simplex.
    
    Parameters
    ----------
    ilr_coords : np.ndarray
        1D array of D-1 ILR coordinates.
        
    Returns
    -------
    np.ndarray
        1D array of D parts, summing to 1.0.
        
    Raises
    ------
    ValueError
        If the input array is empty or has invalid dimensions.
    """
    if ilr_coords.ndim != 1:
        raise ValueError("ILR coordinates must be a 1D array.")
        
    D = len(ilr_coords) + 1
    if D < 2:
        raise ValueError("ILR coordinates must have at least 1 element (D >= 2).")
    
    # Construct the basis matrix V (D x D-1) corresponding to the forward ILR.
    # The forward transform is y = V^T * ln(x).
    # The inverse is ln(x) = V * y (plus a constant for the closure, handled by normalization).
    # x = exp(V * y) / sum(exp(V * y))
    
    V = np.zeros((D, D - 1))
    
    for j in range(D - 1):
        # Column j corresponds to coordinate j
        # The basis vector v_j has:
        # - For rows 0 to j: value = 1 / sqrt((j+1)*(j+2))
        # - For row j+1: value = -sqrt((j+1)/(j+2))
        # - For rows > j+1: value = 0
        
        factor_pos = 1.0 / np.sqrt((j + 1) * (j + 2))
        factor_neg = -np.sqrt((j + 1) / (j + 2))
        
        for k in range(j + 1):
            V[k, j] = factor_pos
        V[j + 1, j] = factor_neg
        
    # Reconstruct log-composition
    log_x = V @ ilr_coords
    
    # Exponentiate and normalize to sum to 1
    x = np.exp(log_x)
    return x / np.sum(x)

def ilr_transform_dataframe(df: pd.DataFrame, composition_columns: List[str]) -> pd.DataFrame:
    """
    Apply ILR transformation to a DataFrame containing composition columns.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    composition_columns : list of str
        List of column names representing the composition parts.
        
    Returns
    -------
    pd.DataFrame
        DataFrame with new columns containing ILR coordinates.
        Original composition columns are preserved.
        New columns are named: 'ilr_0', 'ilr_1', ..., 'ilr_{D-2}'.
    """
    if not composition_columns:
        raise ValueError("composition_columns must not be empty.")
        
    D = len(composition_columns)
    if D < 2:
        raise ValueError("Need at least 2 composition columns for ILR.")
        
    result_df = df.copy()
    
    # Ensure we have positive values
    if (df[composition_columns] <= 0).any().any():
        # Check if it's just very small values or actual zeros
        # For now, we raise an error or handle it. 
        # In a real pipeline, we might have a filter step before this.
        # We'll raise a clear error.
        raise ValueError("Composition columns contain non-positive values. ILR requires strictly positive inputs.")
    
    # Apply transformation row by row (vectorization across rows is complex with variable D if D varies, 
    # but here D is fixed by the column list).
    # We can vectorize across rows for a fixed D.
    
    X = df[composition_columns].values.astype(float)
    coords = np.zeros((len(df), D - 1))
    
    for i in range(D - 1):
        k = i + 1
        # Numerator: geometric mean of first k columns
        # log_geom = (1/k) * sum(log(X[:, :k]))
        log_prod = np.sum(np.log(X[:, :k]), axis=1)
        log_geom_mean = log_prod / k
        
        # Denominator: log of (k)-th column (0-indexed, so column index k)
        log_denom = np.log(X[:, k])
        
        coeff = np.sqrt(k / (k + 1))
        coords[:, i] = coeff * (log_geom_mean - log_denom)
        
    # Add to DataFrame
    for i in range(D - 1):
        result_df[f'ilr_{i}'] = coords[:, i]
        
    return result_df

def ilr_inverse_dataframe(ilr_df: pd.DataFrame, num_original_components: int) -> pd.DataFrame:
    """
    Apply inverse ILR transformation to reconstruct composition from ILR columns.
    
    Parameters
    ----------
    ilr_df : pd.DataFrame
        DataFrame containing ILR columns (ilr_0, ilr_1, ...).
    num_original_components : int
        The number of original components (D) before transformation.
        
    Returns
    -------
    pd.DataFrame
        DataFrame with reconstructed composition columns.
    """
    if num_original_components < 2:
        raise ValueError("num_original_components must be at least 2.")
        
    D = num_original_components
    D_minus_1 = D - 1
    
    ilr_cols = [f'ilr_{i}' for i in range(D_minus_1)]
    if not all(col in ilr_df.columns for col in ilr_cols):
        raise ValueError(f"Missing ILR columns. Expected {ilr_cols}.")
        
    Y = ilr_df[ilr_cols].values.astype(float)
    
    # Construct basis matrix V
    V = np.zeros((D, D_minus_1))
    for j in range(D_minus_1):
        factor_pos = 1.0 / np.sqrt((j + 1) * (j + 2))
        factor_neg = -np.sqrt((j + 1) / (j + 2))
        for k in range(j + 1):
            V[k, j] = factor_pos
        V[j + 1, j] = factor_neg
        
    # Reconstruct
    log_x = Y @ V.T # (N, D-1) @ (D-1, D) -> (N, D)
    X = np.exp(log_x)
    X = X / X.sum(axis=1, keepdims=True)
    
    result_df = ilr_df.copy()
    # Assuming original columns are named comp_0, comp_1, ... or we just return the reconstructed matrix
    # For this utility, we return a DataFrame with the reconstructed values.
    # We'll name them 'reconstructed_comp_0', etc.
    for i in range(D):
        result_df[f'reconstructed_comp_{i}'] = X[:, i]
        
    return result_df