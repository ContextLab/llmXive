"""
Script to execute T014b: Construct and save the static skill index.

This script orchestrates the loading of flattened vectors (from T013),
computes the index structure (from T014a), and saves the result to
data/processed/skill_index.npz.

It also verifies the file existence and integrity post-generation.
"""
import os
import sys
import logging
import time
import hashlib
from pathlib import Path

# Adjust path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.vector_db import load_flattened_vectors, compute_index_structure, prepare_for_serialization, save_index

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_file_integrity(file_path: Path) -> bool:
    """
    Verify the existence and basic integrity of the generated index file.
    
    Args:
        file_path: Path to the .npz file.
        
    Returns:
        True if file exists, is non-empty, and can be loaded.
    """
    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return False
    
    if file_path.stat().st_size == 0:
        logger.error(f"File is empty: {file_path}")
        return False

    try:
        import numpy as np
        data = np.load(file_path)
        logger.info(f"File loaded successfully. Keys: {list(data.keys())}")
        
        # Basic integrity check: ensure 'vectors' and 'metadata' exist and are not empty
        if 'vectors' not in data:
            logger.error("Missing 'vectors' key in index file.")
            return False
        if 'metadata' not in data:
            logger.error("Missing 'metadata' key in index file.")
            return False
        
        vectors = data['vectors']
        if vectors.size == 0:
            logger.error("Vectors array is empty.")
            return False

        logger.info(f"Integrity verified. Shape: {vectors.shape}, Size: {file_path.stat().st_size} bytes")
        return True
    except Exception as e:
        logger.error(f"Failed to load or verify file integrity: {e}")
        return False

def main():
    """Main execution entry point for T014b."""
    logger.info("Starting T014b: Constructing Skill Vector Index")
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    raw_data_dir = project_root / "data" / "raw"
    processed_data_dir = project_root / "data" / "processed"
    output_file = processed_data_dir / "skill_index.npz"

    # Ensure output directory exists
    processed_data_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load flattened vectors (Output from T013)
    # Expected input: data/raw/alfworld_weights.npz and data/raw/searchqa_weights.npz
    # The load_flattened_vectors function expects the directory containing these files
    logger.info(f"Loading flattened vectors from: {raw_data_dir}")
    
    try:
        vectors, metadata = load_flattened_vectors(raw_data_dir)
        if len(vectors) == 0:
            raise ValueError("No vectors loaded from raw data directory.")
        logger.info(f"Loaded {len(vectors)} vectors.")
    except Exception as e:
        logger.error(f"Failed to load flattened vectors: {e}")
        sys.exit(1)

    # 2. Compute index structure
    logger.info("Computing index structure...")
    index_data = compute_index_structure(vectors, metadata)

    # 3. Prepare for serialization
    logger.info("Preparing data for serialization...")
    serializable_data = prepare_for_serialization(index_data)

    # 4. Save index
    logger.info(f"Saving index to: {output_file}")
    try:
        save_index(serializable_data, output_file)
        logger.info("Index saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save index: {e}")
        sys.exit(1)

    # 5. Verify file existence and integrity
    logger.info("Verifying output file integrity...")
    if not verify_file_integrity(output_file):
        logger.error("Verification failed. Task T014b cannot be considered complete.")
        sys.exit(1)

    logger.info("T014b completed successfully. Index constructed and verified.")

if __name__ == "__main__":
    main()
