"""
Lifecycle management retention hooks for configurable retention logic.

This module provides utilities for recording metadata and checking file ages
to support lifecycle management of pipeline artifacts.
"""
import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from loguru import logger

from code.utils.logger import setup_logger

# Initialize logger for this module
logger = setup_logger()


def check_file_age(file_path: Union[str, Path], age_threshold_seconds: float) -> bool:
    """
    Check if a file is older than the specified threshold.
    
    Args:
        file_path: Path to the file to check
        age_threshold_seconds: Age threshold in seconds
        
    Returns:
        True if the file is older than the threshold, False otherwise
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Get file modification time
    mtime = file_path.stat().st_mtime
    current_time = time.time()
    age_seconds = current_time - mtime
    
    is_old = age_seconds > age_threshold_seconds
    
    logger.info(
        f"File age check: {file_path.name} | Age: {age_seconds:.2f}s | "
        f"Threshold: {age_threshold_seconds}s | Result: {'OLD' if is_old else 'FRESH'}"
    )
    
    return is_old


def record_metadata(
    file_path: Union[str, Path],
    metadata: Dict[str, Any],
    output_manifest: Union[str, Path]
) -> None:
    """
    Record metadata for a file into a manifest.
    
    Args:
        file_path: Path to the file being recorded
        metadata: Additional metadata to record
        output_manifest: Path to the manifest file to update
    """
    file_path = Path(file_path)
    output_manifest = Path(output_manifest)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Prepare metadata entry
    file_stat = file_path.stat()
    entry = {
        "file_path": str(file_path),
        "file_name": file_path.name,
        "file_size_bytes": file_stat.st_size,
        "created_timestamp": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
        "modified_timestamp": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        "accessed_timestamp": datetime.fromtimestamp(file_stat.st_atime).isoformat(),
        "recorded_at": datetime.now().isoformat(),
        **metadata
    }
    
    # Load existing manifest or create new one
    manifest_data = {"entries": []}
    if output_manifest.exists():
        try:
            with open(output_manifest, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
                if "entries" not in manifest_data:
                    manifest_data["entries"] = []
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load existing manifest: {e}. Creating new one.")
    
    # Add new entry
    manifest_data["entries"].append(entry)
    
    # Write updated manifest
    with open(output_manifest, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Recorded metadata for {file_path.name} in {output_manifest}")


def get_file_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Retrieve metadata for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary containing file metadata
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_stat = file_path.stat()
    
    return {
        "file_path": str(file_path),
        "file_name": file_path.name,
        "file_size_bytes": file_stat.st_size,
        "created_timestamp": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
        "modified_timestamp": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        "accessed_timestamp": datetime.fromtimestamp(file_stat.st_atime).isoformat(),
        "age_seconds": time.time() - file_stat.st_mtime
    }


def list_files_by_age(
    directory: Union[str, Path],
    max_age_seconds: Optional[float] = None,
    min_age_seconds: Optional[float] = None,
    extensions: Optional[List[str]] = None
) -> List[Path]:
    """
    List files in a directory filtered by age and optionally by extension.
    
    Args:
        directory: Directory to search
        max_age_seconds: Maximum age in seconds (files must be younger than this)
        min_age_seconds: Minimum age in seconds (files must be older than this)
        extensions: List of file extensions to include (e.g., ['.fastq', '.bam'])
        
    Returns:
        List of Path objects matching the criteria
    """
    directory = Path(directory)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    
    matching_files = []
    
    for file_path in directory.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Filter by extension if specified
        if extensions is not None:
            if file_path.suffix not in extensions:
                continue
        
        # Get file age
        try:
            age_seconds = time.time() - file_path.stat().st_mtime
        except OSError:
            logger.warning(f"Could not access file: {file_path}")
            continue
        
        # Filter by age
        if max_age_seconds is not None and age_seconds > max_age_seconds:
            continue
        
        if min_age_seconds is not None and age_seconds < min_age_seconds:
            continue
        
        matching_files.append(file_path)
    
    logger.info(
        f"Found {len(matching_files)} files in {directory} "
        f"(max_age: {max_age_seconds}, min_age: {min_age_seconds})"
    )
    
    return matching_files


def main():
    """
    Main function demonstrating lifecycle management functionality.
    
    This function can be used to test the lifecycle hooks by:
    1. Creating a test directory with sample files
    2. Recording metadata for those files
    3. Checking file ages
    4. Listing files by age criteria
    """
    import tempfile
    import shutil
    
    # Create a temporary directory for testing
    test_dir = Path(tempfile.mkdtemp(prefix="lifecycle_test_"))
    manifest_path = test_dir / "lifecycle_manifest.json"
    
    try:
        logger.info(f"Testing lifecycle management in: {test_dir}")
        
        # Create some test files
        test_files = []
        for i in range(3):
            test_file = test_dir / f"test_file_{i}.txt"
            test_file.write_text(f"Test content {i}")
            # Sleep to create different timestamps
            time.sleep(0.1)
            test_files.append(test_file)
        
        # Record metadata for each file
        for i, file_path in enumerate(test_files):
            record_metadata(
                file_path=file_path,
                metadata={"test_id": f"test_{i}", "pipeline_step": "demo"},
                output_manifest=manifest_path
            )
        
        # Check file ages
        for file_path in test_files:
            is_old = check_file_age(file_path, age_threshold_seconds=1.0)
            logger.info(f"{file_path.name} is {'OLD' if is_old else 'FRESH'}")
        
        # List files by age
        fresh_files = list_files_by_age(test_dir, max_age_seconds=1.0, extensions=['.txt'])
        logger.info(f"Fresh files: {[f.name for f in fresh_files]}")
        
        # Display manifest contents
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
            logger.info(f"Manifest contains {len(manifest_data['entries'])} entries")
            
    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        logger.info(f"Cleaned up test directory: {test_dir}")


if __name__ == "__main__":
    main()
