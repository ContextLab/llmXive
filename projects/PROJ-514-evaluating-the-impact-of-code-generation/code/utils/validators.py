"""
Syntax validation utilities for code files.
Supports Python (ast) and Java (javac subprocess) integrity checks.
"""

import ast
import logging
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, Any

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
    Validate Python syntax using the built-in ast module.
    
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
        True if valid, False otherwise.
        Returns False if javac is not found or file has syntax errors.
    """
    try:
        # Ensure file exists
        if not file_path.exists():
            logger.error(f"Java file not found: {file_path}")
            return False

        # Create a temporary directory for compilation
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir)
            # Copy file to temp directory to avoid modifying original
            temp_file = temp_dir / file_path.name
            temp_file.write_text(file_path.read_text())
            
            # Run javac
            # We use -Xlint:none to suppress warnings and focus on errors
            # We use -proc:none to skip annotation processing for speed
            result = subprocess.run(
                ["javac", "-Xlint:none", "-proc:none", "-d", str(temp_dir), str(temp_file)],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.debug(f"Java compilation failed for {file_path}: {result.stderr.decode()}")
                return False
            
            return True
    except subprocess.TimeoutExpired:
        logger.warning(f"Java validation timed out for {file_path}")
        return False
    except FileNotFoundError:
        logger.warning("javac not found in PATH; skipping Java validation")
        # If javac is missing, we cannot validate, so we return False to indicate
        # the check could not be performed successfully (fail loud).
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Java validation for {file_path}: {e}")
        return False

def validate_file_syntax(file_path: Path) -> bool:
    """
    Validate syntax of a file based on its extension.
    
    Args:
        file_path: Path to the file
    
    Returns:
        True if valid, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return False

    language = get_language_from_extension(str(file_path))
    
    if language == 'python':
        try:
            code = file_path.read_text()
            return validate_python_syntax(code)
        except UnicodeDecodeError as e:
            logger.error(f"Could not read file as text: {file_path} ({e})")
            return False
    elif language == 'java':
        return validate_java_syntax(file_path)
    else:
        logger.warning(f"Unknown language for {file_path}, skipping validation")
        # For unknown types, we assume valid to avoid blocking non-code files,
        # but log the event.
        return True

def validate_directory(dir_path: Path) -> Dict[str, Any]:
    """
    Validate all Python and Java files in a directory recursively.
    
    Args:
        dir_path: Path to directory
    
    Returns:
        Dict with validation results:
            - total: total number of files checked
            - valid: count of valid files
            - invalid: count of invalid files
            - errors: list of paths to invalid files
    """
    results: Dict[str, Any] = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "errors": []
    }
    
    if not dir_path.exists() or not dir_path.is_dir():
        logger.error(f"Directory does not exist: {dir_path}")
        return results
    
    for file_path in dir_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in ['.py', '.java']:
            results["total"] += 1
            if validate_file_syntax(file_path):
                results["valid"] += 1
            else:
                results["invalid"] += 1
                results["errors"].append(str(file_path))
    
    return results