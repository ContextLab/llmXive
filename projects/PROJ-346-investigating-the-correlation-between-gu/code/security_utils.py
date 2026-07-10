"""
Security utilities for the llmXive pipeline.

This module provides functions for sanitizing external inputs,
validating URLs, and preventing path traversal attacks.
"""
import os
from pathlib import Path
from typing import Optional
import re

# Regex pattern to detect path traversal attempts
PATH_TRAVERSAL_PATTERN = re.compile(r'\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c', re.IGNORECASE)

def sanitize_path_input(path: str, base_dir: Optional[Path] = None) -> Path:
    """
    Sanitize a file path to prevent directory traversal attacks.
    
    Args:
        path: The path string to sanitize.
        base_dir: Optional base directory to resolve relative paths against.
                  
    Returns:
        A resolved and validated Path object.
        
    Raises:
        ValueError: If the path contains traversal attempts or resolves outside the base directory.
    """
    if not path or not isinstance(path, str):
        raise ValueError("Path must be a non-empty string.")
    
    path = path.strip()
    
    # Check for traversal patterns in the string
    if PATH_TRAVERSAL_PATTERN.search(path):
        raise ValueError(f"Invalid path detected: potential directory traversal in {path}")
    
    # Convert to Path object
    p = Path(path)
    
    # If relative, resolve against base_dir or project root
    if not p.is_absolute():
        if base_dir is None:
            from utils import get_project_root_path
            base_dir = get_project_root_path()
        p = (base_dir / p).resolve()
    else:
        p = p.resolve()
    
    # Ensure the resolved path is within the intended base directory
    project_root = Path(__file__).resolve().parent.parent
    try:
        p.relative_to(project_root)
    except ValueError:
        raise ValueError(f"Path {p} is outside the project root {project_root}")
    
    return p
