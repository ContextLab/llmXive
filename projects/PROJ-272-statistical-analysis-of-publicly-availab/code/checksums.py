import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

from config import get_path, ensure_dirs

# Configure logger
logger = logging.getLogger(__name__)

def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
            
    return sha256_hash.hexdigest()

def record_checksums(
    file_paths: list, 
    output_path: str, 
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Compute SHA-256 hashes for a list of files and record them in a JSON file.
    
    Args:
        file_paths: List of file paths to hash.
        output_path: Path to the output JSON file.
        overwrite: If True, overwrite existing checksum file.
        
    Returns:
        Dictionary containing the recorded checksums.
        
    Raises:
        ValueError: If no files are provided.
        FileExistsError: If output file exists and overwrite is False.
    """
    if not file_paths:
        raise ValueError("No file paths provided for checksum recording.")
        
    output_file = Path(output_path)
    
    # Load existing checksums if file exists and we aren't overwriting
    existing_checksums = {}
    if output_file.exists() and not overwrite:
        logger.info(f"Loading existing checksums from {output_path}")
        with open(output_file, "r", encoding="utf-8") as f:
            existing_checksums = json.load(f)
    
    results = {}
    for file_path in file_paths:
        if not Path(file_path).exists():
            logger.warning(f"Skipping non-existent file: {file_path}")
            continue
            
        try:
            file_hash = compute_sha256(file_path)
            # Use just the filename as the key, or full relative path if needed
            key = os.path.basename(file_path)
            results[key] = {
                "filename": key,
                "path": str(file_path),
                "sha256": file_hash
            }
            logger.info(f"Computed hash for {key}: {file_hash}")
        except Exception as e:
            logger.error(f"Failed to compute hash for {file_path}: {e}")
            raise
    
    # Merge with existing if not overwriting
    if not overwrite and existing_checksums:
        results = {**existing_checksums, **results}
        
    # Ensure output directory exists
    ensure_dirs(output_path)
    
    # Write results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Checksums recorded to {output_path}")
    return results

def main():
    """
    Main entry point for checksum recording.
    Reads the ADReSS dataset files (if they exist) and records their checksums.
    """
    # Setup logging
    from utils import setup_logging
    setup_logging()
    
    # Define the expected downloaded files based on T012
    # Typically ADReSS comes as a zip file containing the dataset
    data_dir = get_path("data_raw")
    
    # Look for common ADReSS archive names
    possible_files = [
        "ADReSS.zip",
        "ADReSS_challenge.zip",
        "adress_dataset.zip",
        "adress.zip"
    ]
    
    found_files = []
    for filename in possible_files:
        file_path = os.path.join(data_dir, filename)
        if os.path.exists(file_path):
            found_files.append(file_path)
            break # Assume the first match is the one we want
            
    if not found_files:
        # Check if there are any .zip files in the raw data directory
        zip_files = list(Path(data_dir).glob("*.zip"))
        if zip_files:
            found_files.append(str(zip_files[0]))
            logger.warning(f"No specific ADReSS filename found, using: {zip_files[0].name}")
        else:
            logger.error("No ADReSS archive found in data/raw. Run T012 first.")
            return

    output_path = os.path.join(data_dir, "checksums.json")
    
    try:
        record_checksums(found_files, output_path, overwrite=True)
        logger.info("Task T012e completed successfully.")
    except Exception as e:
        logger.error(f"Task T012e failed: {e}")
        raise

if __name__ == "__main__":
    main()
