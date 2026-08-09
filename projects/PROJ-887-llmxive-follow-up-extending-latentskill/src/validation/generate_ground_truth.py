"""
Generate synthetic ground truth weights for known composite tasks.

This module implements the ground truth generation logic required for
T022d (Reconstruction Error) and T030 (Linearity Check).

It interpolates existing single-task weights using the formula:
W_syn = alpha * W_A + (1-alpha) * W_B

where alpha=0.5.

The output is saved to `data/processed/composite_ground_truth.npz`.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Ensure output directory exists
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_proxy_weights(source: str) -> Dict[str, np.ndarray]:
    """
    Load proxy weights from the specified source.

    Args:
        source: Either 'alfworld' or 'searchqa'

    Returns:
        Dictionary containing 'A' and 'B' matrices.

    Raises:
        FileNotFoundError: If the proxy file does not exist.
        ValueError: If the file format is incorrect.
    """
    if source not in ['alfworld', 'searchqa']:
        raise ValueError(f"Invalid source: {source}. Must be 'alfworld' or 'searchqa'.")

    file_path = DATA_RAW_DIR / f"proxy_{source}_weights.npz"

    if not file_path.exists():
        raise FileNotFoundError(f"Proxy weights file not found: {file_path}")

    try:
        data = np.load(file_path)
        # Ensure we have A and B matrices
        if 'A' not in data or 'B' not in data:
            raise ValueError(f"Invalid proxy weights format in {file_path}. Expected 'A' and 'B' keys.")

        return {
            'A': data['A'],
            'B': data['B'],
            'source': source
        }
    except Exception as e:
        logger.error(f"Failed to load proxy weights from {file_path}: {e}")
        raise

def interpolate_weights(
    weights_a: Dict[str, np.ndarray],
    weights_b: Dict[str, np.ndarray],
    alpha: float = 0.5
) -> Dict[str, np.ndarray]:
    """
    Interpolate between two sets of weights using the formula:
    W_syn = alpha * W_A + (1-alpha) * W_B

    Args:
        weights_a: Dictionary containing 'A' and 'B' matrices for task A.
        weights_b: Dictionary containing 'A' and 'B' matrices for task B.
        alpha: Interpolation factor (0.0 to 1.0). Default is 0.5.

    Returns:
        Dictionary containing interpolated 'A' and 'B' matrices.

    Raises:
        ValueError: If matrix dimensions do not match.
    """
    if not np.allclose(weights_a['A'].shape, weights_b['A'].shape):
        raise ValueError(
            f"Matrix A dimensions do not match: "
            f"{weights_a['A'].shape} vs {weights_b['A'].shape}"
        )
    if not np.allclose(weights_a['B'].shape, weights_b['B'].shape):
        raise ValueError(
            f"Matrix B dimensions do not match: "
            f"{weights_a['B'].shape} vs {weights_b['B'].shape}"
        )

    if not 0.0 <= alpha <= 1.0:
        raise ValueError(f"Alpha must be between 0.0 and 1.0, got {alpha}")

    synthesized_A = alpha * weights_a['A'] + (1 - alpha) * weights_b['A']
    synthesized_B = alpha * weights_a['B'] + (1 - alpha) * weights_b['B']

    return {
        'A': synthesized_A,
        'B': synthesized_B,
        'alpha': alpha,
        'source_a': weights_a.get('source', 'unknown'),
        'source_b': weights_b.get('source', 'unknown')
    }

def save_ground_truth(
    weights: Dict[str, np.ndarray],
    output_path: Path
) -> None:
    """
    Save the synthesized ground truth weights to an .npz file.

    Args:
        weights: Dictionary containing 'A', 'B', and metadata.
        output_path: Path to save the .npz file.
    """
    try:
        np.savez(
            output_path,
            A=weights['A'],
            B=weights['B'],
            alpha=weights['alpha'],
            source_a=weights['source_a'],
            source_b=weights['source_b']
        )
        logger.info(f"Successfully saved ground truth to {output_path}")

        # Verify the saved file
        verify_saved_file(output_path)
    except Exception as e:
        logger.error(f"Failed to save ground truth to {output_path}: {e}")
        raise

def verify_saved_file(file_path: Path) -> None:
    """
    Verify that the saved file contains the expected data.

    Args:
        file_path: Path to the .npz file.

    Raises:
        ValueError: If the file does not contain expected keys or shapes.
    """
    data = np.load(file_path)
    expected_keys = ['A', 'B', 'alpha', 'source_a', 'source_b']

    for key in expected_keys:
        if key not in data:
            raise ValueError(f"Missing expected key '{key}' in saved file {file_path}")

    logger.info(f"Verified saved file: {file_path}")
    logger.info(f"  - A shape: {data['A'].shape}")
    logger.info(f"  - B shape: {data['B'].shape}")
    logger.info(f"  - alpha: {data['alpha']}")
    logger.info(f"  - source_a: {data['source_a']}")
    logger.info(f"  - source_b: {data['source_b']}")

def generate_composite_ground_truth(alpha: float = 0.5) -> Dict[str, Any]:
    """
    Main function to generate composite ground truth weights.

    This function:
    1. Loads proxy weights for ALFWorld and SearchQA.
    2. Interpolates them using the specified alpha.
    3. Saves the result to data/processed/composite_ground_truth.npz.

    Args:
        alpha: Interpolation factor. Default is 0.5.

    Returns:
        Dictionary containing metadata about the generation process.
    """
    logger.info("Starting composite ground truth generation...")

    # Load proxy weights
    try:
        weights_alfworld = load_proxy_weights('alfworld')
        logger.info(f"Loaded ALFWorld proxy weights: A shape {weights_alfworld['A'].shape}, B shape {weights_alfworld['B'].shape}")
    except FileNotFoundError as e:
        logger.error(f"ALFWorld proxy weights not found. Please run T012 first.")
        raise
    except Exception as e:
        logger.error(f"Error loading ALFWorld proxy weights: {e}")
        raise

    try:
        weights_searchqa = load_proxy_weights('searchqa')
        logger.info(f"Loaded SearchQA proxy weights: A shape {weights_searchqa['A'].shape}, B shape {weights_searchqa['B'].shape}")
    except FileNotFoundError as e:
        logger.error(f"SearchQA proxy weights not found. Please run T012 first.")
        raise
    except Exception as e:
        logger.error(f"Error loading SearchQA proxy weights: {e}")
        raise

    # Interpolate weights
    logger.info(f"Interpolating weights with alpha={alpha}...")
    synthesized_weights = interpolate_weights(
        weights_alfworld,
        weights_searchqa,
        alpha=alpha
    )

    # Save ground truth
    output_path = DATA_PROCESSED_DIR / "composite_ground_truth.npz"
    save_ground_truth(synthesized_weights, output_path)

    logger.info("Composite ground truth generation completed successfully.")

    return {
        'output_path': str(output_path),
        'alpha': alpha,
        'source_a': 'alfworld',
        'source_b': 'searchqa',
        'A_shape': synthesized_weights['A'].shape,
        'B_shape': synthesized_weights['B'].shape
    }

def main():
    """
    Entry point for the script.
    """
    logger.info("Executing generate_ground_truth.py...")

    try:
        result = generate_composite_ground_truth(alpha=0.5)
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)

    logger.info("Script completed successfully.")

if __name__ == "__main__":
    main()
