"""
CLR (Centered Log-Ratio) transformation for compositional data.

Handles the closure problem in compositional data analysis by applying
log-ratio transformations.
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
    Centered Log-Ratio transformer for compositional data.
    
    The CLR transformation is defined as:
    clr(x)_i = log(x_i / g(x))
    where g(x) is the geometric mean of the composition.
    
    This handles the closure problem where compositional data sums to 1 (or 100%).
    """
    
    def __init__(self, epsilon: float = 1e-10):
        """
        Initialize CLR transformer.
        
        Args:
            epsilon: Small constant to avoid log(0) for zero components.
        """
        self.epsilon = epsilon
        self._is_fitted = False
        logger.info("CLRTransformer initialized with epsilon=%s", epsilon)
    
    def _add_pseudocount(self, x: np.ndarray) -> np.ndarray:
        """
        Add pseudocount to avoid zero values.
        
        Args:
            x: Input composition array.
        
        Returns:
            Array with zeros replaced by epsilon.
        """
        return np.where(x == 0, self.epsilon, x)
    
    def fit(self, X: np.ndarray) -> 'CLRTransformer':
        """
        Fit the transformer (no-op for CLR, but required for sklearn compatibility).
        
        Args:
            X: Training data (compositions).
        
        Returns:
            self
        """
        self._is_fitted = True
        logger.debug("CLRTransformer fitted on %d samples", X.shape[0])
        return self
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Apply CLR transformation to input data.
        
        Args:
            X: Input compositions of shape (n_samples, n_components).
        
        Returns:
            CLR-transformed data of same shape.
        
        Raises:
            ValueError: If not fitted or input has zeros without handling.
        """
        if not self._is_fitted:
            raise ValueError("CLRTransformer not fitted. Call fit() first.")
        
        # Handle zeros
        X_clean = self._add_pseudocount(X)
        
        # Apply CLR transformation
        # compositional.clr expects input to be properly normalized
        try:
            X_clr = clr(X_clean)
        except Exception as e:
            logger.error("CLR transformation failed: %s", str(e))
            raise
        
        logger.debug("Transformed %d samples with CLR", X.shape[0])
        return X_clr
    
    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Fit and transform in one step.
        
        Args:
            X: Input compositions.
        
        Returns:
            CLR-transformed data.
        """
        self.fit(X)
        return self.transform(X)
    
    def inverse_transform(self, X_clr: np.ndarray) -> np.ndarray:
        """
        Inverse CLR transformation to recover original composition.
        
        Args:
            X_clr: CLR-transformed data.
        
        Returns:
            Original composition (sums to 1).
        """
        if not self._is_fitted:
            raise ValueError("CLRTransformer not fitted. Call fit() first.")
        
        # Inverse CLR: x_i = exp(clr_i) / sum(exp(clr))
        try:
            from compositional import clr_inv
            X_original = clr_inv(X_clr)
        except Exception as e:
            logger.error("Inverse CLR transformation failed: %s", str(e))
            raise
        
        return X_original

def main():
    """
    Main entry point for standalone execution.
    
    Runs a simple test of the CLR transformer.
    """
    from seed import init_reproducibility
    init_reproducibility(seed=42)
    
    logger.info("Testing CLRTransformer...")
    
    # Create sample compositional data
    np.random.seed(42)
    n_samples = 10
    n_components = 5
    
    # Generate random compositions that sum to 1
    X_raw = np.random.dirichlet(np.ones(n_components), n_samples)
    
    logger.info("Sample composition shape: %s", X_raw.shape)
    logger.info("Sum of first composition: %.6f", X_raw[0].sum())
    
    # Apply CLR transformation
    transformer = CLRTransformer()
    X_clr = transformer.fit_transform(X_raw)
    
    logger.info("CLR-transformed shape: %s", X_clr.shape)
    logger.info("Sum of CLR-transformed (should be ~0): %.6f", X_clr[0].sum())
    
    # Inverse transform
    X_recovered = transformer.inverse_transform(X_clr)
    
    logger.info("Recovered composition sum: %.6f", X_recovered[0].sum())
    logger.info("Max reconstruction error: %.10f", np.max(np.abs(X_raw - X_recovered)))
    
    logger.info("CLRTransformer test completed successfully.")

if __name__ == "__main__":
    main()
