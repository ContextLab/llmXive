import os
import hashlib
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there is an error reading the file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def archive_data(source_dir: Path, archive_dir: Path, overwrite: bool = False) -> Dict[str, Any]:
    """
    Copy files from source directory to archive directory unchanged.
    
    Args:
        source_dir: Path to the source directory containing raw data.
        archive_dir: Path to the archive directory.
        overwrite: If True, overwrite existing files in archive. Default is False.
        
    Returns:
        Dictionary with 'status' (success/fail) and 'files_archived' count.
        
    Raises:
        FileNotFoundError: If source directory does not exist.
        RuntimeError: If archive fails due to permission or other issues.
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    
    if not source_dir.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source_dir}")
    
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    files_archived = 0
    errors = []
    
    for item in source_dir.rglob("*"):
        if item.is_file():
            relative_path = item.relative_to(source_dir)
            dest_path = archive_dir / relative_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                if dest_path.exists() and not overwrite:
                    logger.warning(f"Skipping existing file: {dest_path}")
                    continue
                shutil.copy2(item, dest_path)
                files_archived += 1
                logger.info(f"Archived: {item} -> {dest_path}")
            except Exception as e:
                error_msg = f"Failed to archive {item}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
    
    if errors:
        logger.error(f"Archiving completed with {len(errors)} errors.")
        return {"status": "partial_success", "files_archived": files_archived, "errors": errors}
    
    logger.info(f"Successfully archived {files_archived} files.")
    return {"status": "success", "files_archived": files_archived}

def verify_archive_integrity(archive_dir: Path, checksums: Dict[str, str]) -> bool:
    """
    Verify the integrity of archived files against provided checksums.
    
    Args:
        archive_dir: Path to the archive directory.
        checksums: Dictionary mapping relative file paths to expected SHA-256 hashes.
        
    Returns:
        True if all files match their checksums, False otherwise.
    """
    all_valid = True
    for rel_path, expected_hash in checksums.items():
        file_path = archive_dir / rel_path
        if not file_path.exists():
            logger.error(f"Missing file in archive: {file_path}")
            all_valid = False
            continue
        
        actual_hash = compute_sha256(file_path)
        if actual_hash != expected_hash:
            logger.error(f"Checksum mismatch for {file_path}: expected {expected_hash}, got {actual_hash}")
            all_valid = False
        else:
            logger.debug(f"Checksum verified for {file_path}")
    
    return all_valid

def generate_checksum_manifest(archive_dir: Path, output_path: Path) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for all files in the archive and write to a manifest file.
    
    Args:
        archive_dir: Path to the archive directory.
        output_path: Path to write the checksum manifest (JSON).
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    checksums = {}
    for item in archive_dir.rglob("*"):
        if item.is_file():
            relative_path = str(item.relative_to(archive_dir))
            try:
                checksum = compute_sha256(item)
                checksums[relative_path] = checksum
                logger.info(f"Computed checksum for {relative_path}: {checksum}")
            except Exception as e:
                logger.error(f"Failed to compute checksum for {item}: {e}")
    
    # Write manifest
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Checksum manifest written to {output_path}")
    return checksums

def run_archive_pipeline(source_dir: Path, archive_dir: Path, output_manifest_path: Path) -> Dict[str, Any]:
    """
    Execute the full archiving pipeline: archive files and generate checksum manifest.
    
    Args:
        source_dir: Source directory containing raw data files.
        archive_dir: Destination archive directory.
        output_manifest_path: Path for the checksum manifest file.
        
    Returns:
        Dictionary with pipeline execution results.
    """
    logger.info(f"Starting archive pipeline: {source_dir} -> {archive_dir}")
    
    # Archive data
    archive_result = archive_data(source_dir, archive_dir, overwrite=True)
    
    # Generate checksums
    if archive_result["status"] in ["success", "partial_success"]:
        checksums = generate_checksum_manifest(archive_dir, output_manifest_path)
        archive_result["checksums_file"] = str(output_manifest_path)
        archive_result["total_checksums"] = len(checksums)
    else:
        archive_result["checksums_file"] = None
        archive_result["total_checksums"] = 0
    
    return archive_result

def main():
    """
    Main entry point for the archive pipeline script.
    Expects source_dir, archive_dir, and manifest_path as arguments or config.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Archive raw data and generate checksums.")
    parser.add_argument("--source", type=str, required=True, help="Source directory path")
    parser.add_argument("--archive", type=str, required=True, help="Archive directory path")
    parser.add_argument("--manifest", type=str, required=True, help="Output manifest file path")
    args = parser.parse_args()
    
    source_dir = Path(args.source)
    archive_dir = Path(args.archive)
    manifest_path = Path(args.manifest)
    
    result = run_archive_pipeline(source_dir, archive_dir, manifest_path)
    print(f"Archive Pipeline Result: {result}")
    
    if result["status"] == "success":
        return 0
    else:
        return 1

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    exit(main())
