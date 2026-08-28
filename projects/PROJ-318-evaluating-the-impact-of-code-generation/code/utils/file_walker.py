"""
File walker utility for traversing directory trees and filtering Python files.

This module provides a generator function to efficiently walk through directory
structures and yield paths to .py files, suitable for large codebases.
"""

import os
import logging
from pathlib import Path
from typing import Generator, List, Optional, Set

logger = logging.getLogger(__name__)


class FileWalkerException(Exception):
    """Exception raised for errors in file walking operations."""
    pass


def walk_python_files(
    root_dir: str,
    exclude_dirs: Optional[Set[str]] = None,
    exclude_patterns: Optional[Set[str]] = None
) -> Generator[Path, None, None]:
    """
    Walk a directory tree and yield paths to .py files.

    This is a generator function that yields Path objects for each .py file
    found in the directory tree rooted at `root_dir`. It supports excluding
    specific directories and filename patterns.

    Args:
        root_dir: Root directory to start walking from.
        exclude_dirs: Set of directory names to exclude (e.g., {'__pycache__', '.git'}).
        exclude_patterns: Set of filename patterns to exclude (e.g., {'test_*.py'}).

    Yields:
        Path: Path object for each .py file found.

    Raises:
        FileWalkerException: If root_dir does not exist or is not a directory.
        FileWalkerException: If root_dir is not accessible (permission denied).

    Example:
        >>> for py_file in walk_python_files('/path/to/repo'):
        ...     print(py_file)
        /path/to/repo/module.py
        /path/to/repo/subdir/utils.py
    """
    root_path = Path(root_dir)

    if not root_path.exists():
        raise FileWalkerException(f"Root directory does not exist: {root_dir}")
    if not root_path.is_dir():
        raise FileWalkerException(f"Root path is not a directory: {root_dir}")
    
    try:
        # Check if we can list the root directory
        list(root_path.iterdir())
    except PermissionError:
        raise FileWalkerException(f"Permission denied accessing: {root_dir}")

    # Default exclusions
    if exclude_dirs is None:
        exclude_dirs = {'__pycache__', '.git', '.hg', '.svn', 'node_modules', 'venv', '.venv', 'env', '.env'}
    
    if exclude_patterns is None:
        exclude_patterns = set()

    logger.info(f"Starting file walk from: {root_path}")
    logger.info(f"Excluding directories: {exclude_dirs}")
    logger.info(f"Excluding patterns: {exclude_patterns}")

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filter out excluded directories in-place to prevent os.walk from descending into them
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for filename in filenames:
            # Check if file ends with .py
            if not filename.endswith('.py'):
                continue

            # Check exclusion patterns
            excluded = False
            for pattern in exclude_patterns:
                if pattern in filename:
                    excluded = True
                    logger.debug(f"Excluding file matching pattern '{pattern}': {filename}")
                    break
            
            if excluded:
                continue

            file_path = Path(dirpath) / filename
            logger.debug(f"Yielding Python file: {file_path}")
            yield file_path

    logger.info(f"File walk completed for: {root_path}")


def collect_python_files(
    root_dir: str,
    exclude_dirs: Optional[Set[str]] = None,
    exclude_patterns: Optional[Set[str]] = None
) -> List[Path]:
    """
    Collect all .py files from a directory tree into a list.

    This is a convenience wrapper around walk_python_files that collects
    all results into a list. Useful when you need to know the total count
    or process files in a specific order.

    Args:
        root_dir: Root directory to start walking from.
        exclude_dirs: Set of directory names to exclude.
        exclude_patterns: Set of filename patterns to exclude.

    Returns:
        List[Path]: List of Path objects for all .py files found.

    Example:
        >>> py_files = collect_python_files('/path/to/repo')
        >>> print(f"Found {len(py_files)} Python files")
        Found 42 Python files
    """
    return list(walk_python_files(root_dir, exclude_dirs, exclude_patterns))


def count_python_files(root_dir: str) -> int:
    """
    Count the number of .py files in a directory tree.

    Args:
        root_dir: Root directory to count files in.

    Returns:
        int: Number of .py files found.
    """
    return sum(1 for _ in walk_python_files(root_dir))


def main():
    """
    Command-line entry point for testing the file walker.
    
    Usage:
        python -m utils.file_walker /path/to/directory
    
    This will list all .py files found in the given directory.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m utils.file_walker <directory>")
        sys.exit(1)

    target_dir = sys.argv[1]
    
    try:
        files = list(walk_python_files(target_dir))
        print(f"Found {len(files)} Python files in {target_dir}:")
        for f in files:
            print(f"  {f}")
    except FileWalkerException as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()