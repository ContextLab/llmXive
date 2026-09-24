"""
Task T024c: Data Hygiene - Compute SHA-256 checksum for embeddings.npy
and record it in data/processed/checksums.json.
"""
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import logging setup from utils to ensure consistent logging
try:
    from utils import setup_logging, get_logger
except ImportError:
    # Fallback if utils is not fully ready, though it should be per completed tasks
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    def get_logger(name): return logging.getLogger(name)


def compute_sha256_file(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files (like embeddings.npy)
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def load_existing_checksums(checksum_file_path: Path) -> Dict[str, Any]:
    """
    Load existing checksums from a JSON file.
    
    Args:
        checksum_file_path: Path to the checksums JSON file.
        
    Returns:
        Dictionary of existing checksums.
    """
    if checksum_file_path.exists():
        try:
            with open(checksum_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Could not load existing checksums from {checksum_file_path}: {e}. Starting fresh.")
            return {"files": {}}
    return {"files": {}}


def save_checksums(checksums: Dict[str, Any], checksum_file_path: Path) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of checksums to save.
        checksum_file_path: Path to the output checksums JSON file.
    """
    checksum_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_file_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=4)
    logging.info(f"Checksums saved to {checksum_file_path}")


def main():
    """
    Main entry point for T024c.
    Computes SHA-256 for data/processed/embeddings.npy and updates data/processed/checksums.json.
    """
    logger = get_logger("T024c")
    logger.info("Starting Task T024c: Data Hygiene Checksum for Embeddings")

    # Define paths relative to project root
    # Assuming script runs from project root or we use absolute paths based on project structure
    project_root = Path(__file__).resolve().parent.parent
    embeddings_path = project_root / "data" / "processed" / "embeddings.npy"
    checksums_path = project_root / "data" / "processed" / "checksums.json"

    # Check if embeddings file exists (it should if T024 completed)
    if not embeddings_path.exists():
        logger.error(f"Critical: Required file not found: {embeddings_path}")
        logger.error("Task T024 (embeddings generation) must complete before T024c can run.")
        sys.exit(1)

    try:
        # 1. Compute SHA-256
        logger.info(f"Computing SHA-256 for {embeddings_path}...")
        sha256_hash = compute_sha256_file(embeddings_path)
        logger.info(f"SHA-256 computed: {sha256_hash}")

        # 2. Load existing checksums
        existing_checksums = load_existing_checksums(checksums_path)
        if "files" not in existing_checksums:
            existing_checksums["files"] = {}

        # 3. Update checksums dictionary
        file_key = "embeddings.npy"
        existing_checksums["files"][file_key] = {
            "sha256": sha256_hash,
            "path": str(embeddings_path.relative_to(project_root)),
            "algorithm": "sha256"
        }

        # Add metadata about when it was generated (optional but good practice)
        existing_checksums["metadata"] = {
            "generated_by": "T024c",
            "target_file": "embeddings.npy"
        }

        # 4. Save updated checksums
        save_checksums(existing_checksums, checksums_path)

        logger.info("Task T024c completed successfully.")

    except Exception as e:
        logger.error(f"Task T024c failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
