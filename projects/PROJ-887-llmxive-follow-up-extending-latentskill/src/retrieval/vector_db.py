"""
Vector Database Module for LatentSkill Indexing.

Implements FR-001: Load flattened vectors from T013, compute the index structure,
and prepare data for serialization.
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

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FLATTENED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_INDEX_PATH = PROJECT_ROOT / "data" / "processed" / "skill_index.npz"


def load_flattened_vectors(input_dir: Optional[Path] = None) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    """
    Load flattened vectors from the processed directory.
    
    Expects .npz files containing 'A' and 'B' matrices that have been flattened
    and normalized by T013 (flatten_lora.py).
    
    Args:
        input_dir: Directory containing flattened vector files. Defaults to data/processed/.
        
    Returns:
        Tuple of (vectors_dict, metadata_dict):
            - vectors_dict: {task_id: flattened_vector}
            - metadata_dict: {task_id: {original_shape, normalization_factor, ...}}
    """
    if input_dir is None:
        input_dir = FLATTENED_DATA_DIR
        
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    vectors = {}
    metadata = {}
    
    logger.info(f"Loading flattened vectors from {input_dir}")
    start_time = time.time()
    
    npz_files = list(input_dir.glob("*.npz"))
    
    if not npz_files:
        raise FileNotFoundError(f"No .npz files found in {input_dir}")
        
    logger.info(f"Found {len(npz_files)} .npz files")
    
    for file_path in npz_files:
        try:
            data = np.load(file_path)
            
            # Extract task ID from filename
            task_id = file_path.stem
            
            # Expect 'vector' key from flatten_lora.py
            if 'vector' not in data:
                logger.warning(f"Skipping {file_path}: missing 'vector' key")
                continue
                
            vector = data['vector']
            
            # Validate vector
            if not isinstance(vector, np.ndarray):
                logger.warning(f"Skipping {file_path}: 'vector' is not an ndarray")
                continue
                
            if np.any(np.isnan(vector)) or np.any(np.isinf(vector)):
                logger.warning(f"Skipping {file_path}: vector contains NaN or Inf")
                continue
                
            vectors[task_id] = vector
            
            # Store metadata
            metadata[task_id] = {
                'file_path': str(file_path),
                'original_shape': data.get('original_shape', None),
                'normalization': data.get('normalization', 'L2'),
                'vector_size': len(vector)
            }
            
            logger.debug(f"Loaded {task_id}: shape={vector.shape}")
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            continue
    
    elapsed = time.time() - start_time
    logger.info(f"Loaded {len(vectors)} vectors in {elapsed:.2f}s")
    
    if len(vectors) == 0:
        raise ValueError("No valid vectors loaded. Check input files.")
        
    return vectors, metadata


def compute_index_structure(vectors: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Compute the index structure from the loaded vectors.
    
    Creates a consolidated structure containing:
    - All vectors concatenated into a single matrix
    - Mapping from vector index to task ID
    - Statistical summaries (min, max, mean, std)
    
    Args:
        vectors: Dictionary of {task_id: vector}
        
    Returns:
        Index structure dictionary containing:
            - 'vectors_matrix': np.ndarray of shape (n_tasks, vector_dim)
            - 'task_mapping': List of task_ids in order
            - 'statistics': Dict of statistical measures
            - 'index_created_at': Timestamp
    """
    logger.info("Computing index structure")
    start_time = time.time()
    
    if not vectors:
        raise ValueError("Cannot compute index from empty vector dictionary")
        
    # Validate consistent dimensions
    vector_dims = [len(v) for v in vectors.values()]
    unique_dims = set(vector_dims)
    
    if len(unique_dims) > 1:
        raise ValueError(f"Inconsistent vector dimensions found: {unique_dims}")
        
    vector_dim = vector_dims[0]
    n_tasks = len(vectors)
    
    logger.info(f"Building index for {n_tasks} tasks, dimension {vector_dim}")
    
    # Sort task IDs for deterministic ordering
    task_ids = sorted(vectors.keys())
    
    # Create matrix
    vectors_matrix = np.zeros((n_tasks, vector_dim), dtype=np.float32)
    
    for idx, task_id in enumerate(task_ids):
        vectors_matrix[idx] = vectors[task_id].astype(np.float32)
    
    # Compute statistics
    stats = {
        'n_tasks': n_tasks,
        'vector_dim': vector_dim,
        'total_elements': n_tasks * vector_dim,
        'matrix_min': float(np.min(vectors_matrix)),
        'matrix_max': float(np.max(vectors_matrix)),
        'matrix_mean': float(np.mean(vectors_matrix)),
        'matrix_std': float(np.std(vectors_matrix)),
        'vector_mins': [float(np.min(vectors[task_id])) for task_id in task_ids],
        'vector_maxs': [float(np.max(vectors[task_id])) for task_id in task_ids],
    }
    
    index_structure = {
        'vectors_matrix': vectors_matrix,
        'task_mapping': task_ids,
        'statistics': stats,
        'index_created_at': time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    elapsed = time.time() - start_time
    logger.info(f"Index structure computed in {elapsed:.2f}s")
    logger.info(f"  Tasks: {n_tasks}, Dim: {vector_dim}, Matrix shape: {vectors_matrix.shape}")
    
    return index_structure


def prepare_for_serialization(index_structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare the index structure for serialization.
    
    Converts numpy arrays to serializable formats and ensures all data
    is ready for saving to disk.
    
    Args:
        index_structure: The computed index structure from compute_index_structure()
        
    Returns:
        Prepared dictionary ready for np.savez()
    """
    logger.info("Preparing index for serialization")
    
    prepared = {
        'vectors_matrix': index_structure['vectors_matrix'],
        'task_mapping': np.array(index_structure['task_mapping'], dtype=object),
        'statistics': {
            'n_tasks': index_structure['statistics']['n_tasks'],
            'vector_dim': index_structure['statistics']['vector_dim'],
            'total_elements': index_structure['statistics']['total_elements'],
            'matrix_min': index_structure['statistics']['matrix_min'],
            'matrix_max': index_structure['statistics']['matrix_max'],
            'matrix_mean': index_structure['statistics']['matrix_mean'],
            'matrix_std': index_structure['statistics']['matrix_std'],
        },
        'index_created_at': index_structure['index_created_at'],
    }
    
    # Log summary
    stats = prepared['statistics']
    logger.info(f"Prepared index: {stats['n_tasks']} tasks, {stats['vector_dim']} dimensions")
    logger.info(f"  Value range: [{stats['matrix_min']:.4f}, {stats['matrix_max']:.4f}]")
    
    return prepared


def save_index(prepared_index: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the prepared index to disk.
    
    Args:
        prepared_index: The prepared index dictionary
        output_path: Path to save the index. Defaults to data/processed/skill_index.npz
        
    Returns:
        Path to the saved file
    """
    if output_path is None:
        output_path = OUTPUT_INDEX_PATH
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving index to {output_path}")
    start_time = time.time()
    
    # Save using np.savez (compressed)
    np.savez_compressed(
        output_path,
        vectors_matrix=prepared_index['vectors_matrix'],
        task_mapping=prepared_index['task_mapping'],
        n_tasks=prepared_index['statistics']['n_tasks'],
        vector_dim=prepared_index['statistics']['vector_dim'],
        total_elements=prepared_index['statistics']['total_elements'],
        matrix_min=prepared_index['statistics']['matrix_min'],
        matrix_max=prepared_index['statistics']['matrix_max'],
        matrix_mean=prepared_index['statistics']['matrix_mean'],
        matrix_std=prepared_index['statistics']['matrix_std'],
        index_created_at=prepared_index['index_created_at'],
    )
    
    elapsed = time.time() - start_time
    file_size = output_path.stat().st_size
    
    logger.info(f"Index saved in {elapsed:.2f}s, size: {file_size / 1024:.2f} KB")
    
    return output_path


def main():
    """
    Main entry point for constructing the skill index.
    
    This function orchestrates the full pipeline:
    1. Load flattened vectors from data/processed/
    2. Compute the index structure
    3. Prepare for serialization
    4. Save to data/processed/skill_index.npz
    """
    logger.info("=" * 60)
    logger.info("Starting Vector DB Index Construction (T014a)")
    logger.info("=" * 60)
    
    total_start = time.time()
    
    try:
        # Step 1: Load flattened vectors
        vectors, metadata = load_flattened_vectors()
        
        # Step 2: Compute index structure
        index_structure = compute_index_structure(vectors)
        
        # Step 3: Prepare for serialization
        prepared_index = prepare_for_serialization(index_structure)
        
        # Step 4: Save index
        output_path = save_index(prepared_index)
        
        # Verify file exists
        if not output_path.exists():
            raise RuntimeError(f"Failed to create index file: {output_path}")
            
        total_elapsed = time.time() - total_start
        
        logger.info("=" * 60)
        logger.info(f"SUCCESS: Index constructed and saved to {output_path}")
        logger.info(f"Total time: {total_elapsed:.2f}s")
        logger.info(f"Tasks indexed: {len(vectors)}")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"ERROR: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())