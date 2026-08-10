"""
Module for flattening LoRA adapters into normalized skill vectors.

This module implements the core logic for User Story 1 (Constructing the Skill Vector Database).
It loads A/B matrices from real LoRA weights, flattens them into 1D vectors, applies L2 normalization,
and outputs ingestion metrics including vector counts and index size.
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def load_lora_weights(filepath: Path) -> Dict[str, np.ndarray]:
    """
    Load LoRA weights from an .npz file.

    Args:
        filepath: Path to the .npz file containing LoRA weights.

    Returns:
        Dictionary mapping weight names to numpy arrays.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is corrupted or contains invalid data.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Weight file not found: {filepath}")

    logger.info(f"Loading weights from {filepath}")
    try:
        data = np.load(filepath, allow_pickle=False)
        weights = {key: data[key] for key in data.files}
        logger.info(f"Loaded {len(weights)} weight matrices from {filepath.name}")
        return weights
    except Exception as e:
        logger.error(f"Failed to load weights from {filepath}: {e}")
        raise


def flatten_and_normalize(weights: Dict[str, np.ndarray]) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Flatten all weight matrices into a single 1D vector and apply L2 normalization.

    Args:
        weights: Dictionary of weight matrices.

    Returns:
        Tuple of (flattened_normalized_vector, metadata_list).
    """
    flattened_parts = []
    metadata = []

    for name, matrix in weights.items():
        # Flatten the matrix
        flat = matrix.flatten()
        flattened_parts.append(flat)

        # Record metadata for this component
        metadata.append({
            "name": name,
            "original_shape": matrix.shape,
            "flattened_size": flat.shape[0]
        })

    # Concatenate all flattened parts
    full_vector = np.concatenate(flattened_parts)

    # Apply L2 normalization
    norm = np.linalg.norm(full_vector)
    if norm == 0:
        logger.warning(f"Zero norm detected for vector, returning zero vector")
        normalized_vector = full_vector
    else:
        normalized_vector = full_vector / norm

    logger.info(f"Flattened vector size: {full_vector.shape[0]}, normalized: {normalized_vector.shape[0]}")
    return normalized_vector, metadata


def validate_dimensions(all_vectors: List[np.ndarray]) -> bool:
    """
    Validate that all flattened vectors have consistent dimensions.

    Args:
        all_vectors: List of flattened vectors.

    Returns:
        True if all dimensions match, False otherwise.
    """
    if not all_vectors:
        logger.warning("No vectors to validate")
        return True

    first_dim = all_vectors[0].shape[0]
    for i, vec in enumerate(all_vectors[1:], start=1):
        if vec.shape[0] != first_dim:
            logger.error(f"Dimension mismatch: vector 0 has {first_dim}, vector {i} has {vec.shape[0]}")
            return False
    logger.info(f"All {len(all_vectors)} vectors have consistent dimension {first_dim}")
    return True


def process_all_adapters(input_dir: Path = DATA_RAW_DIR) -> Dict[str, Any]:
    """
    Process all LoRA adapter files in the input directory.

    Args:
        input_dir: Directory containing .npz weight files.

    Returns:
        Dictionary containing processed vectors, metadata, and ingestion metrics.
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # Find all .npz files
    weight_files = list(input_dir.glob("*.npz"))
    if not weight_files:
        raise ValueError(f"No .npz files found in {input_dir}")

    logger.info(f"Found {len(weight_files)} weight files to process")

    all_vectors = []
    all_metadata = []
    metrics = {
        "start_time": time.time(),
        "files_processed": 0,
        "files_failed": 0,
        "total_vectors": 0,
        "vector_dimension": None,
        "total_size_bytes": 0,
        "processing_time_seconds": 0
    }

    for weight_file in weight_files:
        try:
            logger.info(f"Processing {weight_file.name}")
            weights = load_lora_weights(weight_file)
            vector, meta = flatten_and_normalize(weights)

            all_vectors.append(vector)
            all_metadata.append({
                "source_file": weight_file.name,
                "components": meta
            })
            metrics["files_processed"] += 1
            metrics["total_size_bytes"] += vector.nbytes

        except Exception as e:
            logger.error(f"Failed to process {weight_file.name}: {e}")
            metrics["files_failed"] += 1
            continue

    if not all_vectors:
        raise RuntimeError("No vectors were successfully processed")

    # Validate dimensions
    if not validate_dimensions(all_vectors):
        raise RuntimeError("Dimension validation failed")

    metrics["vector_dimension"] = all_vectors[0].shape[0]
    metrics["total_vectors"] = len(all_vectors)
    metrics["end_time"] = time.time()
    metrics["processing_time_seconds"] = metrics["end_time"] - metrics["start_time"]

    logger.info(f"Ingestion complete: {metrics['files_processed']} vectors processed, "
               f"dimension={metrics['vector_dimension']}, size={metrics['total_size_bytes']} bytes")

    return {
        "vectors": all_vectors,
        "metadata": all_metadata,
        "metrics": metrics
    }


def save_flattened_index(result: Dict[str, Any], output_path: Path) -> None:
    """
    Save the flattened vectors and metadata to an .npz file.

    Args:
        result: Dictionary containing vectors, metadata, and metrics.
        output_path: Path to save the .npz file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare arrays for saving
    vectors = np.array(result["vectors"])
    metadata_json = []
    for meta in result["metadata"]:
        # Convert numpy arrays in metadata to lists for JSON serialization
        clean_meta = {
            "source_file": meta["source_file"],
            "components": [
                {
                    "name": comp["name"],
                    "original_shape": list(comp["original_shape"]),
                    "flattened_size": int(comp["flattened_size"])
                }
                for comp in meta["components"]
            ]
        }
        metadata_json.append(clean_meta)

    # Save vectors as numpy array
    np.savez(
        output_path,
        vectors=vectors,
        metadata=metadata_json,
        metrics=result["metrics"]
    )

    logger.info(f"Saved flattened index to {output_path}")


def main():
    """
    Main entry point for the flattening script.
    """
    logger.info("Starting LoRA weight flattening process")

    try:
        # Process all adapters
        result = process_all_adapters(DATA_RAW_DIR)

        # Save the index
        output_path = DATA_PROCESSED_DIR / "flattened_vectors.npz"
        save_flattened_index(result, output_path)

        # Log final metrics
        metrics = result["metrics"]
        logger.info("=" * 50)
        logger.info("INGESTION METRICS")
        logger.info("=" * 50)
        logger.info(f"Files processed: {metrics['files_processed']}")
        logger.info(f"Files failed: {metrics['files_failed']}")
        logger.info(f"Total vectors: {metrics['total_vectors']}")
        logger.info(f"Vector dimension: {metrics['vector_dimension']}")
        logger.info(f"Total size: {metrics['total_size_bytes']:,} bytes")
        logger.info(f"Processing time: {metrics['processing_time_seconds']:.2f} seconds")
        logger.info("=" * 50)

        # Return success
        return 0

    except Exception as e:
        logger.error(f"Flattening process failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())