"""
Cleanup intermediates script for User Story 1.

This script ensures intermediate files are cleaned up or compressed
to stay within the 7GB total directory size constraint (US1 Acceptance Scenario 1).

It is designed to be run after the preprocessing pipeline (T017) to:
1. Identify intermediate files (e.g., unnormalized NIfTI, temporary derivatives)
2. Compress large intermediate files using gzip
3. Delete unnecessary temporary files
4. Enforce the 7GB directory size limit
5. Log all actions and final directory size
"""
import os
import sys
import gzip
import shutil
import logging
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Import memory monitor to ensure we don't exceed limits during cleanup
# Note: We assume memory_monitor.py is available as per T007
try:
    from utils.memory_monitor import check_memory_limit
except ImportError:
    # Fallback if memory_monitor not available (should not happen in normal execution)
    def check_memory_limit():
        return True

# Configuration
DATA_ROOT = Path("data")
RAW_DIR = DATA_ROOT / "raw"
PROCESSED_DIR = DATA_ROOT / "processed"
MAX_SIZE_GB = 7.0
MAX_SIZE_BYTES = MAX_SIZE_GB * 1024**3

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DATA_ROOT / "cleanup_log.txt"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("cleanup_intermediates")

def get_directory_size(directory: Path) -> int:
    """
    Calculate the total size of a directory in bytes.
    
    Args:
        directory: Path to the directory to measure
        
    Returns:
        Total size in bytes
    """
    total_size = 0
    if not directory.exists():
        return 0
    
    for item in directory.rglob('*'):
        if item.is_file():
            total_size += item.stat().st_size
    return total_size

def get_large_files(directory: Path, min_size_mb: float = 100.0) -> List[Tuple[Path, int]]:
    """
    Find all files larger than a threshold in a directory.
    
    Args:
        directory: Path to search
        min_size_mb: Minimum file size in MB to consider
        
    Returns:
        List of (path, size_bytes) tuples for large files
    """
    threshold_bytes = min_size_mb * 1024**2
    large_files = []
    
    if not directory.exists():
        return large_files
        
    for item in directory.rglob('*'):
        if item.is_file() and item.stat().st_size > threshold_bytes:
            large_files.append((item, item.stat().st_size))
    
    # Sort by size descending
    large_files.sort(key=lambda x: x[1], reverse=True)
    return large_files

def compress_file(file_path: Path) -> bool:
    """
    Compress a file using gzip.
    
    Args:
        file_path: Path to the file to compress
        
    Returns:
        True if successful, False otherwise
    """
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return False
        
    compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
    
    try:
        # Check memory before compressing
        check_memory_limit()
        
        logger.info(f"Compressing: {file_path} -> {compressed_path}")
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Verify compression worked
        if compressed_path.exists() and compressed_path.stat().st_size < file_path.stat().st_size:
            # Remove original
            file_path.unlink()
            logger.info(f"Successfully compressed and removed original: {file_path}")
            return True
        else:
            logger.warning(f"Compression did not reduce size, keeping original: {file_path}")
            compressed_path.unlink()  # Remove the failed compression
            return False
            
    except Exception as e:
        logger.error(f"Failed to compress {file_path}: {str(e)}")
        if compressed_path.exists():
            compressed_path.unlink()
        return False

def remove_intermediate_file(file_path: Path) -> bool:
    """
    Remove an intermediate file.
    
    Args:
        file_path: Path to the file to remove
        
    Returns:
        True if successful, False otherwise
    """
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return False
        
    try:
        logger.info(f"Removing intermediate file: {file_path}")
        file_path.unlink()
        return True
    except Exception as e:
        logger.error(f"Failed to remove {file_path}: {str(e)}")
        return False

def identify_intermediate_files() -> List[Path]:
    """
    Identify intermediate files that should be cleaned up.
    
    This includes:
    - Temporary files from preprocessing (e.g., *_temp.nii.gz)
    - Unnormalized derivatives that are no longer needed
    - Log files from intermediate steps
    
    Returns:
        List of paths to intermediate files
    """
    intermediate_patterns = [
        "*_temp.nii.gz",
        "*_temp.nii",
        "*_tmp.nii.gz",
        "*_tmp.nii",
        "*_derivatives_temp.nii.gz",
        "*.log",
        "*.tmp"
    ]
    
    intermediate_files = []
    
    # Search in raw and processed directories
    for directory in [RAW_DIR, PROCESSED_DIR]:
        if not directory.exists():
            continue
            
        for pattern in intermediate_patterns:
            intermediate_files.extend(directory.rglob(pattern))
    
    return list(set(intermediate_files))  # Remove duplicates

