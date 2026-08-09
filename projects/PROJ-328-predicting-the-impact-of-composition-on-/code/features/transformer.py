"""
Compositional Data Transformer Module.

Implements the Centered Log-Ratio (CLR) transformation to handle the
compositional nature of solder alloy data (sum-to-one constraint).
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
    Transformer for applying Centered Log-Ratio (CLR) transformation.
    """

    def __init__(self, pseudo_count: float = 1e-6):
        """
        Initialize the CLR Transformer.

        Args:
            pseudo_count: Small value added to avoid log(0). Defaults to 1e-6.
        """
        self.pseudo_count = pseudo_count
        self.logger = get_logger(__name__)

    def transform(self, data: np.ndarray) -> np.ndarray:
        """
        Apply CLR transformation to the input data.

        The CLR transformation is defined as:
            clr(x)_i = ln(x_i / g(x))
        where g(x) is the geometric mean of the composition x.

        Args:
            data: Input array of shape (n_samples, n_components).
                  Values must be strictly positive.

        Returns:
            CLR-transformed array of the same shape.

        Raises:
            ValueError: If data contains non-positive values that cannot be handled.
        """
        if data is None or data.size == 0:
            raise ValueError("Input data cannot be empty or None.")

        # Ensure input is a float array
        data = np.asarray(data, dtype=np.float64)

        # Handle non-positive values by adding pseudo-count
        # The compositional library's clr function typically expects positive values.
        # We add a small pseudo-count to zero or negative values to allow log computation.
        if np.any(data <= 0):
            original_min = np.min(data[data <= 0])
            data = data + self.pseudo_count
            self.logger.warning(
                "Non-positive values detected in composition (min: %s). "
                "Added pseudo-count: %s to shift values.",
                original_min, self.pseudo_count
            )

        # Apply CLR transform using the compositional library
        # clr(x) = ln(x / g(x)) where g(x) is the geometric mean
        # The library expects the input to be strictly positive.
        try:
            transformed = clr(data)
        except Exception as e:
            self.logger.error("CLR transformation failed: %s", str(e))
            raise

        return transformed

    def fit_transform(self, data: np.ndarray) -> np.ndarray:
        """
        Fit and transform the data (identity for CLR, but kept for API consistency).

        Args:
            data: Input array.

        Returns:
            Transformed array.
        """
        return self.transform(data)


def main():
    """
    Main entry point for testing the transformer.
    """
    logger.info("Running CLR Transformer self-test...")
    set_seed(42)

    # Create sample compositional data (sums to 1)
    sample_data = np.array([
        [0.5, 0.3, 0.2],
        [0.4, 0.4, 0.2],
        [0.6, 0.2, 0.2]
    ])

    transformer = CLRTransformer()
    result = transformer.transform(sample_data)

    logger.info("Input data:\n%s", sample_data)
    logger.info("CLR Transformed data:\n%s", result)

    # Verify sum of CLR components is approx 0 (property of CLR)
    row_sums = np.sum(result, axis=1)
    logger.info("Row sums of CLR data (should be ~0): %s", row_sums)

    logger.info("CLR Transformer test completed successfully.")


if __name__ == "__main__":
    main()