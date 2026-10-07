"""
CLRTransformer: Applies Centered Log-Ratio transform to compositional data.
Addresses the closure problem (sum-to-one constraint) by mapping to Euclidean space.
"""
import numpy as np
import logging
import json
import pandas as pd
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
from compositional import clr
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
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Apply CLR transform to the data.

        Args:
            X: Compositional data array of shape (n_samples, n_components).

        Returns:
            Transformed data array of shape (n_samples, n_components).
        """
        if X is None or X.size == 0:
            raise ValueError("Input array cannot be empty")

        # Ensure we don't have zeros which would cause log(0)
        X_safe = np.clip(X, self.pseudo_count, None)

        # Normalize to ensure sum is 1 if not already
        sums = X_safe.sum(axis=1, keepdims=True)
        sums = np.where(sums == 0, 1, sums)
        X_normalized = X_safe / sums

        # Apply CLR using the compositional library
        try:
            X_clr = clr(X_normalized)
        except Exception as e:
            logger.error(f"CLR transformation failed: {e}")
            raise

        return X_clr

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Fit and transform the data.
        """
        self.fit(X)
        return self.transform(X)

def main():
    """
    Main entry point.
    Reads cleaned solder data, applies CLR transform, and writes output.
    """
    logger.info("Starting CLR Transformation Pipeline")
    set_seed(42)

    # Paths
    input_path = Path("data/processed/solder_hardness_cleaned.csv")
    output_path = Path("data/processed/clr_features.csv")
    report_path = Path("data/processed/transformer_report.json")

    # Verify input exists
    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Run T013 (cleaner) first to generate solder_hardness_cleaned.csv."
        )

    # Load data
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")

    # Identify composition columns (exclude target and metadata)
    exclude_cols = ['hardness_hv', 'alloy_family', 'source_citation', 'alloy_id']
    # Also exclude non-elemental columns if any (e.g. measurement_temp_c)
    composition_cols = [c for c in df.columns if c not in exclude_cols and not c.startswith('meta_')]

    if not composition_cols:
        raise ValueError("No composition columns found in input data.")

    logger.info(f"Identified composition columns: {composition_cols}")

    # Extract composition matrix
    X = df[composition_cols].values.astype(float)

    # Handle potential NaNs in composition (replace with 0, then add pseudo_count in transform)
    # But cleaner should have handled this. Let's be safe.
    X = np.nan_to_num(X, nan=0.0)

    # Transform
    transformer = CLRTransformer()
    X_clr = transformer.fit_transform(X)

    # Create output DataFrame
    # Keep only the transformed values, named as clr_<col>
    clr_cols = [f"clr_{c}" for c in composition_cols]
    df_clr = pd.DataFrame(X_clr, columns=clr_cols)

    # Add an index or ID to link back if needed (assuming row order is preserved)
    # We'll just save the features as requested
    df_clr.to_csv(output_path, index=False)

    logger.info(f"CLR features written to {output_path} with shape {X_clr.shape}")

    # Write a simple verification report
    report = {
        "status": "success",
        "input_file": str(input_path),
        "output_file": str(output_path),
        "input_shape": list(X.shape),
        "output_shape": list(X_clr.shape),
        "composition_columns": composition_cols,
        "output_columns": clr_cols,
        "row_sums_check": float(np.abs(X_clr.sum(axis=1)).mean()) # Should be ~0
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Verification report written to {report_path}")
    logger.info("CLR Transformation Pipeline completed successfully")

if __name__ == "__main__":
    main()