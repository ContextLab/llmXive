import os
import sys
import logging
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.config import get_data_path, get_project_root, ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_flattened_vectors(input_path: Path) -> Dict[str, Any]:
    """
    Load flattened vectors from an npz file.
    Expected structure: vector (1D array), metadata (dict)
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = np.load(input_path, allow_pickle=True)
    
    if 'vector' not in data.files:
        raise ValueError("Input file must contain 'vector' key")
    
    vector = data['vector']
    metadata = {}
    if 'metadata' in data.files:
        metadata = data['metadata'].item() if isinstance(data['metadata'], np.ndarray) else data['metadata']
    
    return {
        "vector": vector,
        "metadata": metadata,
        "shape": vector.shape,
        "dtype": str(vector.dtype)
    }

def compute_index_structure(vectors: List[np.ndarray], k: int) -> Dict[str, Any]:
    """
    Compute index structure for a list of vectors.
    Returns metadata about the index.
    """
    if not vectors:
        return {"error": "No vectors provided"}
    
    # Assume all vectors have same dimension
    dim = vectors[0].shape[0]
    n_vectors = len(vectors)
    
    return {
        "n_vectors": n_vectors,
        "dimension": dim,
        "k": k,
        "total_elements": n_vectors * dim
    }

def prepare_for_serialization(vectors: List[np.ndarray], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare vectors for serialization.
    Returns a dictionary ready to be saved.
    """
    if not vectors:
        return {"error": "No vectors to serialize"}
    
    # Stack vectors into a 2D array
    stacked = np.stack(vectors, axis=0)
    
    return {
        "vectors": stacked,
        "metadata": metadata,
        "shape": stacked.shape,
        "dtype": str(stacked.dtype),
        "checksum": hashlib.sha256(stacked.tobytes()).hexdigest()
    }

def save_index(serialized_data: Dict[str, Any], output_path: Path, k: int) -> None:
    """
    Save the skill index to an npz file.
    Uses atomic write: write to .tmp then rename.
    """
    temp_path = output_path.with_suffix('.npz.tmp')
    
    try:
        vectors = serialized_data["vectors"]
        metadata = serialized_data["metadata"]
        checksum = serialized_data["checksum"]
        
        # Add index metadata
        final_metadata = {
            "index_shape": list(vectors.shape),
            "dtype": str(vectors.dtype),
            "checksum": checksum,
            "k": k,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_metadata": metadata
        }
        
        # Save to temp file
        np.savez(temp_path, 
                vectors=vectors,
                metadata=final_metadata)
        
        # Verify and rename
        if temp_path.exists():
            temp_path.rename(output_path)
            logger.info(f"Successfully saved index to {output_path}")
            logger.info(f"Index checksum: {checksum}")
        else:
            raise RuntimeError("Temporary file not created")
            
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise e

def main():
    """Main entry point for building skill index."""
    parser = argparse.ArgumentParser(description="Build skill vector index from flattened weights")
    parser.add_argument("--input", type=str, required=True, help="Input file containing flattened weights")
    parser.add_argument("--output", type=str, required=True, help="Output file path for skill index")
    parser.add_argument("--k", type=int, default=5, help="Number of top skills to consider")
    parser.add_argument("--log", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log.upper()))
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    k = args.k
    
    # Ensure output directory exists
    ensure_directories([output_path.parent])
    
    try:
        logger.info(f"Loading flattened vectors from {input_path}")
        loaded_data = load_flattened_vectors(input_path)
        
        vector = loaded_data["vector"]
        metadata = loaded_data["metadata"]
        
        logger.info(f"Loaded vector of shape {vector.shape}")
        
        # For a single flattened vector, we treat it as one skill
        # In a real scenario, we might have multiple vectors
        vectors_list = [vector]
        
        # Compute index structure
        index_structure = compute_index_structure(vectors_list, k)
        logger.info(f"Index structure: {index_structure}")
        
        # Prepare for serialization
        serialized = prepare_for_serialization(vectors_list, metadata)
        
        # Save index
        save_index(serialized, output_path, k)
        
        # Verify output
        if output_path.exists():
            logger.info(f"Output file verified: {output_path}")
            output_data = np.load(output_path, allow_pickle=True)
            logger.info(f"Output vector shape: {output_data['vectors'].shape}")
            logger.info(f"Output checksum: {output_data['metadata'].item()['checksum']}")
        else:
            raise RuntimeError("Output file was not created")
        
    except Exception as e:
        logger.error(f"Failed to build index: {e}")
        raise

if __name__ == "__main__":
    main()