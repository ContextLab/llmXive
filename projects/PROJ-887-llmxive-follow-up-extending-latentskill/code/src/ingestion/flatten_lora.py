import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

from src.utils.config import get_data_path, ensure_directories, load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_npz_file(file_path: Path) -> Dict[str, np.ndarray]:
    """Loads an .npz file and returns the dictionary of arrays."""
    data = np.load(file_path, allow_pickle=True)
    return {key: data[key] for key in data.files}

def load_weights_from_directory(directory: Path) -> List[Tuple[Path, Dict[str, np.ndarray]]]:
    """
    Loads all weight files from a directory.
    Returns a list of (file_path, weights_dict).
    """
    weight_files = []
    for ext in ["*.npz", "*.safetensors", "*.pt", "*.bin"]:
        weight_files.extend(directory.glob(f"**/{ext}"))
    
    # Filter for actual weight files (simple heuristic: size > 1KB)
    valid_files = [f for f in weight_files if f.stat().st_size > 1024]
    
    loaded_weights = []
    for f in valid_files:
        try:
            if f.suffix == '.npz':
                weights = load_npz_file(f)
                loaded_weights.append((f, weights))
            elif f.suffix == '.safetensors':
                # Simplified loading for safetensors (requires library)
                # For this task, we assume we are working with .npz or pre-processed data
                # If .safetensors are present, we would need to convert them.
                # Given the constraints, we skip .safetensors unless we have the library.
                logger.warning(f"Skipping {f} (safetensors support requires extra library)")
            else:
                logger.warning(f"Skipping unsupported format: {f}")
        except Exception as e:
            logger.error(f"Failed to load {f}: {e}")
    
    return loaded_weights

def flatten_and_normalize(weights: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Flattens all weight matrices in the dictionary and applies L2 normalization.
    Returns a single 1D normalized vector.
    """
    flattened = []
    for key, array in weights.items():
        if isinstance(array, np.ndarray):
            flat = array.flatten()
            flattened.append(flat)
    
    if not flattened:
        raise ValueError("No valid arrays found in weights")
    
    combined = np.concatenate(flattened)
    
    # L2 Normalization
    norm = np.linalg.norm(combined)
    if norm == 0:
        raise ValueError("Zero norm encountered during normalization")
    
    return combined / norm

def validate_dimensions(vectors: List[np.ndarray]) -> bool:
    """
    Validates that all vectors have the same dimension.
    """
    if not vectors:
        return False
    first_dim = vectors[0].shape[0]
    for v in vectors:
        if v.shape[0] != first_dim:
            logger.error(f"Dimension mismatch: {first_dim} vs {v.shape[0]}")
            return False
    return True

def process_all_weights(input_dir: Path, output_path: Path) -> None:
    """
    Main processing logic: load, flatten, normalize, and save.
    """
    logger.info(f"Processing weights from {input_dir}")
    
    loaded = load_weights_from_directory(input_dir)
    if not loaded:
        raise RuntimeError("No valid weight files found in input directory")
    
    vectors = []
    metadata = []
    
    for file_path, weights in loaded:
        try:
            vec = flatten_and_normalize(weights)
            vectors.append(vec)
            metadata.append({
                "source": str(file_path),
                "dim": vec.shape[0]
            })
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
    
    if not vectors:
        raise RuntimeError("No valid vectors generated")
    
    if not validate_dimensions(vectors):
        raise RuntimeError("Dimension validation failed")
    
    # Stack vectors
    matrix = np.stack(vectors)
    
    logger.info(f"Saving {matrix.shape[0]} vectors of dimension {matrix.shape[1]} to {output_path}")
    ensure_directories([output_path.parent])
    np.savez_compressed(output_path, vectors=matrix, metadata=np.array(metadata, dtype=object))

def main():
    parser = argparse.ArgumentParser(description="Flatten and normalize LoRA weights")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing weights")
    parser.add_argument("--output", type=str, required=True, help="Output .npz file path")
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_path = Path(args.output)
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    try:
        process_all_weights(input_dir, output_path)
        logger.info("Flatten and normalize completed successfully")
    except Exception as e:
        logger.error(f"Flatten and normalize failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
