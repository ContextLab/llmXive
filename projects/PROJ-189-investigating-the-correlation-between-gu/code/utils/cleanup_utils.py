import os
import json
import logging
import hashlib
import shutil
import ast
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import is_dataclass, asdict

# Configure logger for this module
logger = logging.getLogger(__name__)


def ensure_directory_exists(path: str) -> None:
    """Ensure the directory for the given path exists, creating it if necessary."""
    dir_path = Path(path).parent
    dir_path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {dir_path}")


def load_json_config(path: str) -> Dict[str, Any]:
    """Load and parse a JSON configuration file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_config(data: Dict[str, Any], path: str) -> None:
    """Save a dictionary to a JSON file with pretty formatting."""
    ensure_directory_exists(path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True)
    logger.info(f"Saved JSON config to {path}")


def calculate_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """Calculate the checksum of a file using the specified algorithm."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(p, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def validate_data_integrity(file_path: str, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """Validate a file's integrity by comparing its checksum to an expected value."""
    actual_checksum = calculate_file_checksum(file_path, algorithm)
    is_valid = actual_checksum == expected_checksum
    
    if not is_valid:
        logger.error(
            f"Integrity check failed for {file_path}. "
            f"Expected: {expected_checksum}, Actual: {actual_checksum}"
        )
    else:
        logger.debug(f"Integrity check passed for {file_path}")
    
    return is_valid


def validate_required_columns(df: Any, required_columns: List[str], df_name: str = "DataFrame") -> None:
    """
    Validate that a DataFrame-like object contains all required columns.
    Raises ValueError if any are missing.
    """
    if not hasattr(df, 'columns'):
        raise TypeError(f"{df_name} does not appear to be a DataFrame-like object.")
    
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"{df_name} is missing required columns: {missing}")
    
    logger.debug(f"{df_name} validation passed: all required columns present.")


def clean_temporary_artifacts(patterns: List[str], base_dir: str = "data/processed") -> int:
    """
    Remove temporary files matching given glob patterns relative to base_dir.
    Returns the count of files removed.
    """
    base = Path(base_dir)
    removed_count = 0
    
    for pattern in patterns:
        for file_path in base.glob(pattern):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    logger.info(f"Removed temporary artifact: {file_path}")
                    removed_count += 1
                except OSError as e:
                    logger.warning(f"Failed to remove {file_path}: {e}")
    
    return removed_count


def standardize_logger(logger_obj: logging.Logger, name: Optional[str] = None) -> logging.Logger:
    """
    Ensure a logger is configured with a standard format and level.
    If name is provided, retrieves that logger; otherwise uses the passed object.
    """
    if name:
        logger_obj = logging.getLogger(name)
    
    if logger_obj.handlers:
        # Already configured
        return logger_obj
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(module)s] [%(message)s]',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger_obj.addHandler(handler)
    logger_obj.setLevel(logging.INFO)
    
    return logger_obj


def refactor_imports_check(file_path: str) -> Tuple[bool, List[str]]:
    """
    Analyze a Python file for common import issues:
    - Unused imports
    - Missing imports for used names (basic check)
    
    Returns (is_clean, list_of_issues).
    """
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(p, 'r', encoding='utf-8') as f:
        source = f.read()
    
    try:
        tree = ast.parse(source, filename=str(p))
    except SyntaxError as e:
        return False, [f"Syntax error in {file_path}: {e}"]
    
    issues = []
    
    # Collect all names defined in the module
    defined_names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            defined_names.add(node.id)
    
    # Collect imported names
    imported_names: Dict[str, str] = {} # alias -> full_name
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name
                imported_names[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                name = alias.asname or alias.name
                imported_names[name] = f"{module}.{alias.name}"
    
    # Collect used names (excluding definitions and imports)
    used_names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attr usage
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)
    
    # Check for unused imports
    for name in imported_names:
        if name not in used_names and name not in defined_names:
            issues.append(f"Unused import: {name}")
    
    # Basic check for missing imports (very naive)
    # This is a simplified check and won't catch all cases
    builtins = set(__builtins__.keys()) if isinstance(__builtins__, dict) else set(__builtins__.__dict__.keys())
    for name in used_names:
        if name not in defined_names and name not in imported_names and name not in builtins:
            # Could be a missing import, but might also be a runtime dynamic import or attribute
            # For cleanup purposes, we flag it as a potential issue
            issues.append(f"Potential missing import for name: {name}")
    
    return len(issues) == 0, issues


def get_module_public_names(module_path: str) -> List[str]:
    """
    Extract the public names (those not starting with underscore) 
    from a Python module file.
    """
    p = Path(module_path)
    if not p.exists():
        raise FileNotFoundError(f"Module file not found: {module_path}")
    
    with open(p, 'r', encoding='utf-8') as f:
        source = f.read()
    
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    
    public_names = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            public_names.append(node.name)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
            public_names.append(node.name)
        elif isinstance(node, ast.Assign):
            # Check for module-level assignments (constants, etc.)
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith('_'):
                    public_names.append(target.id)
    
    return sorted(list(set(public_names)))


def cleanup_unused_imports(file_path: str) -> bool:
    """
    Attempt to remove unused imports from a Python file.
    Returns True if changes were made, False otherwise.
    """
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(p, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    original_content = "".join(lines)
    is_clean, issues = refactor_imports_check(file_path)
    
    if is_clean:
        logger.info(f"No cleanup needed for {file_path}")
        return False
    
    # Filter out unused imports based on issues
    # This is a simplified approach; a robust solution would use ast to reconstruct the file
    new_lines = []
    for line in lines:
        stripped = line.strip()
        is_unused = False
        
        if stripped.startswith('import '):
            parts = stripped.split('import ')
            if len(parts) > 1:
                imported = parts[1].split(',')
                for imp in imported:
                    imp_name = imp.strip().split(' as ')[-1].strip()
                    if f"Unused import: {imp_name}" in issues:
                        is_unused = True
                        break
        elif stripped.startswith('from '):
            # Complex case, skipping detailed removal for safety
            # In a full refactor, we would parse the 'from' statement
            pass
        
        if not is_unused:
            new_lines.append(line)
    
    new_content = "".join(new_lines)
    
    if new_content != original_content:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(new_content)
        logger.info(f"Cleaned up unused imports in {file_path}")
        return True
    
    return False