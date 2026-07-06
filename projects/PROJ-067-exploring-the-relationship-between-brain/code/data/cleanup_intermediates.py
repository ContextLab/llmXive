"""
Task T021: Ensure intermediate files are cleaned up or compressed to stay within 7GB total directory size.

This script scans the data/ directory for large intermediate files (e.g., raw NIfTI, 
temporary processing files, uncompressed derivatives) and either removes them or 
compresses them using gzip to reduce disk footprint.

It respects the 7GB directory size constraint specified in US1 Acceptance Scenario 1.
"""
import os
import sys
import gzip
import shutil
import logging
import json
from pathlib import Path
from typing import List, Tuple, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/cleanup.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MAX_SIZE_BYTES = 7 * 1024 * 1024 * 1024  # 7GB
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB
INTERMEDIATE_EXTENSIONS = ['.nii', '.nii.gz', '.tmp', '.bak', '.log']
COMPRESSIBLE_EXTENSIONS = ['.nii', '.log']  # .nii.gz is already compressed

def get_directory_size(path: Path) -> int:
    """Calculate total size of a directory in bytes."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            if filepath.exists():
                total_size += filepath.stat().st_size
    return total_size

def get_large_files(directory: Path, threshold: int = LARGE_FILE_THRESHOLD) -> List[Tuple[Path, int]]:
    """Find files larger than threshold in directory."""
    large_files = []
    if not directory.exists():
        return large_files
    
    for filepath in directory.rglob('*'):
        if filepath.is_file():
            size = filepath.stat().st_size
            if size > threshold:
                large_files.append((filepath, size))
    
    return sorted(large_files, key=lambda x: x[1], reverse=True)

def compress_file(filepath: Path) -> bool:
    """Compress a file using gzip. Returns True if successful."""
    if filepath.suffix == '.gz':
        logger.info(f"Skipping {filepath} - already compressed")
        return True
        
    compressed_path = Path(str(filepath) + '.gz')
    
    try:
        logger.info(f"Compressing {filepath} ({filepath.stat().st_size / 1024 / 1024:.1f} MB)")
        with open(filepath, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Verify compressed file
        if compressed_path.exists():
            original_size = filepath.stat().st_size
            compressed_size = compressed_path.stat().st_size
            logger.info(f"Compressed {filepath} -> {compressed_path} ({compressed_size/original_size*100:.1f}% of original)")
            filepath.unlink()  # Remove original
            return True
        else:
            logger.error(f"Failed to create compressed file for {filepath}")
            return False
            
    except Exception as e:
        logger.error(f"Error compressing {filepath}: {e}")
        return False

def remove_intermediate_file(filepath: Path) -> bool:
    """Remove an intermediate file. Returns True if successful."""
    try:
        size = filepath.stat().st_size
        logger.info(f"Removing intermediate file: {filepath} ({size / 1024 / 1024:.1f} MB)")
        filepath.unlink()
        return True
    except Exception as e:
        logger.error(f"Error removing {filepath}: {e}")
        return False

def identify_intermediate_files(directory: Path) -> List[Path]:
    """Identify files that are safe to remove or compress."""
    intermediate_files = []
    
    if not directory.exists():
        return intermediate_files
        
    for filepath in directory.rglob('*'):
        if not filepath.is_file():
            continue
            
        filename = filepath.name
        suffix = filepath.suffix.lower()
        
        # Skip already compressed files
        if suffix == '.gz':
            continue
            
        # Identify intermediate files based on extension and location
        is_intermediate = False
          
        # Raw data that has been processed
        if filepath.parent == RAW_DIR and suffix in ['.nii']:
            # Check if corresponding processed file exists
            processed_path = PROCESSED_DIR / filepath.name
            if processed_path.exists() or (processed_path.with_suffix('.nii.gz')).exists():
                is_intermediate = True
                
        # Temporary files
        elif suffix in ['.tmp', '.bak']:
            is_intermediate = True
            
        # Log files that are large
        elif suffix == '.log' and filepath.stat().st_size > LARGE_FILE_THRESHOLD:
            is_intermediate = True
            
        if is_intermediate:
            intermediate_files.append(filepath)
            
    return intermediate_files

def cleanup_pipeline() -> Dict:
    """Main cleanup pipeline."""
    stats = {
        'initial_size_bytes': 0,
        'final_size_bytes': 0,
        'files_compressed': 0,
        'files_removed': 0,
        'space_saved_bytes': 0,
        'errors': []
    }
    
    logger.info("Starting intermediate file cleanup...")
    
    # Calculate initial size
    stats['initial_size_bytes'] = get_directory_size(DATA_DIR)
    logger.info(f"Initial data directory size: {stats['initial_size_bytes'] / 1024 / 1024 / 1024:.2f} GB")
    
    if stats['initial_size_bytes'] <= MAX_SIZE_BYTES:
        logger.info("Directory size is within limits. No cleanup needed.")
        stats['final_size_bytes'] = stats['initial_size_bytes']
        return stats
    
    # Find large files
    large_files = get_large_files(DATA_DIR)
    logger.info(f"Found {len(large_files)} files larger than {LARGE_FILE_THRESHOLD / 1024 / 1024:.0f} MB")
    
    # Identify intermediate files
    intermediate_files = identify_intermediate_files(DATA_DIR)
    logger.info(f"Identified {len(intermediate_files)} intermediate files for cleanup")
    
    # Process intermediate files
    for filepath in intermediate_files:
        if not filepath.exists():
            continue
            
        suffix = filepath.suffix.lower()
        
        if suffix in COMPRESSIBLE_EXTENSIONS:
            if compress_file(filepath):
                stats['files_compressed'] += 1
        else:
            if remove_intermediate_file(filepath):
                stats['files_removed'] += 1
    
    # If still over limit, check for other large files to compress
    if get_directory_size(DATA_DIR) > MAX_SIZE_BYTES:
        logger.warning("Still over size limit. Attempting to compress additional large files...")
        for filepath, size in large_files:
            if get_directory_size(DATA_DIR) <= MAX_SIZE_BYTES:
                break
                
            if filepath.suffix.lower() in COMPRESSIBLE_EXTENSIONS and not filepath.suffix.lower() == '.gz':
                if compress_file(filepath):
                    stats['files_compressed'] += 1
    
    # Calculate final size
    stats['final_size_bytes'] = get_directory_size(DATA_DIR)
    stats['space_saved_bytes'] = stats['initial_size_bytes'] - stats['final_size_bytes']
    
    logger.info(f"Cleanup complete.")
    logger.info(f"Files compressed: {stats['files_compressed']}")
    logger.info(f"Files removed: {stats['files_removed']}")
    logger.info(f"Space saved: {stats['space_saved_bytes'] / 1024 / 1024 / 1024:.2f} GB")
    logger.info(f"Final directory size: {stats['final_size_bytes'] / 1024 / 1024 / 1024:.2f} GB")
    
    if stats['final_size_bytes'] > MAX_SIZE_BYTES:
        logger.warning(f"WARNING: Directory size ({stats['final_size_bytes'] / 1024 / 1024 / 1024:.2f} GB) still exceeds limit ({MAX_SIZE_BYTES / 1024 / 1024 / 1024} GB)")
    else:
        logger.info("SUCCESS: Directory size is now within the 7GB limit.")
    
    return stats

def main():
    """Entry point for the cleanup script."""
    try:
        stats = cleanup_pipeline()
        
        # Save stats to JSON
        stats_path = DATA_DIR / "cleanup_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Cleanup statistics saved to {stats_path}")
        
        # Exit with appropriate code
        if stats['final_size_bytes'] > MAX_SIZE_BYTES:
            logger.error("Cleanup failed to reduce directory size below 7GB limit.")
            sys.exit(1)
        else:
            logger.info("Cleanup completed successfully.")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
