"""
Module for flattening LoRA weights into skill vectors.

This module implements the core logic for User Story 1:
- Loading A/B matrices from raw weight files
- Flattening them into 1D vectors
- Applying L2 normalization
- Ensuring consistent dimensions across adapters
- Logging ingestion metrics
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_data_path, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_lora_weights(weight_path: Path) -> Dict[str, np.ndarray]:
    """
    Load LoRA A/B matrices from an .npz file.

    Args:
        weight_path: Path to the .npz file containing A and B matrices.

    Returns:
        Dictionary with 'A' and 'B' keys containing numpy arrays.

    Raises:
        FileNotFoundError: If the weight file doesn't exist.
        ValueError: If the file doesn't contain expected A/B matrices.
    """
    if not weight_path.exists():
        raise FileNotFoundError(f"Weight file not found: {weight_path}")

    logger.info(f"Loading weights from: {weight_path}")
    data = np.load(weight_path)

    if 'A' not in data or 'B' not in data:
        raise ValueError(f"Weight file {weight_path} must contain 'A' and 'B' matrices")

    A = data['A']
    B = data['B']

    logger.info(f"Loaded matrices - A: {A.shape}, B: {B.shape}")
    return {'A': A, 'B': B}

def flatten_matrices(weights: Dict[str, np.ndarray]) -> Tuple[np.ndarray, int, int]:
    """
    Flatten A and B matrices into a single 1D vector.

    Args:
        weights: Dictionary containing 'A' and 'B' numpy arrays.

    Returns:
        Tuple of (flattened_vector, dim_A, dim_B).
    """
    A = weights['A']
    B = weights['B']

    dim_A = A.size
    dim_B = B.size

    # Flatten and concatenate
    flat_A = A.flatten()
    flat_B = B.flatten()
    flattened = np.concatenate([flat_A, flat_B])

    logger.debug(f"Flattened vectors - A: {flat_A.shape}, B: {flat_B.shape}, combined: {flattened.shape}")
    return flattened, dim_A, dim_B

def l2_normalize(vector: np.ndarray) -> np.ndarray:
    """
    Apply L2 normalization to a vector.

    Args:
        vector: 1D numpy array to normalize.

    Returns:
        L2-normalized vector.
    """
    norm = np.linalg.norm(vector)
    if norm == 0:
        logger.warning("Zero-norm vector detected, returning original vector")
        return vector
    return vector / norm

def validate_dimensions(flattened_vectors: List[np.ndarray]) -> bool:
    """
    Validate that all flattened vectors have consistent dimensions.

    Args:
        flattened_vectors: List of flattened vectors to validate.

    Returns:
        True if all dimensions are consistent, False otherwise.

    Raises:
        ValueError: If dimensions are inconsistent.
    """
    if not flattened_vectors:
        logger.warning("No vectors to validate")
        return True

    first_dim = flattened_vectors[0].shape[0]
    for i, vec in enumerate(flattened_vectors[1:], start=1):
        if vec.shape[0] != first_dim:
            error_msg = f"Dimension mismatch at index {i}: expected {first_dim}, got {vec.shape[0]}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    logger.info(f"All {len(flattened_vectors)} vectors have consistent dimension: {first_dim}")
    return True

def process_weight_files(
    weight_dir: Path,
    output_dir: Path,
    file_pattern: str = "*.npz"
) -> Dict[str, Any]:
    """
    Process all weight files in a directory, flatten, normalize, and collect metrics.

    Args:
        weight_dir: Directory containing weight .npz files.
        output_dir: Directory to save processed vectors.
        file_pattern: Glob pattern for weight files.

    Returns:
        Dictionary containing ingestion metrics.
    """
    ensure_directories()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all weight files
    weight_files = list(weight_dir.glob(file_pattern))
    logger.info(f"Found {len(weight_files)} weight files in {weight_dir}")

    if not weight_files:
        logger.warning(f"No weight files found matching {file_pattern} in {weight_dir}")
        return {
            'vectors_processed': 0,
            'index_size_bytes': 0,
            'dimension': None,
            'files_processed': [],
            'files_failed': [],
            'processing_time_seconds': 0
        }

    flattened_vectors = []
    metadata = []
    files_processed = []
    files_failed = []

    start_time = time.time()

    for weight_file in weight_files:
        try:
            logger.info(f"Processing: {weight_file.name}")

            # Load weights
            weights = load_lora_weights(weight_file)

            # Flatten matrices
            flattened, dim_A, dim_B = flatten_matrices(weights)

            # Apply L2 normalization
            normalized = l2_normalize(flattened)

            # Collect
            flattened_vectors.append(normalized)
            metadata.append({
                'filename': weight_file.name,
                'dim_A': dim_A,
                'dim_B': dim_B,
                'total_dim': flattened.shape[0]
            })
            files_processed.append(weight_file.name)

            logger.info(f"Successfully processed {weight_file.name}: {flattened.shape[0]} dimensions")

        except Exception as e:
            logger.error(f"Failed to process {weight_file.name}: {str(e)}")
            files_failed.append({'file': weight_file.name, 'error': str(e)})

    end_time = time.time()
    processing_time = end_time - start_time

    # Validate dimensions
    if flattened_vectors:
        validate_dimensions(flattened_vectors)

    # Create output index
    index_data = {
        'vectors': np.array(flattened_vectors) if flattened_vectors else np.array([]),
        'metadata': metadata,
        'dimension': flattened_vectors[0].shape[0] if flattened_vectors else 0
    }

    # Save index
    index_path = output_dir / "skill_vectors.npz"
    np.savez_compressed(
        index_path,
        vectors=index_data['vectors'],
        metadata=np.array(metadata, dtype=object)
    )

    index_size_bytes = index_path.stat().st_size

    # Compile metrics
    metrics = {
        'vectors_processed': len(flattened_vectors),
        'index_size_bytes': index_size_bytes,
        'dimension': index_data['dimension'],
        'files_processed': files_processed,
        'files_failed': files_failed,
        'processing_time_seconds': processing_time,
        'output_path': str(index_path)
    }

    # Log summary metrics
    logger.info("=" * 50)
    logger.info("INGESTION METRICS SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Vectors processed: {metrics['vectors_processed']}")
    logger.info(f"Index size: {metrics['index_size_bytes'] / 1024:.2f} KB")
    logger.info(f"Vector dimension: {metrics['dimension']}")
    logger.info(f"Files processed successfully: {len(files_processed)}")
    logger.info(f"Files failed: {len(files_failed)}")
    logger.info(f"Processing time: {processing_time:.2f} seconds")
    logger.info("=" * 50)

    return metrics

def main():
    """
    Main entry point for the flatten_lora script.

    This script:
    1. Loads weight files from data/raw/
    2. Flattens and normalizes them
    3. Saves the skill vector index to data/processed/
    4. Logs comprehensive ingestion metrics
    """
    logger.info("Starting LoRA weight flattening process...")

    # Get paths
    data_path = get_data_path()
    raw_dir = data_path / "raw"
    processed_dir = data_path / "processed"

    # Process weights
    metrics = process_weight_files(
        weight_dir=raw_dir,
        output_dir=processed_dir,
        file_pattern="*.npz"
    )

    # Save metrics to JSON for later use
    metrics_path = processed_dir / "ingestion_metrics.json"
    import json
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)

    logger.info(f"Ingestion metrics saved to: {metrics_path}")
    logger.info("LoRA weight flattening complete.")

    return metrics

if __name__ == "__main__":
    main()