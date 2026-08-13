"""
Vector DB construction for Skill Vector Database (US1).
Loads flattened LoRA vectors, computes index structure, serializes to disk.
"""
import os
import sys
import logging
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np

from src.utils.config import get_project_root, get_data_path, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_flattened_vectors(data_dir: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load flattened LoRA vectors from data/raw/ and combine into a single index.
    
    Expects:
      - data/raw/alfworld_weights.npz
      - data/raw/searchqa_weights.npz
    
    Returns:
      - vectors: np.ndarray of shape (N, D) where N is total adapters, D is flattened dim
      - metadata: dict with task_desc, source, original_shape for each vector
    """
    weights_files = {
        "alfworld": data_dir / "alfworld_weights.npz",
        "searchqa": data_dir / "searchqa_weights.npz"
    }
    
    all_vectors = []
    all_metadata = {
        "task_desc": [],
        "source": [],
        "original_shape": []
    }
    
    for source_name, weights_path in weights_files.items():
        if not weights_path.exists():
            logger.error(f"Required weights file missing: {weights_path}")
            raise FileNotFoundError(f"Missing weights file: {weights_path}")
        
        logger.info(f"Loading {source_name} weights from {weights_path}")
        data = np.load(weights_path)
        
        # Expected keys: 'A' and 'B' matrices
        if 'A' not in data or 'B' not in data:
            raise ValueError(f"Invalid weights format in {weights_path}: missing A or B keys")
        
        A = data['A']
        B = data['B']
        
        # Flatten A and B, concatenate
        A_flat = A.flatten()
        B_flat = B.flatten()
        combined = np.concatenate([A_flat, B_flat])
        
        # L2 normalize
        norm = np.linalg.norm(combined)
        if norm == 0:
            logger.warning(f"Zero norm vector for {source_name}, skipping")
            continue
        
        normalized = combined / norm
        
        all_vectors.append(normalized)
        all_metadata["task_desc"].append(f"LoRA adapter for {source_name}")
        all_metadata["source"].append(source_name)
        all_metadata["original_shape"].append({"A": A.shape, "B": B.shape})
        
        logger.info(f"Loaded {source_name}: A={A.shape}, B={B.shape}, flattened={combined.shape}")
    
    if not all_vectors:
        raise ValueError("No valid vectors loaded from weights files")
    
    vectors = np.vstack(all_vectors)
    logger.info(f"Combined index shape: {vectors.shape}")
    
    return vectors, all_metadata


def compute_index_structure(vectors: np.ndarray, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute structural information about the index for validation and debugging.
    """
    n_samples, dim = vectors.shape
    
    structure = {
        "n_samples": n_samples,
        "dimension": dim,
        "dtype": str(vectors.dtype),
        "metadata_keys": list(metadata.keys()),
        "sample_metadata": {
            k: v[0] if isinstance(v, list) and len(v) > 0 else v 
            for k, v in metadata.items()
        },
        "norms": np.linalg.norm(vectors, axis=1).tolist()
    }
    
    # Verify L2 normalization (should be ~1.0)
    max_norm_deviation = max(abs(n - 1.0) for n in structure["norms"])
    structure["max_norm_deviation"] = max_norm_deviation
    
    logger.info(f"Index structure computed: {n_samples} samples, dim={dim}")
    logger.info(f"Max norm deviation from 1.0: {max_norm_deviation:.2e}")
    
    if max_norm_deviation > 1e-5:
        logger.warning(f"Norm deviation {max_norm_deviation} exceeds tolerance")
    
    return structure


def prepare_for_serialization(vectors: np.ndarray, metadata: Dict[str, Any], structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare the complete index package for serialization.
    """
    package = {
        "vectors": vectors,
        "metadata": metadata,
        "structure": structure,
        "version": "1.0",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Validate data types
    if not np.issubdtype(vectors.dtype, np.floating):
        logger.warning(f"Vectors dtype {vectors.dtype} is not floating point")
    
    # Check for NaN/Inf
    if np.any(np.isnan(vectors)) or np.any(np.isinf(vectors)):
        raise ValueError("Vectors contain NaN or Inf values")
    
    logger.info("Index package prepared for serialization")
    return package


def save_index(package: Dict[str, Any], output_path: Path) -> Dict[str, Any]:
    """
    Save the index to disk as .npz and compute checksum.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as npz
    np.savez_compressed(
        output_path,
        vectors=package["vectors"],
        task_desc=package["metadata"]["task_desc"],
        source=package["metadata"]["source"],
        original_shape=np.array(package["metadata"]["original_shape"], dtype=object)
    )
    
    # Compute checksum
    checksum = hashlib.sha256()
    with open(output_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            checksum.update(chunk)
    
    file_size = output_path.stat().st_size
    
    result = {
        "path": str(output_path),
        "exists": True,
        "size_bytes": file_size,
        "checksum_sha256": checksum.hexdigest(),
        "vectors_shape": package["vectors"].shape,
        "dtype": str(package["vectors"].dtype),
        "n_samples": package["structure"]["n_samples"],
        "dimension": package["structure"]["dimension"]
    }
    
    logger.info(f"Index saved to {output_path}")
    logger.info(f"Checksum: {result['checksum_sha256']}")
    logger.info(f"Size: {file_size} bytes")
    
    return result


def main():
    """
    Main entry point for T014d: Construct and save the static skill index.
    """
    start_time = time.time()
    
    project_root = get_project_root()
    data_dir = get_data_path(project_root)
    processed_dir = project_root / "data" / "processed"
    
    ensure_directories(project_root)
    
    input_weights_dir = data_dir / "raw"
    output_path = processed_dir / "skill_index.npz"
    
    logger.info("=" * 60)
    logger.info("T014d: Constructing Skill Vector Database Index")
    logger.info("=" * 60)
    logger.info(f"Input weights dir: {input_weights_dir}")
    logger.info(f"Output path: {output_path}")
    
    try:
        # Step 1: Load flattened vectors
        vectors, metadata = load_flattened_vectors(input_weights_dir)
        
        # Step 2: Compute index structure
        structure = compute_index_structure(vectors, metadata)
        
        # Step 3: Prepare for serialization
        package = prepare_for_serialization(vectors, metadata, structure)
        
        # Step 4: Save index and verify
        save_result = save_index(package, output_path)
        
        # Step 5: Verification
        if not output_path.exists():
            raise RuntimeError(f"Output file was not created: {output_path}")
        
        # Validate data type compatibility
        loaded = np.load(output_path)
        if "vectors" not in loaded:
            raise RuntimeError("Saved index missing 'vectors' key")
        
        loaded_vectors = loaded["vectors"]
        if loaded_vectors.dtype != vectors.dtype:
            logger.warning(f"Loaded dtype {loaded_vectors.dtype} differs from original {vectors.dtype}")
        
        # Verify checksum
        checksum = hashlib.sha256()
        with open(output_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                checksum.update(chunk)
        
        if checksum.hexdigest() != save_result["checksum_sha256"]:
            raise RuntimeError("Checksum mismatch after save")
        
        elapsed = time.time() - start_time
        
        logger.info("=" * 60)
        logger.info("T014d COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Output file: {output_path}")
        logger.info(f"Checksum: {save_result['checksum_sha256']}")
        logger.info(f"Shape: {save_result['vectors_shape']}")
        logger.info(f"Dtype: {save_result['dtype']}")
        logger.info(f"Samples: {save_result['n_samples']}")
        logger.info(f"Dimension: {save_result['dimension']}")
        logger.info(f"Elapsed time: {elapsed:.2f}s")
        
        # Return summary for programmatic access
        return {
            "status": "success",
            "output_path": str(output_path),
            "checksum": save_result["checksum_sha256"],
            "shape": save_result["vectors_shape"],
            "dtype": save_result["dtype"],
            "n_samples": save_result["n_samples"],
            "dimension": save_result["dimension"],
            "elapsed_seconds": elapsed
        }
        
    except Exception as e:
        logger.error(f"T014d FAILED: {str(e)}", exc_info=True)
        elapsed = time.time() - start_time
        return {
            "status": "failed",
            "error": str(e),
            "elapsed_seconds": elapsed
        }


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result["status"] == "success" else 1)
