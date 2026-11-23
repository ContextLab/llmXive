"""
Utility functions for the Automated Detection of Algorithmic Bias pipeline.

Provides:
- Logging configuration
- Error handling wrappers
- Memory-efficient streaming repository iterator
"""

import ast
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple, Union

# Ensure the project root is in the path for imports if running as a script
# This is defensive; the pipeline should ideally be run as a package.
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

# --- Logging Configuration ---

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    logger_name: str = "bias_pipeline"
) -> logging.Logger:
    """
    Configures and returns a logger with console and optional file handlers.
    
    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file.
        logger_name: Name of the logger to configure.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File Handler (optional)
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        fh = logging.FileHandler(log_file)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

# --- Error Handling ---

class PipelineError(Exception):
    """Base exception for pipeline-specific errors."""
    pass

class SyntaxErrorInRepo(PipelineError):
    """Raised when a repository file contains unparseable Python syntax."""
    pass

class FileNotFoundErrorInRepo(PipelineError):
    """Raised when a required file is missing from the repository."""
    pass

def safe_execute(func):
    """
    Decorator to safely execute a function and log errors without crashing the pipeline.
    
    This wrapper catches exceptions, logs them with context, and returns None.
    The caller is responsible for handling the None return value.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SyntaxErrorInRepo as e:
            logging.getLogger(__name__).warning(f"Syntax error skipped: {e}")
            return None
        except FileNotFoundErrorInRepo as e:
            logging.getLogger(__name__).warning(f"File not found skipped: {e}")
            return None
        except Exception as e:
            logging.getLogger(__name__).error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return None
    return wrapper

# --- Streaming Repository Iterator ---

def streaming_repo_iterator(
    repo_path: Union[str, Path],
    extensions: Tuple[str, ...] = ('.py',),
    max_files: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Iterates over Python files in a repository directory in a memory-efficient manner.
    
    This generator yields one dictionary per file containing the file path,
    content string, and relative path. It does NOT load the entire repository
    into memory at once, making it suitable for large datasets.
    
    Args:
        repo_path: Path to the root of the repository.
        extensions: Tuple of file extensions to include (default: ('.py',)).
        max_files: Optional limit on the number of files to yield.
        
    Yields:
        Dict containing:
            - 'path': Absolute path to the file.
            - 'relative_path': Path relative to repo root.
            - 'content': String content of the file.
            - 'extension': File extension.
    """
    repo_root = Path(repo_path)
    if not repo_root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_root}")
    
    if not repo_root.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {repo_root}")
    
    count = 0
    
    # Walk the directory tree
    for root, dirs, files in os.walk(repo_root):
        # Skip hidden directories and common non-code directories to save time/memory
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'venv', 'env', '.git', '__pycache__', 'node_modules'}]
        
        for file in files:
            if max_files and count >= max_files:
                return
            
            if not file.endswith(extensions):
                continue
            
            file_path = Path(root) / file
            relative_path = file_path.relative_to(repo_root)
            
            try:
                # Read file content line-by-line or in chunks if needed, 
                # but for AST parsing we usually need the whole string.
                # Assuming standard text files fit in memory individually.
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                yield {
                    'path': str(file_path),
                    'relative_path': str(relative_path),
                    'content': content,
                    'extension': file_path.suffix
                }
                count += 1
                
            except Exception as e:
                # Log and skip files that cannot be read
                logging.getLogger(__name__).warning(f"Skipping unreadable file {file_path}: {e}")
                continue

def is_valid_python_syntax(content: str) -> Tuple[bool, Optional[str]]:
    """
    Checks if a string contains valid Python syntax.
    
    Args:
        content: String content to check.
        
    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is None.
        If invalid, error_message contains the exception string.
    """
    try:
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)