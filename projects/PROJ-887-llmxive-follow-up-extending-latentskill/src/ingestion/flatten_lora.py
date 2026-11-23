"""
Flatten LoRA weights into normalized vectors.

This module implements FR-001: Ingest pre-trained LoRA adapters (A and B matrices),
flatten them into normalized high-dimensional vectors, and generate a static CPU-compatible index.
"""
import os
import sys
import logging
import argparse
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

# Import from project utilities
from src.utils.config import get_project_root, ensure_directories, get_data_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_npz_file(file_path: Path) -> Dict[str, np.ndarray]:
    """
    Load weights from an NPZ file.

    Args:
        file_path: Path to the .npz file

    Returns:
        Dictionary of weight matrices
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Weight file not found: {file_path}")

    logger.info(f"Loading weights from {file_path}")
    try:
        data = np.load(file_path, allow_pickle=True)
        weights = {key: data[key] for key in data.files}
        logger.info(f"Loaded {len(weights)} weight matrices")
        return weights
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        raise


def load_weights_from_directory(directory: Path) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Load all NPZ files from a directory.

    Args:
        directory: Path to directory containing .npz files

    Returns:
        Dictionary mapping filename to weight matrices
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    all_weights = {}
    npz_files = list(directory.glob("*.npz"))

    if not npz_files:
        logger.warning(f"No .npz files found in {directory}")
        return all_weights

    for npz_file in npz_files:
        try:
            weights = load_npz_file(npz_file)
            all_weights[npz_file.stem] = weights
        except Exception as e:
            logger.error(f"Skipping {npz_file} due to error: {e}")

    return all_weights


def flatten_and_normalize(weights: Dict[str, np.ndarray]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Flatten A/B matrices and apply L2 normalization.

    Args:
        weights: Dictionary of weight matrices (A and B pairs)

    Returns:
        Tuple of (flattened_normalized_vector, metadata)
    """
    flattened_parts = []
    metadata = {
        "original_shapes": {},
        "total_elements": 0,
        "norm": 0.0
    }

    for key, matrix in weights.items():
        if matrix.ndim < 2:
            logger.warning(f"Skipping non-matrix weight: {key} (shape {matrix.shape})")
            continue

        # Flatten the matrix
        flat = matrix.flatten()
        flattened_parts.append(flat)
        metadata["original_shapes"][key] = list(matrix.shape)
        metadata["total_elements"] += flat.size

    if not flattened_parts:
        raise ValueError("No valid matrices to flatten")

    # Concatenate all flattened matrices
    combined = np.concatenate(flattened_parts)

    # Apply L2 normalization
    norm = np.linalg.norm(combined)
    if norm == 0:
        logger.warning(f"Zero norm detected for combined weights, returning unnormalized vector")
        normalized = combined
    else:
        normalized = combined / norm

    metadata["norm"] = float(norm)
    metadata["final_dimension"] = normalized.size

    return normalized, metadata


def validate_dimensions(all_vectors: List[np.ndarray], expected_dim: Optional[int] = None) -> bool:
    """
    Validate that all vectors have consistent dimensions.

    Args:
        all_vectors: List of flattened vectors
        expected_dim: Optional expected dimension to check against

    Returns:
        True if dimensions are consistent
    """
    if not all_vectors:
        return True

    dims = [v.size for v in all_vectors]
    unique_dims = set(dims)

    if len(unique_dims) > 1:
        logger.error(f"Inconsistent vector dimensions found: {dict(zip(range(len(dims)), dims))}")
        return False

    if expected_dim is not None and dims[0] != expected_dim:
        logger.error(f"Expected dimension {expected_dim}, got {dims[0]}")
        return False

    logger.info(f"All vectors have consistent dimension: {dims[0]}")
    return True


def process_all_weights(
    input_path: Path,
    output_path: Path,
    is_directory: bool = False
) -> Dict[str, Any]:
    """
    Process all weights from input, flatten, normalize, and save to output.

    Args:
        input_path: Path to input file or directory
        output_path: Path to output .npz file
        is_directory: If True, treat input_path as a directory

    Returns:
        Dictionary of ingestion metrics
    """
    start_time = time.time()
    metrics = {
        "input_path": str(input_path),
        "output_path": str(output_path),
        "vectors_processed": 0,
        "total_elements": 0,
        "index_size_bytes": 0,
        "processing_time_seconds": 0.0,
        "dimensions": None,
        "status": "success"
    }

    ensure_directories(output_path.parent)

    try:
        # Load weights
        if is_directory:
            all_weights = load_weights_from_directory(input_path)
        else:
            single_weights = load_npz_file(input_path)
            all_weights = {input_path.stem: single_weights}

        if not all_weights:
            raise ValueError("No weights loaded from input")

        logger.info(f"Processing {len(all_weights)} weight sets")

        flattened_vectors = []
        all_metadata = []

        for name, weights in all_weights.items():
            try:
                vector, meta = flatten_and_normalize(weights)
                flattened_vectors.append(vector)
                all_metadata.append({
                    "name": name,
                    "metadata": meta
                })
                metrics["vectors_processed"] += 1
                metrics["total_elements"] += meta["total_elements"]
            except Exception as e:
                logger.error(f"Error processing {name}: {e}")
                metrics["status"] = "partial_success"

        if not flattened_vectors:
            raise ValueError("No vectors successfully processed")

        # Validate dimensions
        if not validate_dimensions(flattened_vectors):
            logger.warning("Dimension validation failed, proceeding with warning")

        # Create output arrays
        vector_array = np.array(flattened_vectors)
        metrics["dimensions"] = vector_array.shape

        # Save to NPZ
        np.savez(
            output_path,
            vectors=vector_array,
            metadata=np.array(all_metadata, dtype=object),
            allow_pickle=True
        )

        # Calculate file size
        metrics["index_size_bytes"] = output_path.stat().st_size

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        metrics["status"] = "failed"
        raise
    finally:
        metrics["processing_time_seconds"] = time.time() - start_time

    # Log final metrics
    logger.info("=" * 50)
    logger.info("INGESTION METRICS")
    logger.info("=" * 50)
    logger.info(f"Input: {metrics['input_path']}")
    logger.info(f"Output: {metrics['output_path']}")
    logger.info(f"Vectors processed: {metrics['vectors_processed']}")
    logger.info(f"Total elements: {metrics['total_elements']}")
    logger.info(f"Index size: {metrics['index_size_bytes']:,} bytes ({metrics['index_size_bytes'] / 1024 / 1024:.2f} MB)")
    logger.info(f"Vector dimension: {metrics['dimensions'][1] if metrics['dimensions'] else 'N/A'}")
    logger.info(f"Processing time: {metrics['processing_time_seconds']:.2f} seconds")
    logger.info(f"Status: {metrics['status']}")
    logger.info("=" * 50)

    return metrics


def main():
    """CLI entry point for flatten_lora."""
    parser = argparse.ArgumentParser(
        description="Flatten and normalize LoRA weights into vectors"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input .npz file or directory containing .npz files"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output .npz file"
    )
    parser.add_argument(
        "--is-directory",
        action="store_true",
        help="Treat input as a directory containing multiple .npz files"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)

    try:
        metrics = process_all_weights(
            input_path=input_path,
            output_path=output_path,
            is_directory=args.is_directory
        )
        logger.info("Flatten and normalize completed successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Flatten and normalize failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()