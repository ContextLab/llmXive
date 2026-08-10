import os
import sys
import logging
import time
import hashlib
from pathlib import Path

# Add project root to path if not present
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.retrieval.vector_db import main as vector_db_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_file_integrity(file_path: Path) -> bool:
    """
    Verify the existence and basic integrity of the generated index file.
    Checks:
    1. File exists
    2. File size > 0
    3. File is readable as npz (basic check)
    """
    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return False

    if file_path.stat().st_size == 0:
        logger.error(f"File is empty: {file_path}")
        return False

    try:
        import numpy as np
        # Attempt to load to verify format integrity
        data = np.load(file_path, allow_pickle=True)
        if 'vectors' not in data.files:
            logger.error(f"File missing required 'vectors' key: {file_path}")
            return False
        if 'metadata' not in data.files:
            logger.error(f"File missing required 'metadata' key: {file_path}")
            return False
        
        # Compute SHA256 for versioning
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        logger.info(f"Index file verified successfully: {file_path}")
        logger.info(f"  - Size: {file_path.stat().st_size / 1024 / 1024:.2f} MB")
        logger.info(f"  - Vector count: {len(data['vectors'])}")
        logger.info(f"  - SHA256: {sha256_hash.hexdigest()[:16]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to verify file integrity: {e}")
        return False

def main():
    """
    Executes the vector_db construction and verifies the output.
    """
    logger.info("Starting T014b: Executing vector_db construction...")
    start_time = time.time()

    try:
        # Execute the main logic from vector_db module
        # This function is responsible for loading flattened vectors,
        # computing the index structure, and saving to data/processed/skill_index.npz
        vector_db_main()
        
        elapsed = time.time() - start_time
        logger.info(f"Vector DB construction completed in {elapsed:.2f} seconds.")

        # Define expected output path
        output_path = project_root / "data" / "processed" / "skill_index.npz"
        
        # Verify the output
        if verify_file_integrity(output_path):
            logger.info("T014b: SUCCESS - Index constructed and verified.")
            return 0
        else:
            logger.error("T014b: FAILED - Index verification failed.")
            return 1

    except Exception as e:
        logger.exception(f"T014b: FAILED with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