def cleanup_pipeline() -> Dict:
    """
    Main cleanup function for the preprocessing pipeline.
    
    This function:
    1. Identifies intermediate files
    2. Compresses large intermediate files
    3. Removes unnecessary temporary files
    4. Enforces the 7GB size limit
    5. Logs all actions and final state
    
    Returns:
        Dictionary with cleanup statistics and results
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "actions": [],
        "files_compressed": 0,
        "files_deleted": 0,
        "space_saved_bytes": 0,
        "initial_size_bytes": 0,
        "final_size_bytes": 0,
        "size_limit_gb": MAX_SIZE_GB,
        "status": "success"
    }
    
    logger.info("Starting intermediate file cleanup...")
    
    # Record initial size
    results["initial_size_bytes"] = get_directory_size(DATA_ROOT)
    logger.info(f"Initial directory size: {results['initial_size_bytes'] / (1024**3):.2f} GB")
    
    # Identify intermediate files
    intermediate_files = identify_intermediate_files()
    logger.info(f"Found {len(intermediate_files)} intermediate files")
    
    # Process intermediate files
    for file_path in intermediate_files:
        original_size = file_path.stat().st_size if file_path.exists() else 0
        
        # Try to compress first if it's a NIfTI file
        if file_path.suffix in ['.nii', '.nii.gz'] and original_size > 100 * 1024**2:
            if compress_file(file_path):
                results["files_compressed"] += 1
                new_size = file_path.with_suffix(file_path.suffix + '.gz').stat().st_size if file_path.with_suffix(file_path.suffix + '.gz').exists() else 0
                results["space_saved_bytes"] += (original_size - new_size)
                results["actions"].append(f"Compressed: {file_path}")
            else:
                # If compression fails, try to delete
                if remove_intermediate_file(file_path):
                    results["files_deleted"] += 1
                    results["space_saved_bytes"] += original_size
                    results["actions"].append(f"Deleted: {file_path}")
        else:
            # Delete other intermediate files
            if remove_intermediate_file(file_path):
                results["files_deleted"] += 1
                results["space_saved_bytes"] += original_size
                results["actions"].append(f"Deleted: {file_path}")
    
    # Check if we're still over the limit
    final_size = get_directory_size(DATA_ROOT)
    results["final_size_bytes"] = final_size
    
    if final_size > MAX_SIZE_BYTES:
        logger.warning(f"Directory size {final_size / (1024**3):.2f} GB still exceeds limit of {MAX_SIZE_GB} GB")
        results["status"] = "warning"
        
        # Additional cleanup: compress large processed files if necessary
        logger.info("Attempting additional cleanup for large processed files...")
        large_files = get_large_files(PROCESSED_DIR, min_size_mb=500.0)
        
        for file_path, size in large_files[:5]:  # Limit to top 5 to avoid over-compression
            if file_path.suffix in ['.nii', '.nii.gz'] and not file_path.suffix.endswith('.gz'):
                if compress_file(file_path):
                    results["files_compressed"] += 1
                    results["space_saved_bytes"] += size
                    results["actions"].append(f"Compressed (additional): {file_path}")
                    
                    # Check size again
                    final_size = get_directory_size(DATA_ROOT)
                    if final_size <= MAX_SIZE_BYTES:
                        break
        
        results["final_size_bytes"] = get_directory_size(DATA_ROOT)
        if results["final_size_bytes"] > MAX_SIZE_BYTES:
            results["status"] = "failed"
            logger.error(f"Failed to reduce directory size below {MAX_SIZE_GB} GB")
    else:
        logger.info(f"Final directory size: {final_size / (1024**3):.2f} GB (within limit)")
    
    # Log summary
    logger.info(f"Cleanup complete:")
    logger.info(f"  Files compressed: {results['files_compressed']}")
    logger.info(f"  Files deleted: {results['files_deleted']}")
    logger.info(f"  Space saved: {results['space_saved_bytes'] / (1024**2):.2f} MB")
    logger.info(f"  Final size: {results['final_size_bytes'] / (1024**3):.2f} GB")
    logger.info(f"  Status: {results['status']}")
    
    return results

def main():
    """
    Main entry point for the cleanup script.
    """
    logger.info("Running intermediate file cleanup for preprocessing pipeline...")
    
    try:
        results = cleanup_pipeline()
        
        # Save results to JSON
        results_path = DATA_ROOT / "cleanup_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Cleanup results saved to: {results_path}")
        
        # Exit with appropriate code
        if results["status"] == "failed":
            sys.exit(1)
        elif results["status"] == "warning":
            sys.exit(0)  # Still successful but with warnings
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Cleanup failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()