"""
Core verification logic for research files.

This module provides functions to verify the integrity and content of research
documents, ensuring they meet the project's scientific standards.
"""

import os
from pathlib import Path
from typing import Optional

def verify_research_file(file_path: Path) -> bool:
    """
    Verify that a research file exists, is readable, and is not empty.
    
    Args:
        file_path: Path to the research file.
        
    Returns:
        True if the file is valid.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file is not readable.
        ValueError: If the file is empty.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Research file missing: {file_path}")
    
    if not file_path.is_file():
        raise FileNotFoundError(f"Path exists but is not a file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                raise ValueError(f"Research file is empty: {file_path}")
        return True
    except PermissionError as e:
        raise PermissionError(f"Research file exists but is not readable: {file_path}") from e