"""
Vector Database Construction Module for LatentSkill Project.

This module handles the loading of flattened LoRA vectors, computation of index structures,
and serialization of the static CPU-compatible skill index.
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path constants relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FLATTENED_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "flattened_vectors"
OUTPUT_INDEX_PATH = PROJECT_ROOT / "data" / "processed" / "skill_index.npz"


def load_flattened_vectors() -> Dict[str, np.ndarray]:
    """
    Load flattened and L2-normalized vectors from the ingestion stage.

    Expects .npy files in data/processed/flattened_vectors/ where:
    - Filename format: <dataset>_<adapter_name>.npy
    - Content: 1D numpy array of normalized weights

    Returns:
        Dict mapping adapter identifiers to their vector arrays.
    """
    if not FLATTENED_DATA_DIR.exists():
        logger.error(f"Flattened data directory not found: {FLATTENED_DATA_DIR}")
        raise FileNotFoundError(f"Flattened data directory not found: {FLATTENED_DATA_DIR}")

    vectors = {}
    npy_files = list(FLATTENED_DATA_DIR.glob("*.npy"))

    if not npy_files:
        logger.warning(f"No .npy files found in {FLATTENED_DATA_DIR}")
        return vectors

    for file_path in npy_files:
        try:
            vec = np.load(file_path)
            if vec.ndim != 1:
                logger.warning(f"Skipping {file_path}: expected 1D array, got {vec.ndim}D")
                continue
            # Derive key from filename
            key = file_path.stem
            vectors[key] = vec
            logger.info(f"Loaded vector: {key} (shape: {vec.shape})")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise

    logger.info(f"Total vectors loaded: {len(vectors)}")
    return vectors


def compute_index_structure(vectors: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Compute metadata and structure for the vector index.

    Args:
        vectors: Dictionary of adapter names to 1D arrays.

    Returns:
        Dictionary containing:
            - 'metadata': List of dicts with adapter info (name, shape, norm)
            - 'dim': The dimensionality of the vectors (assumed uniform)
            - 'count': Total number of vectors
    """
    if not vectors:
        raise ValueError("Cannot compute index structure for empty vector set.")

    # Check uniformity of dimensions
    first_key = next(iter(vectors))
    dim = vectors[first_key].shape[0]
    
    metadata = []
    for name, vec in vectors.items():
        if vec.shape[0] != dim:
            logger.warning(f"Dimension mismatch for {name}: {vec.shape[0]} vs {dim}")
        norm = np.linalg.norm(vec)
        metadata.append({
            "name": name,
            "shape": list(vec.shape),
            "norm": float(norm)
        })

    index_structure = {
        "metadata": metadata,
        "dim": dim,
        "count": len(vectors),
        "source_dir": str(FLATTENED_DATA_DIR)
    }

    logger.info(f"Index structure computed: {len(vectors)} vectors, dim={dim}")
    return index_structure


def prepare_for_serialization(vectors: Dict[str, np.ndarray], structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare data for serialization into the final index file.

    Combines the raw vectors and the computed structure into a single payload.

    Args:
        vectors: Raw vector dictionary.
        structure: Computed index structure metadata.

    Returns:
        Dictionary ready for np.savez.
    """
    # Convert vector dict to arrays for savez
    # We need to pad or handle variable lengths if necessary, but here we assume uniform dim.
    # To store variable names in npz, we pass them as kwargs or use a structured array.
    # Here we store the vectors as a list of arrays and metadata as a separate array.
    
    vector_names = list(vectors.keys())
    vector_arrays = [vectors[k] for k in vector_names]
    
    # Convert metadata to a list of strings or a structured array for saving
    # Since np.savez doesn't handle complex dicts well directly, we serialize metadata to a string
    import json
    metadata_json = json.dumps(structure['metadata'])

    payload = {
        "vector_names": np.array(vector_names, dtype=object),
        "vectors": np.array(vector_arrays, dtype=object), # Store as object array of 1D arrays
        "metadata_json": np.array(metadata_json, dtype=object),
        "dim": np.array(structure['dim']),
        "count": np.array(structure['count'])
    }

    logger.info("Data prepared for serialization.")
    return payload


def save_index(payload: Dict[str, np.ndarray], output_path: Path) -> None:
    """
    Save the prepared payload to a .npz file.

    Args:
        payload: Dictionary of arrays to save.
        output_path: Destination path for the .npz file.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving index to {output_path}")
    np.savez(output_path, **payload)
    
    # Verify file existence and size
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"Index saved successfully. Size: {size_mb:.2f} MB")
    else:
        raise RuntimeError(f"Failed to create output file: {output_path}")


def main() -> None:
    """
    Main entry point to execute the vector DB construction pipeline.
    
    1. Load flattened vectors from data/processed/flattened_vectors/
    2. Compute index structure
    3. Prepare for serialization
    4. Save to data/processed/skill_index.npz
    5. Verify output
    """
    logger.info("Starting Vector DB Construction (T014b)")
    start_time = time.time()

    try:
        # 1. Load
        vectors = load_flattened_vectors()
        if not vectors:
            logger.error("No vectors loaded. Aborting.")
            sys.exit(1)

        # 2. Compute Structure
        structure = compute_index_structure(vectors)

        # 3. Prepare
        payload = prepare_for_serialization(vectors, structure)

        # 4. Save
        save_index(payload, OUTPUT_INDEX_PATH)

        # 5. Verify
        logger.info("Verifying output integrity...")
        with np.load(OUTPUT_INDEX_PATH, allow_pickle=True) as data:
            loaded_names = data['vector_names']
            loaded_count = int(data['count'])
            if len(loaded_names) != loaded_count:
                raise ValueError("Verification failed: Name count mismatch.")
            logger.info(f"Verification passed. {loaded_count} vectors indexed.")

        elapsed = time.time() - start_time
        logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()