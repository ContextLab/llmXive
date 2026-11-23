"""
Cleanup and refactoring utilities for the statistical analysis pipeline.

This module provides helper functions for code quality, logging standardization,
and resource management cleanup tasks.

Refactors repetitive patterns across ingestion, basis, fpca, and robustness modules.
"""
import os
import logging
import gc
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager

from config import get_project_root, get_log_dir, get_data_dir, get_artifacts_dir

logger = logging.getLogger(__name__)


def setup_cleanup_logging() -> None:
    """
    Initialize logging specifically for cleanup operations.
    Ensures consistent log format and level across all cleanup tasks.
    """
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "cleanup.log"
    
    # Configure root logger if not already configured
    if not logging.getLogger().handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)
    
    # File handler for cleanup logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logging.getLogger().addHandler(file_handler)
    
    logger.info(f"Cleanup logging initialized. Log file: {log_file}")


def validate_file_exists(file_path: str, description: str = "file") -> bool:
    """
    Validate that a required file exists before proceeding with operations.
    
    Args:
        file_path: Path to the file to validate
        description: Human-readable description for error messages
        
    Returns:
        True if file exists, False otherwise
        
    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        error_msg = f"Required {description} not found: {file_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.debug(f"Validated {description} exists: {file_path}")
    return True


def get_file_size_mb(file_path: str) -> float:
    """
    Get the size of a file in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB
    """
    path = Path(file_path)
    if not path.exists():
        return 0.0
    return path.stat().st_size / (1024 * 1024)


def clean_empty_directories(base_path: str, exclude_patterns: Optional[List[str]] = None) -> int:
    """
    Remove empty directories recursively from the base path.
    
    Args:
        base_path: Root directory to start cleanup from
        exclude_patterns: List of directory name patterns to exclude from cleanup
        
    Returns:
        Number of directories removed
    """
    exclude_patterns = exclude_patterns or []
    base = Path(base_path)
    removed_count = 0
    
    if not base.exists():
        logger.warning(f"Base path does not exist: {base_path}")
        return 0
    
    # Process directories bottom-up
    for dir_path in sorted(base.rglob('*'), key=lambda p: len(str(p)), reverse=True):
        if not dir_path.is_dir():
            continue
        
        # Check exclusion patterns
        if any(pattern in dir_path.name for pattern in exclude_patterns):
            logger.debug(f"Skipping excluded directory: {dir_path}")
            continue
        
        # Check if directory is empty
        try:
            if not any(dir_path.iterdir()):
                dir_path.rmdir()
                removed_count += 1
                logger.info(f"Removed empty directory: {dir_path}")
        except PermissionError:
            logger.warning(f"Permission denied when removing: {dir_path}")
        except OSError as e:
            logger.warning(f"Error removing directory {dir_path}: {e}")
    
    logger.info(f"Cleanup complete. Removed {removed_count} empty directories.")
    return removed_count


def cleanup_temp_files(base_path: str, extensions: Optional[List[str]] = None) -> int:
    """
    Remove temporary files from the base path.
    
    Args:
        base_path: Root directory to search for temp files
        extensions: List of file extensions to remove (e.g., ['.tmp', '.bak'])
        
    Returns:
        Number of files removed
    """
    extensions = extensions or ['.tmp', '.bak', '.swp', '.pyc']
    base = Path(base_path)
    removed_count = 0
    
    if not base.exists():
        return 0
    
    for ext in extensions:
        for file_path in base.rglob(f'*{ext}'):
            try:
                file_path.unlink()
                removed_count += 1
                logger.info(f"Removed temp file: {file_path}")
            except PermissionError:
                logger.warning(f"Permission denied when removing: {file_path}")
            except OSError as e:
                logger.warning(f"Error removing file {file_path}: {e}")
    
    logger.info(f"Cleanup complete. Removed {removed_count} temporary files.")
    return removed_count


@contextmanager
def memory_monitor(label: str = "Operation"):
    """
    Context manager to monitor memory usage before and after a block.
    
    Args:
        label: Label for the operation being monitored
        
    Yields:
        None
    """
    gc.collect()
    initial_mem = gc.get_count()
    logger.info(f"[Memory] Starting {label}: GC count = {initial_mem}")
    
    try:
        yield
    finally:
        gc.collect()
        final_mem = gc.get_count()
        delta = final_mem[0] - initial_mem[0]
        logger.info(f"[Memory] Completed {label}: GC count delta = {delta}")


def ensure_required_modules_present(module_names: List[str]) -> None:
    """
    Ensure that required modules are importable.
    
    Args:
        module_names: List of module names to check
        
    Raises:
        ImportError: If any required module is missing
    """
    missing = []
    for name in module_names:
        try:
            __import__(name)
            logger.debug(f"Module available: {name}")
        except ImportError:
            missing.append(name)
    
    if missing:
        error_msg = f"Missing required modules: {', '.join(missing)}"
        logger.error(error_msg)
        raise ImportError(error_msg)


def get_project_stats() -> Dict[str, Any]:
    """
    Gather statistics about the project structure.
    
    Returns:
        Dictionary containing project statistics
    """
    root = get_project_root()
    data_dir = get_data_dir()
    artifacts_dir = get_artifacts_dir()
    
    stats = {
        "root": str(root),
        "data_dir_exists": data_dir.exists(),
        "artifacts_dir_exists": artifacts_dir.exists(),
        "data_size_mb": get_file_size_mb(str(data_dir)),
        "artifacts_size_mb": get_file_size_mb(str(artifacts_dir)),
    }
    
    logger.info(f"Project stats: {stats}")
    return stats


def main() -> int:
    """
    Main entry point for cleanup operations.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        setup_cleanup_logging()
        logger.info("Starting cleanup and refactoring operations...")
        
        # Validate project structure
        project_root = get_project_root()
        validate_file_exists(str(project_root), "project root")
        
        # Clean up temporary files
        temp_count = cleanup_temp_files(str(project_root))
        
        # Clean up empty directories (excluding code, data, tests, specs)
        empty_count = clean_empty_directories(
            str(project_root),
            exclude_patterns=['code', 'data', 'tests', 'specs', '.git']
        )
        
        # Get project statistics
        stats = get_project_stats()
        
        logger.info("Cleanup operations completed successfully.")
        logger.info(f"Summary: {temp_count} temp files, {empty_count} empty dirs removed")
        
        return 0
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
