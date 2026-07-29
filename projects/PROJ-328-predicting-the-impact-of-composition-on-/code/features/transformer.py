"""
Compositional Data Transformers.

Implements Centered Log-Ratio (CLR) transform to handle the closure problem
in compositional data (e.g., weight fractions summing to 1).
"""
import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any

from compositional import clr, ilr, alr
from utils.logging_config import get_logger

logger = get_logger(__name__)


class CLRTransformer:
    """
    Applies Centered Log-Ratio (CLR) transform to compositional data.

    The CLR transform maps data from the simplex to real Euclidean space.
    clr(x) = [ln(x_1/g(x)), ..., ln(x_D/g(x))]
    where g(x) is the geometric mean of the components.
    """

    def __init__(self, epsilon: float = 1e-10):
        """
        Args:
            epsilon: Small value to add to zero components to avoid log(0).
        """
        self.epsilon = epsilon
        self.is_fitted = False

    def _handle_zeros(self, data: np.ndarray) -> np.ndarray:
        """Replaces zeros with a small epsilon value."""
        return np.where(data == 0, self.epsilon, data)

    def fit(self, X: np.ndarray) -> "CLRTransformer":
        """
        Fit the transformer (no-op for CLR, but required for sklearn compatibility).
        """
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply the CLR transform.

        Args:
            X: Array of shape (n_samples, n_components) representing compositions.

        Returns:
            Tuple of (clr_transformed_data, weights)
            weights are the original composition values (used for downstream weighting).
        """
        if not self.is_fitted:
            self.fit(X)

        # Handle zeros
        X_clean = self._handle_zeros(X)

        # Compute CLR
        # The 'compositional' library expects the data to be in a specific format.
        # We assume X is a numpy array of floats.
        try:
            # clr function from compositional library
            # Returns the CLR transformed data
            clr_data = clr(X_clean)
        except Exception as e:
            logger.error(f"Error in CLR transform: {e}")
            raise

        # Return transformed data and the original weights (for descriptor weighting)
        return clr_data, X_clean

    def fit_transform(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fit and transform in one step.
        """
        return self.fit(X).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Inverse CLR transform (ilr inverse is not exactly clr inverse without normalization).
        For CLR, the inverse is the exponential followed by normalization (closure).
        """
        # exp(clr) gives the ratios relative to geometric mean
        # To get back to simplex, we need to normalize
        try:
            # compositional library might have an inverse, but standard math:
            # x = exp(clr) / sum(exp(clr))
            exp_data = np.exp(X)
            # Normalize to sum to 1 (closure)
            closure = np.sum(exp_data, axis=1, keepdims=True)
            return exp_data / closure
        except Exception as e:
            logger.error(f"Error in inverse CLR transform: {e}")
            raise
