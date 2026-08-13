"""
CLRTransformer: Applies Centered Log-Ratio transform to compositional data.
Addresses the closure problem (sum-to-one constraint) by mapping to Euclidean space.
"""
import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any
from compositional import clr, ilr, alr
from utils.logging_config import get_logger
from seed import set_seed

logger = get_logger(__name__)

class CLRTransformer:
    """
    Transformer for applying Centered Log-Ratio (CLR) transformation to compositional data.
    """

    def __init__(self, pseudo_count: float = 1e-6):
        """
        Initialize the CLR Transformer.

        Args:
            pseudo_count: Small value added to compositions to avoid log(0).
        """
        self.pseudo_count = pseudo_count
        logger.info(f"CLRTransformer initialized with pseudo_count={pseudo_count}")

    def fit(self, X: np.ndarray) -> 'CLRTransformer':
        """
        Fit the transformer (no-op for CLR, but required for sklearn compatibility).

        Args:
            X: Compositional data array of shape (n_samples, n_components).

        Returns:
            self
        """
        # CLR transform is stateless; no fitting required
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Apply CLR transform to the data.

        Args:
            X: Compositional data array of shape (n_samples, n_components).
               Values should sum to ~1.0 (or 100.0).

        Returns:
            Transformed data array of shape (n_samples, n_components).
        """
        if X is None or X.size == 0:
            raise ValueError("Input array cannot be empty")

        # Ensure we don't have zeros which would cause log(0)
        X_safe = np.clip(X, self.pseudo_count, None)

        # Normalize to ensure sum is 1 if not already (robustness)
        sums = X_safe.sum(axis=1, keepdims=True)
        # Avoid division by zero
        sums = np.where(sums == 0, 1, sums)
        X_normalized = X_safe / sums

        # Apply CLR using the compositional library
        # clr function expects shape (n_samples, n_components)
        try:
            X_clr = clr(X_normalized)
        except Exception as e:
            logger.error(f"CLR transformation failed: {e}")
            raise

        return X_clr

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Fit and transform the data.

        Args:
            X: Compositional data array.

        Returns:
            Transformed data array.
        """
        self.fit(X)
        return self.transform(X)

def main():
    """
    Main entry point for testing the CLRTransformer.
    """
    logger.info("Starting CLRTransformer test")
    set_seed(42)

    # Example usage
    test_data = np.array([
        [0.5, 0.3, 0.2],
        [0.1, 0.8, 0.1],
        [0.33, 0.33, 0.34]
    ])

    transformer = CLRTransformer()
    transformed = transformer.fit_transform(test_data)

    logger.info(f"Original data:\n{test_data}")
    logger.info(f"Transformed data:\n{transformed}")

    # Verify sum of transformed values is close to 0 (property of CLR)
    sums = transformed.sum(axis=1)
    logger.info(f"Sum of transformed rows (should be ~0): {sums}")

    logger.info("CLRTransformer test completed successfully")

if __name__ == "__main__":
    main()
