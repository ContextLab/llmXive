import numpy as np
from typing import List, Tuple, Optional, Union
from scipy import stats

def calculate_vif(X: np.ndarray) -> List[float]:
    """
    Calculate Variance Inflation Factor for each feature.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        
    Returns:
        List of VIF values for each feature
    """
    n_features = X.shape[1]
    vif_values = []
    
    for i in range(n_features):
        # Regress feature i against all other features
        y = X[:, i]
        X_other = np.delete(X, i, axis=1)
        
        # Add constant for intercept
        X_other_with_const = np.column_stack([np.ones(X_other.shape[0]), X_other])
        
        # Fit linear regression
        try:
            coeffs, residuals, rank, s = np.linalg.lstsq(X_other_with_const, y, rcond=None)
            y_pred = X_other_with_const @ coeffs
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            vif = 1 / (1 - r_squared) if r_squared < 1 else float('inf')
        except np.linalg.LinAlgError:
            vif = float('inf')
        
        vif_values.append(vif)
    
    return vif_values

def residualize_features(X: np.ndarray, target_idx: int) -> np.ndarray:
    """
    Residualize one feature against all others to remove collinearity.
    
    Args:
        X: Feature matrix
        target_idx: Index of feature to residualize
        
    Returns:
        New feature matrix with target feature residualized
    """
    X_res = X.copy()
    y = X[:, target_idx]
    X_other = np.delete(X, target_idx, axis=1)
    
    # Add constant
    X_other_with_const = np.column_stack([np.ones(X_other.shape[0]), X_other])
    
    # Fit and predict
    coeffs, _, _, _ = np.linalg.lstsq(X_other_with_const, y, rcond=None)
    y_pred = X_other_with_const @ coeffs
    
    # Residualize
    residuals = y - y_pred
    X_res[:, target_idx] = residuals
    
    return X_res

def pca_decorrelate(X: np.ndarray, n_components: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply PCA to decorrelate features.
    
    Args:
        X: Feature matrix
        n_components: Number of components to keep (default: all)
        
    Returns:
        Tuple of (transformed features, explained variance ratio)
    """
    # Center the data
    X_centered = X - np.mean(X, axis=0)
    
    # Compute covariance matrix
    cov_matrix = np.cov(X_centered, rowvar=False)
    
    # Eigendecomposition
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    
    # Sort by eigenvalue descending
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    # Select components
    if n_components is None:
        n_components = X.shape[1]
    
    principal_components = eigenvectors[:, :n_components]
    X_transformed = X_centered @ principal_components
    
    explained_variance_ratio = eigenvalues[:n_components] / np.sum(eigenvalues)
    
    return X_transformed, explained_variance_ratio

def check_collinearity_report(X: np.ndarray, threshold: float = 5.0) -> dict:
    """
    Generate a collinearity report for the feature matrix.
    
    Args:
        X: Feature matrix
        threshold: VIF threshold for high collinearity
        
    Returns:
        Dictionary with VIF values and collinearity flags
    """
    vif_values = calculate_vif(X)
    high_vif = [i for i, v in enumerate(vif_values) if v > threshold]
    
    return {
        "vif_values": vif_values,
        "high_vif_indices": high_vif,
        "max_vif": max(vif_values),
        "mean_vif": float(np.mean(vif_values)),
        "is_collinear": len(high_vif) > 0
    }
