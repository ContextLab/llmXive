"""
Cleanup utility for User Story 1.
Ensures intermediate files are cleaned up or compressed to stay within 7GB total directory size.

This script scans the data directories, identifies large intermediate files (e.g., raw NIfTI,
pre-ICA-AROMA outputs), and either compresses them or removes them based on configuration.
It also enforces a hard size limit on the total data directory.
"""
import os
import gzip
import shutil
import logging
import json
import sys
from pathlib import Path
from typing import List, Tuple, Dict
from dataclasses import dataclass

# Import config for paths and thresholds
try:
    from utils.config import get_config
except ImportError:
    # Fallback for direct execution without full package setup
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/cleanup.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
SIZE_LIMIT_BYTES = 7 * 1024 * 1024 * 1024  # 7GB
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB
INTERMEDIATE_PATTERNS = [
    'desc-preproc_bold.nii.gz',
    'desc-smooth_bold.nii.gz',
    'desc-confounds_timeseries.tsv',
    'desc-AROMA_noise.nii.gz',
    'func_space-MNI_desc-preproc_bold.nii.gz'
]
KEEP_PATTERNS = [
    'desc-denoised_bold.nii.gz',
    'desc-normalized_bold.nii.gz',
    'valid_subjects.json',
    'metadata.json'
]

@dataclass
class FileAction:
    path: Path
    action: str  # 'compress', 'delete', 'keep'
    original_size: int
    estimated_new_size: int = 0

def get_directory_size(path: Path) -> int:
    """Calculate total size of a directory in bytes."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = Path(dirpath) / f
            try:
                total_size += fp.stat().st_size
            except OSError:
                pass
    return total_size

def identify_files_for_cleanup(data_dir: Path) -> List[FileAction]:
    """Identify files that should be cleaned up or compressed."""
    actions = []
    
    if not data_dir.exists():
        logger.warning(f"Data directory {data_dir} does not exist.")
        return actions

    for root, dirs, files in os.walk(data_dir):
        for file in files:
            file_path = Path(root) / file
            try:
                size = file_path.stat().st_size
            except OSError:
                continue

            # Skip if file is too small
            if size < LARGE_FILE_THRESHOLD:
                continue

            # Check if it's a keep pattern
            if any(file.endswith(p) for p in KEEP_PATTERNS):
                actions.append(FileAction(file_path, 'keep', size))
                continue

            # Check if it's an intermediate pattern
            if any(file.endswith(p) for p in INTERMEDIATE_PATTERNS):
                # Compress if not already compressed
                if not file.endswith('.gz'):
                    actions.append(FileAction(file_path, 'compress', size, size // 3))
                else:
                    # Already compressed, delete if it's intermediate
                    actions.append(FileAction(file_path, 'delete', size))
                continue

            # Default: check extension for large files
            if file.endswith(('.nii', '.nii.gz', '.tsv', '.txt')):
                # If it's not in a 'processed' or 'final' subdirectory, consider compression
                if 'raw' in str(file_path) or 'intermediate' in str(file_path):
                    if not file.endswith('.gz'):
                        actions.append(FileAction(file_path, 'compress', size, size // 3))
                    else:
                        actions.append(FileAction(file_path, 'delete', size))
                    continue

    return actions

def compress_file(file_path: Path) -> int:
    """Compress a file using gzip. Returns new size."""
    compressed_path = Path(str(file_path) + '.gz')
    try:
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        new_size = compressed_path.stat().st_size
        file_path.unlink()  # Remove original
        logger.info(f"Compressed {file_path.name} -> {compressed_path.name} ({new_size} bytes)")
        return new_size
    except Exception as e:
        logger.error(f"Failed to compress {file_path}: {e}")
        return file_path.stat().st_size

def delete_file(file_path: Path) -> None:
    """Delete a file."""
    try:
        file_path.unlink()
        logger.info(f"Deleted {file_path.name}")
    except Exception as e:
        logger.error(f"Failed to delete {file_path}: {e}")

def enforce_size_limit(data_dir: Path, limit_bytes: int = SIZE_LIMIT_BYTES) -> bool:
    """
    Enforce the total directory size limit.
    Returns True if limit is satisfied, False otherwise.
    """
    current_size = get_directory_size(data_dir)
    
    if current_size <= limit_bytes:
        logger.info(f"Total data directory size ({current_size / 1e9:.2f} GB) is within limit.")
        return True
    
    logger.warning(f"Total data directory size ({current_size / 1e9:.2f} GB) exceeds limit ({limit_bytes / 1e9:.2f} GB).")
    
    # Identify files to clean
    actions = identify_files_for_cleanup(data_dir)
    
    # Prioritize deletions over compressions
    actions.sort(key=lambda x: (0 if x.action == 'delete' else 1, -x.original_size))
    
    space_needed = current_size - limit_bytes
    freed_space = 0
    
    for action in actions:
        if freed_space >= space_needed:
            break
        
        if action.action == 'delete':
            delete_file(action.path)
            freed_space += action.original_size
        elif action.action == 'compress':
            new_size = compress_file(action.path)
            freed_space += (action.original_size - new_size)
    
    final_size = get_directory_size(data_dir)
    logger.info(f"After cleanup, total size: {final_size / 1e9:.2f} GB")
    
    return final_size <= limit_bytes

def main():
    """Main entry point for cleanup script."""
    config = get_config()
    data_dir = Path(config.get('data_dir', 'data'))
    
    logger.info(f"Starting cleanup for directory: {data_dir}")
    
    # First, try to compress/delete intermediate files
    actions = identify_files_for_cleanup(data_dir)
    logger.info(f"Identified {len(actions)} files for action.")
    
    for action in actions:
        if action.action == 'compress':
            compress_file(action.path)
        elif action.action == 'delete':
            delete_file(action.path)
    
    # Then enforce size limit
    success = enforce_size_limit(data_dir)
    
    if not success:
        logger.error("Failed to reduce directory size below 7GB limit.")
        sys.exit(1)
    
    # Generate a report
    report = {
        'timestamp': str(Path().absolute()),
        'total_size_gb': get_directory_size(data_dir) / 1e9,
        'limit_gb': SIZE_LIMIT_BYTES / 1e9,
        'status': 'success' if success else 'failed'
    }
    
    report_path = data_dir / 'cleanup_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Cleanup complete. Report saved to {report_path}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
