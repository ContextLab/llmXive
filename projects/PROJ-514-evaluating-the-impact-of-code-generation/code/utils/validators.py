import ast
import logging
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Tuple, Optional

def get_language_from_extension(file_path: Path) -> Optional[str]:
    """Determines language based on file extension."""
    ext = file_path.suffix.lower()
    if ext == '.py':
        return 'python'
    elif ext in ['.java', '.kt', '.groovy']:
        return 'java'
    return None

def validate_python_syntax(code_content: str) -> Tuple[bool, Optional[str]]:
    """Validates Python syntax using ast module."""
    try:
        ast.parse(code_content)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def validate_java_syntax(code_content: str, java_path: str = "javac") -> Tuple[bool, Optional[str]]:
    """Validates Java syntax using javac (requires Java installed)."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".java", delete=False) as tmp:
        tmp.write(code_content.encode('utf-8'))
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [java_path, tmp_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, None
        else:
            return False, f"Compilation Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Compilation Timeout"
    except FileNotFoundError:
        return False, "javac not found (Java not installed)"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def validate_file_syntax(file_path: Path) -> Tuple[bool, Optional[str]]:
    """Validates syntax of a file based on extension."""
    if not file_path.exists():
        return False, "File not found"
    
    lang = get_language_from_extension(file_path)
    if not lang:
        return True, None # Unknown extension, skip validation or treat as valid
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return False, f"Read Error: {str(e)}"
    
    if lang == 'python':
        return validate_python_syntax(content)
    elif lang == 'java':
        return validate_java_syntax(content)
    
    return True, None

def validate_directory(dir_path: Path) -> Tuple[int, int, int]:
    """
    Validates all files in a directory.
    Returns (total, valid, invalid_count)
    """
    if not dir_path.exists():
        return 0, 0, 0
    
    total = 0
    valid = 0
    invalid = 0
    
    for file_path in dir_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in ['.py', '.java']:
            total += 1
            is_valid, reason = validate_file_syntax(file_path)
            if is_valid:
                valid += 1
            else:
                invalid += 1
                logging.getLogger(__name__).warning(f"Invalid {file_path}: {reason}")
    
    return total, valid, invalid
