"""
Checksum generation for reproducibility (Constitution Principle V).

Generates SHA-256 checksums for all artifacts in data/raw/ and results/
directories and saves them to data/checksums_manifest.json.
"""
import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from config import DATA_DIR, RESULTS_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute checksum for {file_path}: {e}")
        raise


def collect_files(directory: Path, extensions: List[str] = None) -> List[Path]:
    """
    Recursively collect all files in a directory.
    
    Args:
        directory: Root directory to scan.
        extensions: Optional list of file extensions to filter (e.g., ['.csv', '.json']).
                    If None, all files are included.
                    
    Returns:
        List of Path objects for all files found.
    """
    files = []
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return files
    
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = Path(root) / filename
            if extensions is None or any(filename.endswith(ext) for ext in extensions):
                files.append(file_path)
    
    return sorted(files)


def generate_checksums_manifest(
    data_dir: Path = DATA_DIR,
    results_dir: Path = RESULTS_DIR,
    output_path: Path = None
) -> Dict[str, Any]:
    """
    Generate a manifest of checksums for all artifacts.
    
    Args:
        data_dir: Path to the data directory.
        results_dir: Path to the results directory.
        output_path: Path to save the manifest JSON. Defaults to data/checksums_manifest.json.
        
    Returns:
        Dictionary containing the manifest data.
    """
    if output_path is None:
        output_path = data_dir / "checksums_manifest.json"
        
    manifest = {
        "version": "1.0",
        "algorithm": "SHA-256",
        "files": []
    }
    
    # Collect files from data/raw/
    data_files = collect_files(data_dir / "raw")
    logger.info(f"Found {len(data_files)} files in {data_dir / 'raw'}")
    
    for file_path in data_files:
        checksum = compute_file_checksum(file_path)
        relative_path = file_path.relative_to(data_dir)
        manifest["files"].append({
            "path": str(relative_path),
            "checksum": checksum,
            "size_bytes": file_path.stat().st_size
        })
    
    # Collect files from results/
    results_files = collect_files(results_dir)
    logger.info(f"Found {len(results_files)} files in {results_dir}")
    
    for file_path in results_files:
        checksum = compute_file_checksum(file_path)
        relative_path = file_path.relative_to(results_dir)
        manifest["files"].append({
            "path": f"results/{relative_path}",
            "checksum": checksum,
            "size_bytes": file_path.stat().st_size
        })
    
    # Sort files by path for reproducibility
    manifest["files"].sort(key=lambda x: x["path"])
    
    # Save manifest
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"Checksum manifest saved to {output_path}")
    logger.info(f"Total files checksummed: {len(manifest['files'])}")
    
    return manifest


def verify_checksums(
    manifest_path: Path = None,
    data_dir: Path = DATA_DIR,
    results_dir: Path = RESULTS_DIR
) -> bool:
    """
    Verify checksums against a manifest.
    
    Args:
        manifest_path: Path to the manifest JSON. Defaults to data/checksums_manifest.json.
        data_dir: Path to the data directory.
        results_dir: Path to the results directory.
        
    Returns:
        True if all checksums match, False otherwise.
    """
    if manifest_path is None:
        manifest_path = data_dir / "checksums_manifest.json"
        
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return False
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    all_valid = True
    for file_entry in manifest["files"]:
        file_path_str = file_entry["path"]
        expected_checksum = file_entry["checksum"]
        
        # Determine actual path based on prefix
        if file_path_str.startswith("results/"):
            actual_path = results_dir / file_path_str.replace("results/", "", 1)
        else:
            actual_path = data_dir / file_path_str
            
        if not actual_path.exists():
            logger.error(f"File missing: {actual_path}")
            all_valid = False
            continue
            
        actual_checksum = compute_file_checksum(actual_path)
        
        if actual_checksum != expected_checksum:
            logger.error(f"Checksum mismatch for {actual_path}: expected {expected_checksum}, got {actual_checksum}")
            all_valid = False
        else:
            logger.debug(f"Checksum verified: {actual_path}")
            
    if all_valid:
        logger.info("All checksums verified successfully!")
    else:
        logger.error("Checksum verification failed!")
        
    return all_valid


def run_checksum_generation():
    """Main entry point for checksum generation."""
    logger.info("Starting checksum generation...")
    try:
        manifest = generate_checksums_manifest()
        logger.info("Checksum generation completed successfully.")
        return manifest
    except Exception as e:
        logger.error(f"Checksum generation failed: {e}")
        raise


if __name__ == "__main__":
    run_checksum_generation()
