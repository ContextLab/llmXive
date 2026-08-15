import os
import sys
import logging
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Add project root to path if not already
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_data_path, ensure_directories
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_flattened_vectors(raw_data_dir: Optional[Path] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load flattened LoRA vectors from the raw data directory.
    Expects data/raw/alfworld_weights.npz and data/raw/searchqa_weights.npz
    """
    if raw_data_dir is None:
        raw_data_dir = get_data_path("raw")

    alfworld_path = raw_data_dir / "alfworld_weights.npz"
    searchqa_path = raw_data_dir / "searchqa_weights.npz"

    vectors = []
    metadata = []

    if not alfworld_path.exists():
        raise FileNotFoundError(f"Missing required file: {alfworld_path}")
    if not searchqa_path.exists():
        raise FileNotFoundError(f"Missing required file: {searchqa_path}")

    logger.info(f"Loading vectors from {raw_data_dir}")

    # Load ALFWorld weights
    logger.info(f"Loading ALFWorld weights from {alfworld_path}")
    alfworld_data = np.load(alfworld_path, allow_pickle=True)
    # Expecting keys like 'A', 'B' or specific layer names
    # Assuming structure: keys are layer names, values are tuples (A, B) or arrays
    for key in alfworld_data.files:
        try:
            data = alfworld_data[key]
            if isinstance(data, np.ndarray) and data.ndim > 1:
                # Flatten and normalize
                flat = data.flatten()
                norm = flat / np.linalg.norm(flat)
                vectors.append(norm)
                metadata.append({"source": "alfworld", "layer": key, "dim": len(flat)})
            elif isinstance(data, (tuple, list)) and len(data) == 2:
                # Handle (A, B) tuple if present
                A, B = data
                flat_A = A.flatten()
                flat_B = B.flatten()
                norm_A = flat_A / np.linalg.norm(flat_A)
                norm_B = flat_B / np.linalg.norm(flat_B)
                vectors.append(norm_A)
                vectors.append(norm_B)
                metadata.append({"source": "alfworld", "layer": f"{key}_A", "dim": len(flat_A)})
                metadata.append({"source": "alfworld", "layer": f"{key}_B", "dim": len(flat_B)})
        except Exception as e:
            logger.warning(f"Skipping key {key} due to error: {e}")

    # Load SearchQA weights
    logger.info(f"Loading SearchQA weights from {searchqa_path}")
    searchqa_data = np.load(searchqa_path, allow_pickle=True)
    for key in searchqa_data.files:
        try:
            data = searchqa_data[key]
            if isinstance(data, np.ndarray) and data.ndim > 1:
                flat = data.flatten()
                norm = flat / np.linalg.norm(flat)
                vectors.append(norm)
                metadata.append({"source": "searchqa", "layer": key, "dim": len(flat)})
            elif isinstance(data, (tuple, list)) and len(data) == 2:
                A, B = data
                flat_A = A.flatten()
                flat_B = B.flatten()
                norm_A = flat_A / np.linalg.norm(flat_A)
                norm_B = flat_B / np.linalg.norm(flat_B)
                vectors.append(norm_A)
                vectors.append(norm_B)
                metadata.append({"source": "searchqa", "layer": f"{key}_A", "dim": len(flat_A)})
                metadata.append({"source": "searchqa", "layer": f"{key}_B", "dim": len(flat_B)})
        except Exception as e:
            logger.warning(f"Skipping key {key} due to error: {e}")

    if not vectors:
        raise ValueError("No valid vectors found in the input files.")

    return np.array(vectors), metadata

def compute_index_structure(vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute statistics about the index structure."""
    return {
        "num_vectors": len(vectors),
        "vector_dim": vectors.shape[1] if len(vectors.shape) > 1 else vectors.shape[0],
        "sources": list(set(m["source"] for m in metadata)),
        "total_dim": vectors.shape[1] if len(vectors.shape) > 1 else vectors.shape[0],
        "checksum": hashlib.sha256(vectors.tobytes()).hexdigest()[:16]
    }

def prepare_for_serialization(vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Prepare data for serialization."""
    # Ensure 2D array
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)
    
    # Create metadata dict for npz saving
    meta_dict = {
        "metadata": np.array(metadata, dtype=object),
        "structure": compute_index_structure(vectors, metadata)
    }
    
    return vectors, meta_dict

def save_index(vectors: np.ndarray, metadata: Dict[str, Any], output_path: Path) -> None:
    """Save the index to a .npz file."""
    ensure_directories(output_path.parent)
    
    # Save vectors and metadata
    np.savez(
        output_path,
        vectors=vectors,
        metadata=np.array([metadata], dtype=object) # Wrap structure in list for object array
    )
    
    # Verify
    if not output_path.exists():
        raise RuntimeError(f"Failed to write index file: {output_path}")
    
    logger.info(f"Saved skill index to {output_path} ({output_path.stat().st_size} bytes)")

def main():
    """Main entry point for T014d."""
    logger.info("Starting vector DB construction (T014d)")
    
    raw_dir = get_data_path("raw")
    output_path = get_data_path("processed") / "skill_index.npz"
    
    try:
        vectors, metadata_list = load_flattened_vectors(raw_dir)
        vectors_2d, meta_dict = prepare_for_serialization(vectors, metadata_list)
        save_index(vectors_2d, meta_dict["structure"], output_path)
        
        # Verify output
        if output_path.exists():
            logger.info(f"SUCCESS: Index created at {output_path}")
            return 0
        else:
            logger.error("FAILED: Output file not created")
            return 1
    except FileNotFoundError as e:
        logger.error(f"DATA MISSING: {e}")
        return 1
    except Exception as e:
        logger.error(f"ERROR: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
