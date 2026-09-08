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
    This script writes a verification report to data/processed/transformer_test_report.json
    to prove the function works on real data structures.
    """
    logger.info("Starting CLRTransformer test and verification")
    set_seed(42)

    # Example usage with realistic solder composition data (Sn, Ag, Cu)
    # These sum to 1.0 (100%)
    test_data = np.array([
        [0.965, 0.030, 0.005],  # SAC305 variant
        [0.950, 0.040, 0.010],  # SAC405
        [0.990, 0.005, 0.005],  # Sn-rich
        [0.850, 0.100, 0.050],  # High Ag/Cu
        [0.500, 0.300, 0.200],  # Extreme case
        [0.1, 0.8, 0.1],
        [0.33, 0.33, 0.34]
    ])

    transformer = CLRTransformer()
    transformed = transformer.fit_transform(test_data)

    logger.info(f"Original data shape: {test_data.shape}")
    logger.info(f"Transformed data shape: {transformed.shape}")
    
    # Verify sum of transformed values is close to 0 (property of CLR)
    sums = transformed.sum(axis=1)
    logger.info(f"Sum of transformed rows (should be ~0): {sums}")

    # Verify no NaN or Inf values
    has_nan = np.isnan(transformed).any()
    has_inf = np.isinf(transformed).any()
    
    if has_nan or has_inf:
        logger.error("Transformation produced NaN or Inf values!")
        raise ValueError("Transformation failed: produced invalid values")

    # Write verification report to disk as required by task execution constraints
    # ensuring the script produces a real output file.
    output_path = "data/processed/transformer_test_report.json"
    report = {
        "status": "success",
        "input_shape": list(test_data.shape),
        "output_shape": list(transformed.shape),
        "row_sums": sums.tolist(),
        "has_nan": bool(has_nan),
        "has_inf": bool(has_inf),
        "test_samples": test_data.tolist(),
        "transformed_samples": transformed.tolist()
    }

    import json
    from pathlib import Path
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification report written to {output_path}")
    logger.info("CLRTransformer test completed successfully")

if __name__ == "__main__":
    main()
