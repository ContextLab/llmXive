"""
Path normalization utilities for the project.
Implements FR-009: lowercase, strip extensions, normalize slashes.
"""

import os
from pathlib import Path
import re
from typing import List, Union

# Extensions to strip
STRIP_EXTENSIONS = {'.bak', '.pyc', '.min.js', '.lock'}

def normalize_path(path: Union[str, Path]) -> str:
    """
    Normalize a file path according to FR-009.
    
    Rules:
    1. Convert to lowercase
    2. Strip .bak, .pyc, .min.js, .lock extensions
    3. Normalize path separators (backslash to forward slash)
    
    Args:
        path: Input path (string or Path object)
    
    Returns:
        Normalized path string
    """
    if isinstance(path, Path):
        path = str(path)
    
    # Normalize slashes
    path = path.replace('\\', '/')
    
    # Convert to lowercase
    path = path.lower()
    
    # Strip specified extensions
    for ext in STRIP_EXTENSIONS:
        if path.endswith(ext):
            path = path[:-len(ext)]
            break
    
    # Remove trailing slashes
    path = path.rstrip('/')
    
    return path

def normalize_paths(paths: List[Union[str, Path]]) -> List[str]:
    """
    Normalize a list of paths.
    
    Args:
        paths: List of paths to normalize
    
    Returns:
        List of normalized path strings
    """
    return [normalize_path(p) for p in paths]

def is_valid_source_path(path: Union[str, Path]) -> bool:
    """
    Check if a path appears to be a valid source file.
    
    Args:
        path: Path to check
    
    Returns:
        True if valid source path, False otherwise
    """
    if isinstance(path, Path):
        path = str(path)
    
    path = normalize_path(path)
    
    # Check for common source file extensions
    valid_extensions = {
        '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.hpp',
        '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.php',
        '.cs', '.m', '.mm', '.pl', '.pm', '.sh', '.bash'
    }
    
    # Get extension
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    
    return ext in valid_extensions
