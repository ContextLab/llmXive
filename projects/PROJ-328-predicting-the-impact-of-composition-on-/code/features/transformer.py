"""
Compositional data transformation utilities.

Implements the Centered Log-Ratio (CLR) transformation to handle
the closure problem in compositional data (where components sum to 1 or 100%).
"""

import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any
from compositional import clr, ilr, alr

logger = logging.getLogger(__name__)

class CLRTransformer:
    """
    Transformer for applying Centered Log-Ratio (CLR) transformation
    to compositional data.
    
    The CLR transformation maps data from the simplex to real space,
    allowing standard statistical methods to be applied.
    
    Attributes:
        elements (list): Ordered list of element names in the composition.
        has_fit (bool): Whether the transformer has been fitted.
    """
    
    def __init__(self, elements: Optional[list] = None):
        """
        Initialize the CLRTransformer.
        
        Args:
            elements: Optional list of element names. If provided, the transformer
                     will validate that input data matches this ordering.
        """
        self.elements = elements if elements else []
        self.has_fit = False
        self.logger = logging.getLogger(__name__)
    
    def fit(self, X: np.ndarray) -> 'CLRTransformer':
        """
        Fit the transformer to the data (no-op for CLR, but validates input).
        
        Args:
            X: Array of compositional data, shape (n_samples, n_components).
        
        Returns:
            self: The fitted transformer.
        
        Raises:
            ValueError: If input data contains zeros or negative values.
        """
        if X is None or X.size == 0:
            raise ValueError("Input data cannot be empty")
        
        if np.any(X <= 0):
            # CLR requires strictly positive values
            # Replace zeros with a small pseudo-count
            self.logger.warning(
                "Input contains zeros or negative values. "
                "Replacing with small pseudo-count (1e-6) for CLR transformation."
            )
            X = np.where(X <= 0, 1e-6, X)
        
        if self.elements and X.shape[1] != len(self.elements):
            raise ValueError(
                f"Expected {len(self.elements)} components, got {X.shape[1]}"
            )
        
        self.has_fit = True
        return self
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Apply CLR transformation to the data.
        
        Args:
            X: Array of compositional data, shape (n_samples, n_components).
        
        Returns:
            np.ndarray: CLR-transformed data, same shape as input.
        
        Raises:
            ValueError: If transform is called before fit.
        """
        if not self.has_fit:
            raise ValueError("Transformer must be fitted before transform")
        
        # Handle zeros/negatives again for safety
        X_clean = np.where(X <= 0, 1e-6, X)
        
        # Apply CLR transformation using compositional library
        # clr returns the centered log-ratio transformed data
        try:
            X_clr = clr(X_clean)
        except Exception as e:
            self.logger.error(f"CLR transformation failed: {e}")
            raise
        
        return X_clr
    
    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Fit and transform the data in one step.
        
        Args:
            X: Array of compositional data, shape (n_samples, n_components).
        
        Returns:
            np.ndarray: CLR-transformed data.
        """
        self.fit(X)
        return self.transform(X)
    
    def get_inverse_transform(self, X_clr: np.ndarray) -> np.ndarray:
        """
        Apply inverse CLR transformation to recover original composition.
        
        Args:
            X_clr: CLR-transformed data.
        
        Returns:
            np.ndarray: Original compositional data (normalized).
        """
        try:
            # Inverse CLR: exp(x) / sum(exp(x))
            X_inv = np.exp(X_clr)
            X_norm = X_inv / X_inv.sum(axis=1, keepdims=True)
            return X_norm
        except Exception as e:
            self.logger.error(f"Inverse CLR transformation failed: {e}")
            raise
    
    def get_weights(self) -> np.ndarray:
        """
        Get the weight coefficients for the CLR transformation.
        
        For CLR, the transformation is:
            y_i = log(x_i / g(x))
        where g(x) is the geometric mean of the composition.
        
        Returns:
            np.ndarray: Weight coefficients (1/n for each component in the denominator).
        """
        if not self.has_fit:
            raise ValueError("Transformer must be fitted first")
        
        n = len(self.elements) if self.elements else 1
        # The CLR transformation can be expressed as a linear combination
        # with weights: [1, 1, ..., 1] for numerator and [-1/n, -1/n, ...] for denominator
        # This returns the effective weights for feature engineering
        return np.ones(n) / n
    
    def get_feature_names_out(self) -> list:
        """
        Get feature names for the transformed data.
        
        Returns:
            list: List of feature names with '_clr' suffix.
        """
        if not self.elements:
            return [f"component_{i}_clr" for i in range(10)]  # Default
        return [f"{elem}_clr" for elem in self.elements]
