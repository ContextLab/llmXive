"""
Script to execute T014b: Construct and save the static skill index.
Depends on T014a (vector_db.py logic) and T013 (flatten_lora.py outputs).
"""
import os
import sys
import logging
import time
import hashlib
from pathlib import Path

# Ensure code directory is in path
CODE_ROOT = Path(__file__).resolve().parent.parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from src.retrieval.vector_db import load_flattened_vectors, compute_index_structure, prepare_for_serialization, save_index

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(CODE_ROOT / "logs" / "t014b_execution.log")
    ]
)
logger = logging.getLogger(__name__)

def verify_file_integrity(file_path: Path) -> str:
    """Compute SHA256 hash of the output file for integrity verification."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    logger.info("Starting T014b: Constructing static skill index.")
    
    # Define paths relative to project root (code/ is parent of scripts/)
    project_root = CODE_ROOT.parent
    flattened_vectors_path = project_root / "data" / "processed" / "flattened_vectors.npz"
    output_path = project_root / "data" / "processed" / "skill_index.npz"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load flattened vectors (output from T013)
        logger.info(f"Loading flattened vectors from {flattened_vectors_path}")
        if not flattened_vectors_path.exists():
            raise FileNotFoundError(f"Required input file not found: {flattened_vectors_path}. "
                                    "Ensure T013 has been executed successfully.")
        
        vectors_data = load_flattened_vectors(flattened_vectors_path)
        logger.info(f"Loaded {len(vectors_data['vectors'])} vectors.")

        # 2. Compute index structure
        logger.info("Computing index structure...")
        index_data = compute_index_structure(vectors_data)
        
        # 3. Prepare for serialization (add metadata, ensure types)
        logger.info("Preparing index for serialization...")
        serialized_data = prepare_for_serialization(index_data, source_path=flattened_vectors_path)

        # 4. Save index
        logger.info(f"Saving index to {output_path}")
        save_index(serialized_data, output_path)

        # 5. Verify output
        if not output_path.exists():
            raise RuntimeError(f"Failed to create output file: {output_path}")
        
        file_size = output_path.stat().st_size
        checksum = verify_file_integrity(output_path)
        
        logger.info(f"SUCCESS: Index created at {output_path}")
        logger.info(f"  - File Size: {file_size / (1024*1024):.2f} MB")
        logger.info(f"  - SHA256: {checksum}")
        logger.info(f"  - Vectors Indexed: {serialized_data.get('metadata', {}).get('vector_count', 'N/A')}")

        return 0

    except Exception as e:
        logger.error(f"Execution failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
