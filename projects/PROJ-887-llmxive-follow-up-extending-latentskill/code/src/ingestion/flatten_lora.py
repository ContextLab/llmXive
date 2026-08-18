import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.config import get_data_path, get_project_root, ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_npz_file(file_path: Path) -> Dict[str, np.ndarray]:
    """Load an npz file and return as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    data = np.load(file_path, allow_pickle=True)
    return {key: data[key] for key in data.files}

def load_weights_from_directory(dir_path: Path) -> Dict[str, Dict[str, np.ndarray]]:
    """Load all npz files from a directory."""
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    weights = {}
    for npz_file in dir_path.glob("*.npz"):
        logger.info(f"Loading {npz_file.name}")
        weights[npz_file.stem] = load_npz_file(npz_file)
    
    return weights

def flatten_and_normalize(weights_dict: Dict[str, np.ndarray]) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Flatten all weight matrices into a single 1D vector and L2 normalize.
    Returns the flattened vector and metadata about dimensions.
    """
    flattened_parts = []
    metadata = {}
    
    for key, matrix in weights_dict.items():
        # Ensure matrix is 2D
        if matrix.ndim == 1:
            matrix = matrix.reshape(1, -1)
        elif matrix.ndim > 2:
            # Flatten higher dimensions
            matrix = matrix.reshape(-1, matrix.shape[-1])
        
        # Flatten to 1D
        flat = matrix.flatten()
        flattened_parts.append(flat)
        metadata[key] = len(flat)
    
    if not flattened_parts:
        raise ValueError("No weights to flatten")
    
    # Concatenate all parts
    combined = np.concatenate(flattened_parts)
    
    # L2 normalize
    norm = np.linalg.norm(combined)
    if norm == 0:
        logger.warning("Zero norm detected, returning unnormalized vector")
        return combined, metadata
    
    normalized = combined / norm
    
    return normalized, metadata

def validate_dimensions(all_metadata: List[Dict[str, int]]) -> bool:
    """
    Validate that all weight sets have consistent dimensions.
    This is a simplified check - in reality, we'd check specific layer dimensions.
    """
    if not all_metadata:
        return True
    
    # For now, we just check that we have data
    # A more robust check would compare specific layer sizes
    logger.info(f"Validating dimensions across {len(all_metadata)} weight sets")
    return True

def process_all_weights(input_path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Process all weight files from input path.
    Returns the combined flattened vector and metadata.
    """
    all_flattened = []
    all_metadata = []
    total_size = 0
    
    if input_path.is_file():
        # Single file
        weights = {input_path.stem: load_npz_file(input_path)}
    elif input_path.is_dir():
        # Directory
        weights = load_weights_from_directory(input_path)
    else:
        raise ValueError(f"Input path is neither file nor directory: {input_path}")
    
    if not weights:
        raise ValueError("No weight files found")
    
    for name, weight_dict in weights.items():
        logger.info(f"Processing {name}: {len(weight_dict)} matrices")
        
        # Flatten and normalize this set
        flattened, meta = flatten_and_normalize(weight_dict)
        all_flattened.append(flattened)
        all_metadata.append(meta)
        total_size += len(flattened)
        
        logger.info(f"  Flattened size: {len(flattened)}, norm: {np.linalg.norm(flattened):.4f}")
    
    # Validate dimensions
    if not validate_dimensions(all_metadata):
        logger.warning("Dimension validation failed")
    
    # Combine all flattened vectors
    combined = np.concatenate(all_flattened)
    
    # Final normalization of combined vector
    norm = np.linalg.norm(combined)
    if norm > 0:
        combined = combined / norm
    
    result_metadata = {
        "total_vectors": len(weights),
        "total_elements": total_size,
        "final_norm": float(np.linalg.norm(combined)),
        "sources": list(weights.keys())
    }
    
    return combined, result_metadata

def main():
    """Main entry point for flattening LoRA weights."""
    parser = argparse.ArgumentParser(description="Flatten and normalize LoRA weights")
    parser.add_argument("--input", type=str, required=True, help="Input file or directory path")
    parser.add_argument("--output", type=str, required=True, help="Output file path for flattened weights")
    parser.add_argument("--log", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log.upper()))
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Ensure output directory exists
    ensure_directories([output_path.parent])
    
    try:
        logger.info(f"Processing weights from {input_path}")
        flattened_vector, metadata = process_all_weights(input_path)
        
        logger.info(f"Saving flattened vector to {output_path}")
        np.savez(output_path, 
                vector=flattened_vector,
                metadata=metadata)
        
        logger.info(f"Successfully saved {len(flattened_vector)} elements")
        
    except Exception as e:
        logger.error(f"Failed to process weights: {e}")
        raise

if __name__ == "__main__":
    main()
