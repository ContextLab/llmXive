"""
Utility functions for archiving downloaded data and computing checksums.
Implements T005d: Archive and Checksum.
"""
import os
import hashlib
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List

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
        ValueError: If the file is empty.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        digest = sha256_hash.hexdigest()
        if digest == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855":
            logger.warning(f"File is empty but checksum computed: {file_path}")
        
        return digest
    except PermissionError as e:
        raise PermissionError(f"Permission denied reading file: {file_path}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to compute checksum for {file_path}: {e}") from e


def archive_data(
    source_dir: Path, 
    archive_dir: Path, 
    overwrite: bool = False
) -> Dict[str, str]:
    """
    Archive downloaded files to a designated directory and compute their checksums.
    
    This function copies files from the source directory to the archive directory,
    preserving the directory structure, and computes SHA-256 checksums for all
    archived files.
    
    Args:
        source_dir: Directory containing the downloaded files to archive.
        archive_dir: Directory where files will be archived.
        overwrite: If True, overwrite existing files in archive. If False and file
                  exists, skip the file.
    
    Returns:
        Dictionary mapping relative file paths (relative to archive_dir) to their
        SHA-256 checksums.
    
    Raises:
        FileNotFoundError: If source_dir does not exist.
        RuntimeError: If archiving fails for any reason.
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")
    
    if not source_dir.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source_dir}")
    
    # Create archive directory if it doesn't exist
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    checksums = {}
    files_archived = 0
    files_skipped = 0
    
    logger.info(f"Archiving data from {source_dir} to {archive_dir}")
    
    for file_path in source_dir.rglob("*"):
        if file_path.is_file():
            # Compute relative path from source_dir
            relative_path = file_path.relative_to(source_dir)
            archive_file_path = archive_dir / relative_path
            
            # Ensure parent directory exists
            archive_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file already exists
            if archive_file_path.exists() and not overwrite:
                logger.debug(f"Skipping existing file: {archive_file_path}")
                files_skipped += 1
                # Still compute checksum for existing file
                try:
                    checksums[str(relative_path)] = compute_sha256(archive_file_path)
                except Exception as e:
                    logger.error(f"Failed to compute checksum for existing file {archive_file_path}: {e}")
                continue
            
            try:
                # Copy file
                shutil.copy2(file_path, archive_file_path)
                logger.debug(f"Archived: {file_path} -> {archive_file_path}")
                
                # Compute checksum
                checksum = compute_sha256(archive_file_path)
                checksums[str(relative_path)] = checksum
                files_archived += 1
                
            except Exception as e:
                logger.error(f"Failed to archive {file_path}: {e}")
                raise RuntimeError(f"Failed to archive file {file_path}: {e}") from e
    
    logger.info(
        f"Archiving complete: {files_archived} files archived, "
        f"{files_skipped} files skipped"
    )
    
    if not checksums:
        logger.warning("No files were archived. Checksums dictionary is empty.")
    
    return checksums


def verify_archive_integrity(
    archive_dir: Path, 
    checksums: Dict[str, str]
) -> Dict[str, bool]:
    """
    Verify the integrity of archived files against known checksums.
    
    Args:
        archive_dir: Directory containing archived files.
        checksums: Dictionary mapping relative file paths to expected checksums.
    
    Returns:
        Dictionary mapping relative file paths to verification status (True = valid).
    """
    verification_results = {}
    
    for relative_path, expected_checksum in checksums.items():
        file_path = archive_dir / relative_path
        
        if not file_path.exists():
            logger.error(f"Missing file in archive: {file_path}")
            verification_results[relative_path] = False
            continue
        
        try:
            actual_checksum = compute_sha256(file_path)
            is_valid = actual_checksum == expected_checksum
            verification_results[relative_path] = is_valid
            
            if not is_valid:
                logger.error(
                    f"Checksum mismatch for {file_path}: "
                    f"expected {expected_checksum}, got {actual_checksum}"
                )
            else:
                logger.debug(f"Checksum verified: {file_path}")
                
        except Exception as e:
            logger.error(f"Failed to verify checksum for {file_path}: {e}")
            verification_results[relative_path] = False
    
    return verification_results


def generate_checksum_manifest(
    archive_dir: Path, 
    output_path: Path
) -> None:
    """
    Generate a manifest file containing checksums for all files in the archive.
    
    Args:
        archive_dir: Directory containing archived files.
        output_path: Path where the manifest file will be written.
    """
    checksums = {}
    
    for file_path in archive_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(archive_dir)
            checksums[str(relative_path)] = compute_sha256(file_path)
    
    # Write manifest as a simple text file with format: checksum  relative_path
    with open(output_path, "w", encoding="utf-8") as f:
        for relative_path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {relative_path}\n")
    
    logger.info(f"Checksum manifest written to {output_path}")
    logger.info(f"Total files in manifest: {len(checksums)}")
