import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_path, ensure_dirs

# Setup logger
logger = logging.getLogger(__name__)

def compute_sha256_file(file_path: Path) -> str:
    """
    Compute SHA-256 checksum for a given file.
    
    Args:
        file_path: Path to the file to compute checksum for.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def load_existing_checksums(checksums_path: Path) -> Dict[str, Any]:
    """
    Load existing checksums from a JSON file.
    
    Args:
        checksums_path: Path to the checksums JSON file.
        
    Returns:
        Dictionary containing existing checksums, or empty dict if file doesn't exist.
    """
    if checksums_path.exists():
        with open(checksums_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"files": {}}

def save_checksums(checksums_path: Path, checksums: Dict[str, Any]) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums_path: Path to the checksums JSON file.
        checksums: Dictionary containing checksums to save.
    """
    ensure_dirs(checksums_path.parent)
    with open(checksums_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {checksums_path}")

def main() -> None:
    """
    Main entry point for T024c: Compute and record SHA-256 checksum for embeddings.npy.
    
    This task:
    1. Computes SHA-256 checksum for data/processed/embeddings.npy
    2. Records the checksum in data/processed/checksums.json
    3. Logs the operation
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get paths
    embeddings_path = get_path("data/processed/embeddings.npy")
    checksums_path = get_path("data/processed/checksums.json")
    
    logger.info(f"Computing checksum for: {embeddings_path}")
    
    try:
        # Verify file exists
        if not embeddings_path.exists():
            raise FileNotFoundError(
                f"Embeddings file not found: {embeddings_path}. "
                "Please ensure T024 has been completed successfully."
            )
        
        # Compute checksum
        checksum = compute_sha256_file(embeddings_path)
        logger.info(f"SHA-256 checksum computed: {checksum}")
        
        # Load existing checksums
        existing_checksums = load_existing_checksums(checksums_path)
        
        # Update checksums dictionary
        filename = embeddings_path.name
        existing_checksums["files"][filename] = {
            "sha256": checksum,
            "path": str(embeddings_path),
            "algorithm": "sha256"
        }
        
        # Also add metadata about the file
        file_size_bytes = embeddings_path.stat().st_size
        existing_checksums["files"][filename]["size_bytes"] = file_size_bytes
        
        # Save updated checksums
        save_checksums(checksums_path, existing_checksums)
        
        logger.info(f"Checksum recorded successfully for {filename}")
        logger.info(f"Checksums saved to: {checksums_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during checksum computation: {e}")
        raise

if __name__ == "__main__":
    main()
