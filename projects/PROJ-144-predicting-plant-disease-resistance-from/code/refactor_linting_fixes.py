"""
Refactoring script to apply linting feedback and cleanup codebase.

This script addresses common linting issues identified by flake8/black:
- Removes unused imports
- Fixes line length violations
- Standardizes docstrings
- Removes redundant code
- Fixes variable naming conventions
- Ensures consistent error handling
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple

from utils.constants import CODE_DIR


def find_python_files(directory: Path) -> List[Path]:
    """Recursively find all Python files in a directory."""
    return list(directory.rglob("*.py"))


def parse_imports(file_path: Path) -> Tuple[Set[str], Set[str], Set[str]]:
    """
    Parse a Python file and extract imported names.
    
    Returns:
        Tuple of (standard_lib, third_party, local_imports)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            return set(), set(), set()
    
    std_lib = set()
    third_party = set()
    local_imports = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".")[0]
                std_lib.add(name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split(".")[0]
                # Check if it's a local import
                if module_name in ["utils", "data", "modeling", "research", "setup"]:
                    local_imports.add(module_name)
                else:
                    # Simple heuristic: if not in std_lib, assume third_party
                    std_lib.add(module_name)
    
    return std_lib, third_party, local_imports


def remove_unused_imports(file_path: Path) -> bool:
    """
    Remove unused imports from a Python file.
    
    Returns:
        True if file was modified, False otherwise.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return False
    
    # Get all names used in the file
    used_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle attribute access like 'pd.DataFrame'
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)
    
    # Find import lines
    lines = content.split("\n")
    new_lines = []
    modified = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            # Check if this import is used
            import_match = re.match(r"(?:import|from)\s+(\S+)", stripped)
            if import_match:
                import_name = import_match.group(1).split(".")[0]
                # Simple check: if import name is not in used_names, skip it
                # This is a heuristic and may not catch all cases
                if import_name not in used_names and not any(
                    name.startswith(import_name) for name in used_names
                ):
                    modified = True
                    continue
        new_lines.append(line)
    
    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))
        return True
    
    return False


def fix_line_length(file_path: Path, max_length: int = 88) -> bool:
    """
    Fix line length violations by wrapping long lines.
    
    Returns:
        True if file was modified, False otherwise.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    
    for line in lines:
        # Skip if line is already short enough
        if len(line.rstrip("\n")) <= max_length:
            new_lines.append(line)
            continue
        
        # Skip if line is a comment or string
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
            new_lines.append(line)
            continue
        
        # Simple wrapping: break at spaces
        parts = line.rstrip("\n").split()
        if len(parts) <= 1:
            new_lines.append(line)
            continue
        
        # Rebuild line with wrapping
        current_line = parts[0]
        for part in parts[1:]:
            if len(current_line) + 1 + len(part) <= max_length:
                current_line += " " + part
            else:
                new_lines.append(current_line + "\n")
                current_line = part
        
        new_lines.append(current_line + "\n")
        modified = True
    
    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    
    return False


def fix_docstrings(file_path: Path) -> bool:
    """
    Standardize docstring format to use triple double quotes.
    
    Returns:
        True if file was modified, False otherwise.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace single quotes with double quotes for docstrings
    # This is a simple regex-based approach
    pattern = r'(?m)^\s*("""|\'\'\')'
    replacement = '"""'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    
    return False


def fix_variable_naming(file_path: Path) -> bool:
    """
    Fix variable naming to follow snake_case convention.
    
    Returns:
        True if file was modified, False otherwise.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find all variable assignments
    # This is a simplified approach
    modified = False
    new_content = content
    
    # Pattern to match CamelCase variables (excluding classes)
    camel_case_pattern = r'(?<![A-Za-z])([a-z]+[A-Z][a-zA-Z0-9]*)(?=\s*[=,;)\]])'
    
    # Replace CamelCase with snake_case
    def to_snake_case(match):
        name = match.group(1)
        # Insert underscore before capital letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return s2.lower()
    
    new_content = re.sub(camel_case_pattern, to_snake_case, new_content)
    
    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    
    return False


def cleanup_redundant_code(file_path: Path) -> bool:
    """
    Remove redundant code patterns (e.g., redundant type hints, unnecessary parentheses).
    
    Returns:
        True if file was modified, False otherwise.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    modified = False
    new_content = content
    
    # Remove redundant parentheses around return values
    new_content = re.sub(r'return\s+\((.*?)\)', r'return \1', new_content)
    
    # Remove redundant parentheses around function arguments
    new_content = re.sub(r'(\w+)\s*\(\s*(.*?)\s*\)', r'\1(\2)', new_content)
    
    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    
    return False


def apply_linting_fixes(file_path: Path) -> Dict[str, bool]:
    """
    Apply all linting fixes to a single file.
    
    Returns:
        Dictionary of fix names to success status.
    """
    results = {
        "remove_unused_imports": remove_unused_imports(file_path),
        "fix_line_length": fix_line_length(file_path),
        "fix_docstrings": fix_docstrings(file_path),
        "fix_variable_naming": fix_variable_naming(file_path),
        "cleanup_redundant_code": cleanup_redundant_code(file_path),
    }
    return results


def main():
    """Main entry point for the refactoring script."""
    print("Starting linting feedback cleanup...")
    
    python_files = find_python_files(CODE_DIR)
    total_files = len(python_files)
    modified_count = 0
    
    for i, file_path in enumerate(python_files, 1):
        print(f"[{i}/{total_files}] Processing {file_path.relative_to(CODE_DIR)}")
        
        results = apply_linting_fixes(file_path)
        
        if any(results.values()):
            modified_count += 1
            print(f"  Modified: {file_path.relative_to(CODE_DIR)}")
            for fix, success in results.items():
                if success:
                    print(f"    - Applied {fix}")
        else:
            print(f"  No changes needed")
    
    print(f"\nCleanup complete. Modified {modified_count}/{total_files} files.")
    print("Please run 'black --check code/' and 'flake8 code/' to verify fixes.")

if __name__ == "__main__":
    main()
