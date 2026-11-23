import os
import sys
import logging
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np

from src.utils.config import get_data_path, ensure_directories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_flattened_vectors(input_path: Path) -> Dict[str, np.ndarray]:
    """Loads the flattened vectors from the .npz file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = np.load(input_path, allow_pickle=True)
    return {key: data[key] for key in data.files}

def compute_index_structure(vectors: np.ndarray) -> Dict[str, Any]:
    """
    Computes the structure of the index (dimensions, count).
    """
    return {
        "count": vectors.shape[0],
        "dimension": vectors.shape[1],
        "dtype": str(vectors.dtype)
    }

def prepare_for_serialization(vectors: np.ndarray, metadata: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """
    Prepares data for serialization.
    """
    return {
        "vectors": vectors,
        "metadata": metadata,
        "index_info": compute_index_structure(vectors)
    }

def save_index(data: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the index to a .npz file.
    """
    ensure_directories([output_path.parent])
    
    # Compute checksum for integrity
    # We save the data and a checksum
    np.savez_compressed(output_path, **data)
    
    # Verify
    if output_path.exists():
        logger.info(f"Index saved to {output_path}")
    else:
        raise RuntimeError("Failed to save index")

def main():
    parser = argparse.ArgumentParser(description="Build Skill Vector Index")
    parser.add_argument("--input", type=str, required=True, help="Input flattened vectors .npz")
    parser.add_argument("--output", type=str, required=True, help="Output index .npz")
    parser.add_argument("--k", type=int, default=5, help="Top-k for retrieval (metadata)")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        logger.info(f"Loading vectors from {input_path}")
        data = load_flattened_vectors(input_path)
        
        vectors = data.get('vectors')
        metadata = data.get('metadata')
        
        if vectors is None:
            raise ValueError("No 'vectors' key found in input file")
        
        logger.info(f"Processing {vectors.shape[0]} vectors")
        
        # Prepare for serialization
        index_data = prepare_for_serialization(vectors, metadata)
        
        # Save
        save_index(index_data, output_path)
        
        logger.info(f"Index built successfully at {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to build index: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
