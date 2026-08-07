"""
Centered Log-Ratio (CLR) transformation for compositional data.

Handles the closure problem in compositional data by transforming
data into the real space using log-ratios.
"""
import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any
from compositional import clr, ilr, alr
from utils.logging_config import get_logger

logger = get_logger(__name__)


class CLRTransformer:
    """
    Transformer for applying Centered Log-Ratio (CLR) transformation to
    compositional data.

    The CLR transformation maps compositional data from the simplex space
    to real space, allowing standard statistical methods to be applied.

    Formula: clr(x)_i = log(x_i / g(x))
    where g(x) is the geometric mean of the composition.
    """

    def __init__(self, pseudocount: float = 1e-6):
        """
        Initialize the CLR transformer.

        Args:
            pseudocount: Small value added to compositions to handle zeros.
                        Default is 1e-6.
        """
        self.pseudocount = pseudocount
        self._is_fitted = False
        logger.debug(f"CLRTransformer initialized with pseudocount={pseudocount}")

    def fit(self, X: np.ndarray) -> "CLRTransformer":
        """
        Fit the transformer (no-op for CLR, but required for sklearn compatibility).

        Args:
            X: Compositional data array of shape (n_samples, n_components)

        Returns:
            self
        """
        logger.debug("Fitting CLRTransformer (no parameters to learn)")
        self._is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Apply CLR transformation to the input data.

        Args:
            X: Compositional data array of shape (n_samples, n_components)

        Returns:
            Transformed data array of shape (n_samples, n_components)

        Raises:
            ValueError: If input contains negative values or zeros (after pseudocount)
        """
        if not self._is_fitted:
            logger.warning("CLRTransformer not fitted. Calling fit() automatically.")
            self.fit(X)

        # Handle zeros by adding pseudocount
        X_adjusted = X + self.pseudocount

        # Ensure rows sum to 1 (closure)
        row_sums = X_adjusted.sum(axis=1, keepdims=True)
        X_closed = X_adjusted / row_sums

        # Apply CLR transformation
        try:
            # compositional.clr expects input in [0, 1] and returns CLR-transformed values
            result = clr(X_closed)
        except Exception as e:
            logger.error(f"CLR transformation failed: {e}")
            raise

        logger.debug(f"CLR transformation completed. Output shape: {result.shape}")
        return result

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Fit and transform in one step.

        Args:
            X: Compositional data array

        Returns:
            Transformed data array
        """
        return self.fit(X).transform(X)

    def inverse_transform(self, X_cl: np.ndarray) -> np.ndarray:
        """
        Inverse CLR transformation to recover original composition.

        Args:
            X_cl: CLR-transformed data array

        Returns:
            Reconstructed composition array (closed to sum to 1)
        """
        if not self._is_fitted:
            raise ValueError("CLRTransformer not fitted")

        try:
            # compositional library doesn't have a direct inverse_clr,
            # so we implement it manually: exp(x) / sum(exp(x))
            exp_x = np.exp(X_cl)
            row_sums = exp_x.sum(axis=1, keepdims=True)
            result = exp_x / row_sums
        except Exception as e:
            logger.error(f"Inverse CLR transformation failed: {e}")
            raise

        logger.debug(f"Inverse CLR transformation completed. Output shape: {result.shape}")
        return result

def main():
    """
    Main function for testing the CLR transformer.
    """
    from seed import init_reproducibility
    init_reproducibility()

    # Example usage
    logger.info("Testing CLRTransformer")

    # Sample compositional data (must sum to 1)
    sample_data = np.array([
        [0.5, 0.3, 0.2],
        [0.6, 0.3, 0.1],
        [0.4, 0.4, 0.2],
    ])

    transformer = CLRTransformer()
    transformed = transformer.fit_transform(sample_data)

    logger.info(f"Original data:\n{sample_data}")
    logger.info(f"Transformed data:\n{transformed}")

    # Verify inverse transformation
    reconstructed = transformer.inverse_transform(transformed)
    logger.info(f"Reconstructed data:\n{reconstructed}")

    # Check reconstruction error
    error = np.abs(sample_data - reconstructed).max()
    logger.info(f"Max reconstruction error: {error}")

    if error < 1e-5:
        logger.info("CLR transformation test PASSED")
    else:
        logger.warning("CLR transformation test FAILED - reconstruction error too high")

if __name__ == "__main__":
    main()
