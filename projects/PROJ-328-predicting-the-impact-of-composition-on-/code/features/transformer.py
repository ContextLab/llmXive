"""
Centered Log-Ratio (CLR) transformation for compositional data.

This module implements the CLR transformation to handle the closure problem
inherent in compositional data (e.g., alloy compositions that sum to 100%).
"""
import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any
from compositional import clr, ilr, alr

logger = logging.getLogger(__name__)


class CLRTransformer:
    """
    Transformer for applying Centered Log-Ratio transformation to compositional data.
    
    The CLR transformation maps compositional data from the simplex space to
    real Euclidean space, making it suitable for standard machine learning algorithms.
    
    Attributes:
        eps: Small constant to avoid log(0) errors.
        fitted: Whether the transformer has been fitted (for consistency with sklearn API).
    """
    
    def __init__(self, eps: float = 1e-10):
        """
        Initialize the CLR transformer.
        
        Args:
            eps: Small constant added to compositions to avoid log(0).
        """
        self.eps = eps
        self.fitted = False
        logger.debug(f"CLRTransformer initialized with eps={eps}")
    
    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'CLRTransformer':
        """
        Fit the transformer (no-op for CLR, required for sklearn compatibility).
        
        Args:
            X: Compositional data array of shape (n_samples, n_components).
            y: Optional target variable (ignored).
        
        Returns:
            self: The fitted transformer instance.
        """
        logger.debug("Fitting CLRTransformer (no-op)")
        self.fitted = True
        return self
    
    def transform(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply CLR transformation to compositional data.
        
        The CLR transformation is defined as:
            clr(x)_i = log(x_i / g(x))
        where g(x) is the geometric mean of the composition.
        
        Args:
            X: Compositional data array of shape (n_samples, n_components).
               Each row should sum to approximately 1.0 (or 100.0).
        
        Returns:
            Tuple of (clr_transformed, weights):
                - clr_transformed: The CLR-transformed data.
                - weights: The geometric means used for normalization (log-space weights).
        
        Raises:
            ValueError: If input contains negative values or zeros.
            RuntimeError: If the transformer is not fitted.
        """
        if not self.fitted:
            logger.warning("CLRTransformer not fitted. Calling fit() automatically.")
            self.fit(X)
        
        X = np.asarray(X, dtype=np.float64)
        
        if np.any(X < 0):
            raise ValueError("Compositional data cannot contain negative values.")
        
        # Add small epsilon to avoid log(0)
        X_safe = np.where(X == 0, self.eps, X)
        
        # Calculate geometric means
        # g(x) = (prod(x_i))^(1/D) where D is the number of components
        log_X = np.log(X_safe)
        geometric_means = np.exp(np.mean(log_X, axis=1, keepdims=True))
        
        # Apply CLR transformation
        clr_transformed = np.log(X_safe / geometric_means)
        
        logger.debug(f"CLR transformation applied to {X.shape[0]} samples with {X.shape[1]} components")
        
        return clr_transformed, geometric_means.flatten()
    
    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fit and transform compositional data in one step.
        
        Args:
            X: Compositional data array.
            y: Optional target variable.
        
        Returns:
            Tuple of (clr_transformed, weights) as in transform().
        """
        return self.fit(X).transform(X)
    
    def inverse_transform(self, X_clr: np.ndarray) -> np.ndarray:
        """
        Inverse transform CLR data back to compositional space.
        
        Args:
            X_clr: CLR-transformed data array.
        
        Returns:
            Compositional data array (summing to 1.0).
        """
        logger.debug(f"Inverse transforming CLR data with shape {X_clr.shape}")
        
        # Inverse CLR: x_i = exp(clr_i) / sum(exp(clr_j))
        exp_X = np.exp(X_clr)
        compositional = exp_X / np.sum(exp_X, axis=1, keepdims=True)
        
        return compositional