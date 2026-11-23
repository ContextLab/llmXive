import os
import sys
import logging
import time
import hashlib
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Add project root to path to allow imports from src
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_project_root, get_data_path, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_flattened_vectors(input_path: Path) -> Tuple[Dict[str, Any], List[np.ndarray], List[str]]:
    """
    Load flattened and normalized LoRA vectors from an .npz file.
    
    Args:
        input_path: Path to the input .npz file containing flattened vectors.
        
    Returns:
        Tuple of (metadata, list of vectors, list of task IDs).
    """
    import numpy as np
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading flattened vectors from {input_path}")
    
    try:
        data = np.load(input_path, allow_pickle=True)
    except Exception as e:
        logger.error(f"Failed to load {input_path}: {e}")
        raise
    
    # Expecting keys: 'vectors' (2D array), 'task_ids' (1D array), 'metadata' (dict)
    if 'vectors' not in data:
        raise ValueError(f"Expected 'vectors' key in {input_path}")
    if 'task_ids' not in data:
        raise ValueError(f"Expected 'task_ids' key in {input_path}")
    
    vectors = data['vectors']
    task_ids = data['task_ids']
    
    # Handle metadata if present
    metadata = {}
    if 'metadata' in data:
        metadata = data['metadata'].item() if isinstance(data['metadata'], np.ndarray) else data['metadata']
    
    logger.info(f"Loaded {len(vectors)} vectors with shape {vectors.shape}")
    return metadata, vectors, task_ids.tolist()


def compute_index_structure(vectors: List[np.ndarray], k: int) -> Dict[str, Any]:
    """
    Compute the structure of the skill index for serialization.
    
    Args:
        vectors: List of 1D numpy arrays representing skill vectors.
        k: Number of top neighbors to consider for each skill (used for metadata).
        
    Returns:
        Dictionary containing index structure information.
    """
    import numpy as np
    
    if not vectors:
        return {"error": "No vectors provided"}
    
    # Ensure all vectors are numpy arrays and have consistent dimensions
    vector_array = np.array(vectors)
    if len(vector_array.shape) != 2:
        raise ValueError(f"Expected 2D array of vectors, got shape {vector_array.shape}")
    
    return {
        "num_skills": len(vectors),
        "vector_dimension": vector_array.shape[1],
        "top_k": k,
        "dtype": str(vector_array.dtype)
    }


def prepare_for_serialization(vectors: np.ndarray, task_ids: List[str], metadata: Dict[str, Any], k: int) -> Dict[str, Any]:
    """
    Prepare data for serialization into the final skill index.
    
    Args:
        vectors: 2D numpy array of skill vectors.
        task_ids: List of task IDs corresponding to each vector.
        metadata: Additional metadata for the index.
        k: Top-k parameter for retrieval.
        
    Returns:
        Dictionary ready for serialization.
    """
    import numpy as np
    
    # Validate inputs
    if vectors.shape[0] != len(task_ids):
        raise ValueError(f"Number of vectors ({vectors.shape[0]}) does not match number of task IDs ({len(task_ids)})")
    
    # Compute index structure
    index_info = compute_index_structure([vectors[i] for i in range(vectors.shape[0])], k)
    
    # Prepare final data structure
    serialized_data = {
        "vectors": vectors,
        "task_ids": np.array(task_ids),
        "metadata": {
            **metadata,
            "index_info": index_info,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "flatten_lora.py"
        }
    }
    
    logger.info(f"Prepared index with {len(task_ids)} skills, vector dim {vectors.shape[1]}")
    return serialized_data


def save_index(data: Dict[str, Any], output_path: Path) -> str:
    """
    Save the skill index to disk in .npz format.
    
    Args:
        data: Dictionary containing vectors, task_ids, and metadata.
        output_path: Path to save the .npz file.
        
    Returns:
        SHA256 checksum of the saved file.
    """
    import numpy as np
    
    ensure_directories(output_path)
    
    # Extract components
    vectors = data["vectors"]
    task_ids = data["task_ids"]
    metadata = data["metadata"]
    
    # Save to .npz
    # Note: np.savez stores arrays and pickles objects. 
    # We store metadata as a pickled object to preserve structure.
    np.savez(
        output_path,
        vectors=vectors,
        task_ids=task_ids,
        metadata=metadata
    )
    
    # Compute checksum
    sha256_hash = hashlib.sha256()
    with open(output_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()
    
    logger.info(f"Saved skill index to {output_path} (checksum: {checksum[:16]}...)")
    return checksum


def main():
    """
    CLI entry point for building the skill vector database index.
    
    Usage:
        python src/retrieval/vector_db.py --input <path_to_weights.npz> --output <path_to_index.npz> --k <int>
    """
    parser = argparse.ArgumentParser(
        description="Build a skill vector database index from flattened LoRA weights."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input .npz file containing flattened and normalized LoRA vectors."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save the output skill index .npz file."
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of top neighbors to consider for retrieval (default: 5)."
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    logger.info(f"Starting index build: input={input_path}, output={output_path}, k={args.k}")
    
    try:
        # 1. Load flattened vectors
        metadata, vectors_list, task_ids = load_flattened_vectors(input_path)
        
        # Convert list of vectors to 2D array
        import numpy as np
        vectors_array = np.vstack(vectors_list)
        
        # 2. Prepare for serialization
        serialized_data = prepare_for_serialization(vectors_array, task_ids, metadata, args.k)
        
        # 3. Save index
        checksum = save_index(serialized_data, output_path)
        
        # 4. Verification
        if not output_path.exists():
            raise RuntimeError(f"Output file was not created: {output_path}")
        
        logger.info(f"SUCCESS: Index created at {output_path}")
        logger.info(f"Checksum: {checksum}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()