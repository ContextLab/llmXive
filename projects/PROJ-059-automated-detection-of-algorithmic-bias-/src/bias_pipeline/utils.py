"""
Utility functions for the bias detection pipeline.

Provides logging setup, custom exceptions, safe execution wrappers,
and a memory-efficient streaming iterator for processing repositories.
"""
import ast
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple, Union

# --------------------------------------------------------------------------
# Custom Exceptions
# --------------------------------------------------------------------------

class PipelineError(Exception):
    """Base exception for pipeline-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}

class SyntaxErrorInRepo(PipelineError):
    """Raised when a repository contains files with invalid Python syntax."""
    pass

class FileNotFoundErrorInRepo(PipelineError):
    """Raised when a required file is missing within a repository."""
    pass

# --------------------------------------------------------------------------
# Logging Setup
# --------------------------------------------------------------------------

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configures a logger with console and optional file output.

    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger("bias_pipeline")
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (if specified)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

# --------------------------------------------------------------------------
# Safe Execution Wrappers
# --------------------------------------------------------------------------

def safe_execute(func: callable, *args: Any, **kwargs: Any) -> Tuple[bool, Any, Optional[Exception]]:
    """
    Executes a function and catches any exceptions, returning a status tuple.

    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        A tuple (success, result, exception).
        - If successful: (True, result, None)
        - If failed: (False, None, exception_instance)
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        return False, None, e

# --------------------------------------------------------------------------
# Syntax Validation
# --------------------------------------------------------------------------

def is_valid_python_syntax(file_path: Union[str, Path]) -> bool:
    """
    Checks if a file contains valid Python syntax without executing it.

    Args:
        file_path: Path to the Python file.

    Returns:
        True if valid, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True
    except SyntaxError:
        return False
    except Exception:
        # If we can't read or parse for any other reason, treat as invalid for safety
        return False

# --------------------------------------------------------------------------
# Streaming Repository Iterator
# --------------------------------------------------------------------------

def streaming_repo_iterator(
    repo_path: Union[str, Path],
    extensions: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
    max_files: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Iterates over Python files in a repository in a memory-efficient manner.

    This generator yields dictionaries containing file metadata and content
    one file at a time, preventing the need to load the entire repository
    into memory. It respects a GB RAM limit by processing files sequentially.

    Args:
        repo_path: Path to the root of the repository.
        extensions: List of file extensions to include (default: ['.py']).
        exclude_dirs: List of directory names to skip (default: ['.git', '__pycache__', 'node_modules']).
        max_files: Optional limit on the number of files to yield.

    Yields:
        A dictionary with keys:
            - 'path': Absolute path to the file.
            - 'content': String content of the file.
            - 'size_bytes': Size of the file in bytes.
            - 'status': 'ok' or 'error' (with 'error_message' if applicable).
    """
    if extensions is None:
        extensions = ['.py']
    
    if exclude_dirs is None:
        exclude_dirs = ['.git', '__pycache__', 'node_modules', '.tox', '.eggs', '*.egg-info']

    repo_root = Path(repo_path)
    if not repo_root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

    if not repo_root.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {repo_path}")

    file_count = 0

    for root, dirs, files in os.walk(repo_root):
        # Filter out excluded directories in-place to prevent os.walk from descending into them
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for filename in files:
            if max_files is not None and file_count >= max_files:
                return

            # Check extension
            if not any(filename.endswith(ext) for ext in extensions):
                continue

            file_path = Path(root) / filename

            try:
                # Check file size to avoid loading massive files into memory
                # Optional: Add a max file size check here if needed (e.g., 10MB)
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                file_size = os.path.getsize(file_path)

                yield {
                    'path': str(file_path),
                    'content': content,
                    'size_bytes': file_size,
                    'status': 'ok'
                }
                
                file_count += 1

            except UnicodeDecodeError as e:
                # Log warning but continue with next file
                yield {
                    'path': str(file_path),
                    'content': None,
                    'size_bytes': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    'status': 'error',
                    'error_message': f"Unicode decode error: {str(e)}"
                }
            except Exception as e:
                # Log unexpected errors
                yield {
                    'path': str(file_path),
                    'content': None,
                    'size_bytes': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    'status': 'error',
                    'error_message': f"Error reading file: {str(e)}"
                }