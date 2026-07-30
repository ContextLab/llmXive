"""
Data Integrity Module for Project PROJ-263
Implements checksum generation and verification for raw data (Principle III).
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
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
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"IO Error reading {file_path}: {e}")
        raise

def generate_checksums_for_raw_data(raw_data_dir: Path) -> Dict[str, str]:
    """
    Generate checksums for all files in the raw data directory.
    
    Args:
        raw_data_dir: Path to the directory containing raw data files.
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums.
        
    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    if not raw_data_dir.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {raw_data_dir}")
    
    checksums = {}
    file_count = 0
    
    for file_path in raw_data_dir.rglob("*"):
        if file_path.is_file():
            # Use relative path from raw_data_dir for portability
            relative_path = str(file_path.relative_to(raw_data_dir))
            try:
                checksum = compute_file_sha256(file_path)
                checksums[relative_path] = checksum
                file_count += 1
                logger.info(f"Computed checksum for: {relative_path}")
            except Exception as e:
                logger.error(f"Failed to compute checksum for {relative_path}: {e}")
    
    logger.info(f"Generated checksums for {file_count} files.")
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of file paths to checksums.
        output_path: Path where the JSON file will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "algorithm": "sha256",
        "generated_at": None,  # Will be set by caller if needed
        "checksums": checksums
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Checksums saved to: {output_path}")

def verify_checksums(raw_data_dir: Path, checksums_path: Path) -> Dict[str, bool]:
    """
    Verify file integrity against stored checksums.
    
    Args:
        raw_data_dir: Path to the raw data directory.
        checksums_path: Path to the JSON file containing checksums.
        
    Returns:
        Dictionary mapping file paths to verification status (True/False).
    """
    if not checksums_path.exists():
        raise FileNotFoundError(f"Checksums file not found: {checksums_path}")
    
    with open(checksums_path, "r", encoding="utf-8") as f:
        stored_data = json.load(f)
    
    stored_checksums = stored_data.get("checksums", {})
    results = {}
    
    for relative_path, expected_checksum in stored_checksums.items():
        file_path = raw_data_dir / relative_path
        if not file_path.exists():
            results[relative_path] = False
            logger.warning(f"File missing during verification: {relative_path}")
            continue
        
        try:
            actual_checksum = compute_file_sha256(file_path)
            is_valid = actual_checksum == expected_checksum
            results[relative_path] = is_valid
            status = "VALID" if is_valid else "INVALID"
            logger.info(f"Verification {status}: {relative_path}")
        except Exception as e:
            results[relative_path] = False
            logger.error(f"Verification failed for {relative_path}: {e}")
    
    return results

def main():
    """
    Main entry point for checksum generation and verification workflow.
    Expects environment variables or defaults to standard paths.
    """
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    raw_data_dir = project_root / "data" / "raw"
    checksums_output_path = project_root / "data" / "processed" / "data_checksums.json"
    
    # Allow override via command line args (simple implementation)
    import argparse
    parser = argparse.ArgumentParser(description="Generate or verify data checksums.")
    parser.add_argument("--verify", action="store_true", help="Verify checksums instead of generating")
    parser.add_argument("--raw-dir", type=str, help="Path to raw data directory")
    parser.add_argument("--checksums-file", type=str, help="Path to checksums file (for verification)")
    args = parser.parse_args()
    
    if args.raw_dir:
        raw_data_dir = Path(args.raw_dir)
    if args.checksums_file:
        checksums_output_path = Path(args.checksums_file)
    
    try:
        if args.verify:
            logger.info("Starting checksum verification...")
            results = verify_checksums(raw_data_dir, checksums_output_path)
            all_valid = all(results.values())
            if all_valid:
                logger.info("All checksums verified successfully.")
                return 0
            else:
                logger.error("Checksum verification failed for some files.")
                return 1
        else:
            logger.info("Starting checksum generation for raw data...")
            checksums = generate_checksums_for_raw_data(raw_data_dir)
            if not checksums:
                logger.warning("No files found to checksum in the raw data directory.")
                return 0
            save_checksums(checksums, checksums_output_path)
            logger.info("Checksum generation completed successfully.")
            return 0
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
