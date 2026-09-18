import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

from sklearn.decomposition import PCA
import numpy as np

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)


def run_pca_check(complexity_scores_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run PCA on complexity metrics to verify construct validity.
    Expects a DataFrame with columns: edge_density, entropy, fractal_dim.
    Returns a dictionary with cumulative variance explained.
    """
    if complexity_scores_path is None:
        root = get_project_root()
        complexity_scores_path = root / "data" / "processed" / "complexity_scores.csv"

    if not complexity_scores_path.exists():
        raise FileNotFoundError(f"Complexity scores file not found: {complexity_scores_path}")

    logger.info(f"Loading complexity scores from {complexity_scores_path}")
    df = pd.read_csv(complexity_scores_path)

    # Filter for valid images
    valid_df = df[df['status'] == 'valid'].copy()

    if valid_df.empty:
        raise ValueError("No valid images found in complexity scores.")

    # Select metrics
    metrics = ['edge_density', 'entropy', 'fractal_dim']
    X = valid_df[metrics].dropna()

    if X.empty:
        raise ValueError("No valid metric data after dropping NaNs.")

    logger.info(f"Running PCA on {len(X)} images with {X.shape[1]} metrics")

    # Perform PCA
    pca = PCA()
    pca.fit(X)

    # Calculate cumulative variance
    cumulative_variance = np.cumsum(pca.explained_variance_ratio_)

    result = {
        "n_components": len(pca.explained_variance_ratio_),
        "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "cumulative_variance": cumulative_variance.tolist(),
        "cumulative_variance_threshold_met": cumulative_variance[-1] > 0.8,
        "n_samples": len(X)
    }

    logger.info(f"PCA cumulative variance: {cumulative_variance[-1]:.4f}")

    return result


def main() -> None:
    """Main entry point for PCA check."""
    root = get_project_root()
    output_path = root / "data" / "results" / "pca_variance.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = run_pca_check()

        # Save results
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"PCA results saved to {output_path}")

        # Verify threshold
        if not result["cumulative_variance_threshold_met"]:
            logger.warning(
                f"Cumulative variance ({result['cumulative_variance'][-1]:.4f}) "
                "is below the 0.8 threshold. Construct validity may be compromised."
            )
        else:
            logger.info("Construct validity verified: cumulative variance > 0.8")

    except Exception as e:
        logger.error(f"PCA check failed: {e}")
        raise


if __name__ == "__main__":
    main()
