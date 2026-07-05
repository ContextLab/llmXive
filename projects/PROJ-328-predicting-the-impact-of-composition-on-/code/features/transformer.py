"""
Compositional Data Analysis (CoDA) transformer.
Implements the Centered Log-Ratio (CLR) transform to handle the closure problem.
"""
import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any
from compositional import clr, ilr, alr  # Using the compositional library as per requirements

logger = logging.getLogger(__name__)

class CLRTransformer:
    """
    Transformer for applying CLR transform to compositional data.
    
    The CLR transform is defined as:
    clr(x)_i = log(x_i / g(x))
    where g(x) is the geometric mean of the composition.
    
    This handles the 'closure' problem where compositions sum to 1 (or 100%),
    allowing standard statistical methods to be applied.
    """
    
    def __init__(self, epsilon: float = 1e-6):
        """
        Initialize the CLR transformer.
        
        Args:
            epsilon: Small constant to avoid log(0) for zero components.
                    Replaces zeros with epsilon before transformation.
        """
        self.epsilon = epsilon
        self._is_fitted = False
        self._feature_names = None

    def _replace_zeros(self, X: np.ndarray) -> np.ndarray:
        """Replace zeros with epsilon to avoid log(0)."""
        X_clean = X.copy()
        zero_mask = X_clean == 0
        if np.any(zero_mask):
            count = np.sum(zero_mask)
            logger.debug(f"Replacing {count} zero components with epsilon={self.epsilon}")
            X_clean[zero_mask] = self.epsilon
        return X_clean

    def fit(self, X: np.ndarray, y=None, feature_names: Optional[list] = None):
        """
        Fit the transformer (no-op for CLR, but stores feature names).
        
        Args:
            X: Composition matrix of shape (n_samples, n_components).
            y: Unused.
            feature_names: Optional list of component names (e.g., ['Sn', 'Ag', 'Cu']).
        
        Returns:
            self
        """
        if feature_names is not None:
            self._feature_names = feature_names
            logger.debug(f"Stored feature names: {self._feature_names}")
        self._is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply the CLR transform.
        
        Args:
            X: Composition matrix of shape (n_samples, n_components).
        
        Returns:
            Tuple of:
                - clr_transformed: CLR-transformed data (n_samples, n_components).
                - weights: The geometric mean weights used (n_components,) for reference.
        """
        if not self._is_fitted:
            raise RuntimeError("Transformer must be fitted before transform.")
        
        X_clean = self._replace_zeros(X)
        
        # Calculate geometric mean for each sample
        # g(x) = (product(x_i))^(1/D)
        # log(g(x)) = (1/D) * sum(log(x_i))
        log_X = np.log(X_clean)
        log_g = np.mean(log_X, axis=1, keepdims=True)
        
        # CLR: log(x_i) - log(g(x))
        clr_X = log_X - log_g
        
        # Calculate weights (geometric means) for downstream use if needed
        # weights = g(x)
        weights = np.exp(log_g)
        
        logger.debug(f"CLR transform applied: input shape {X.shape}, output shape {clr_X.shape}")
        return clr_X, weights

    def fit_transform(self, X: np.ndarray, y=None, feature_names: Optional[list] = None):
        """Fit and transform in one step."""
        self.fit(X, y, feature_names)
        return self.transform(X)

    def inverse_transform(self, X_clr: np.ndarray) -> np.ndarray:
        """
        Inverse CLR transform (reconstruct composition from CLR).
        
        Args:
            X_clr: CLR-transformed data.
        
        Returns:
            Reconstructed composition (sums to 1).
        """
        # x_i = exp(clr_i) / sum(exp(clr_j))
        exp_X = np.exp(X_clr)
        return exp_X / np.sum(exp_X, axis=1, keepdims=True)
