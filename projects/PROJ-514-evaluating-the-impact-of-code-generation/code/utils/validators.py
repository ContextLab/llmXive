"""
Syntax validation utilities for Python and Java files.
"""

import ast
import logging
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

def get_language_from_extension(file_path: Path) -> Optional[str]:
    """Determine language based on file extension."""
    ext = file_path.suffix.lower()
    if ext == '.py':
        return 'python'
    elif ext in ['.java', '.jav']:
        return 'java'
    return None

def validate_python_syntax(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate Python syntax using the ast module.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def validate_java_syntax(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate Java syntax by attempting to compile it with javac.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    # Check for javac availability
    try:
        subprocess.run(['javac', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, "javac not found in PATH. Java compiler required for validation."
    
    # Create a temporary directory for compilation
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / file_path.name
        
        try:
            # Copy file to temp location
            with open(file_path, 'r', encoding='utf-8') as src:
                content = src.read()
            with open(tmp_file, 'w', encoding='utf-8') as dst:
                dst.write(content)
            
            # Attempt compilation
            result = subprocess.run(
                ['javac', '-Xlint:none', '-d', tmpdir, str(tmp_file)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, None
            else:
                # Extract relevant error message
                error_msg = result.stderr.split('\n')[0] if result.stderr else "Compilation failed"
                return False, f"Java compilation error: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

def validate_file_syntax(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate syntax based on file extension.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    language = get_language_from_extension(file_path)
    
    if language == 'python':
        return validate_python_syntax(file_path)
    elif language == 'java':
        return validate_java_syntax(file_path)
    else:
        return False, f"Unsupported language for file: {file_path}"

def validate_directory(directory: Path) -> Tuple[int, int, List[str]]:
    """
    Validate all Python and Java files in a directory recursively.
    
    Returns:
        Tuple of (valid_count, invalid_count, list_of_errors)
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    valid_count = 0
    invalid_count = 0
    errors = []
    
    # Extensions to check
    extensions = {'.py', '.java', '.jav'}
    
    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            is_valid, error_msg = validate_file_syntax(file_path)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                errors.append(f"{file_path.relative_to(directory)}: {error_msg}")
    
    logger.info(f"Validated {directory}: {valid_count} valid, {invalid_count} invalid")
    return valid_count, invalid_count, errors
