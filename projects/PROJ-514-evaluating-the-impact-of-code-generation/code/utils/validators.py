"""
Syntax validation utilities for code files.
"""

import ast
import logging
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional

from utils.logger import get_logger
logger = get_logger(__name__)

def get_language_from_extension(file_path: str) -> Optional[str]:
    """
    Determine language from file extension.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Language name ('python', 'java', etc.) or None
    """
    ext = Path(file_path).suffix.lower()
    if ext == '.py':
        return 'python'
    elif ext == '.java':
        return 'java'
    return None

def validate_python_syntax(code: str) -> bool:
    """
    Validate Python syntax.
    
    Args:
        code: Python code string
    
    Returns:
        True if valid, False otherwise
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        logger.debug(f"Python syntax error: {e}")
        return False

def validate_java_syntax(file_path: Path) -> bool:
    """
    Validate Java syntax using javac (if available).
    
    Args:
        file_path: Path to Java file
    
    Returns:
        True if valid, False otherwise
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy file to temp directory
            temp_file = Path(tmpdir) / file_path.name
            temp_file.write_text(file_path.read_text())
            
            # Run javac
            result = subprocess.run(
                ["javac", "-Xlint:none", str(temp_file)],
                capture_output=True,
                timeout=30
            )
            
            return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"Java validation failed: {e}")
        return False

def validate_file_syntax(file_path: Path) -> bool:
    """
    Validate syntax of a file based on its extension.
    
    Args:
        file_path: Path to the file
    
    Returns:
        True if valid, False otherwise
    """
    language = get_language_from_extension(str(file_path))
    
    if language == 'python':
        code = file_path.read_text()
        return validate_python_syntax(code)
    elif language == 'java':
        return validate_java_syntax(file_path)
    else:
        logger.warning(f"Unknown language for {file_path}, skipping validation")
        return True

def validate_directory(dir_path: Path) -> Dict[str, Any]:
    """
    Validate all files in a directory.
    
    Args:
        dir_path: Path to directory
    
    Returns:
        Dict with validation results
    """
    results = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "errors": []
    }
    
    for file_path in dir_path.iterdir():
        if file_path.is_file() and file_path.suffix in ['.py', '.java']:
            results["total"] += 1
            if validate_file_syntax(file_path):
                results["valid"] += 1
            else:
                results["invalid"] += 1
                results["errors"].append(str(file_path))
    
    return results