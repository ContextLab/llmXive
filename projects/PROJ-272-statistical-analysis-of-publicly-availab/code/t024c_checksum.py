"""
Task T024c: Data Hygiene
Compute SHA-256 checksum for `data/processed/embeddings.npy` and record it in `data/processed/checksums.json`.
"""
import hashlib
import json
import logging
from pathlib import Path
from config import get_path

logger = logging.getLogger(__name__)

def compute_sha256_file(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def main():
    """Main entry point for T024c."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting T024c: Checksum Embeddings")
    
    embeddings_path = get_path("embeddings")
    checksum_output_path = get_path("checksums_processed")
    
    if not embeddings_path.exists():
        logger.error(f"Embeddings file not found: {embeddings_path}")
        logger.error("Please ensure T024 (feature extraction) has been completed.")
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")
    
    try:
        file_hash = compute_sha256_file(embeddings_path)
        checksums_data = {embeddings_path.name: file_hash}
        
        checksum_output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(checksum_output_path, "w", encoding="utf-8") as f:
            json.dump(checksums_data, f, indent=2)
        
        logger.info(f"Checksum saved for {embeddings_path.name}: {file_hash}")
        logger.info(f"Checksums saved to {checksum_output_path}")
    except Exception as e:
        logger.error(f"Failed to compute or save checksum: {e}")
        raise
    
    logger.info("T024c completed successfully.")

if __name__ == "__main__":
    main()