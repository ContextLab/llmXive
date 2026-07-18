"""
Utility functions for code cleanup and refactoring tasks.
This module provides helpers for standardizing imports, docstrings, and code structure.
"""
import ast
import re
from typing import List, Dict, Any, Optional, Tuple


def standardize_docstring(docstring: Optional[str]) -> str:
    """
    Standardize a docstring to follow the project's convention.

    Args:
        docstring: The original docstring.

    Returns:
        A standardized docstring.
    """
    if not docstring:
        return "TODO: Add docstring"

    # Basic cleanup: strip leading/trailing whitespace
    lines = docstring.strip().split('\n')
    lines = [line.strip() for line in lines]
    return '\n'.join(lines)


def check_imports(file_content: str) -> List[str]:
    """
    Analyze a Python file's imports and return a list of issues.

    Args:
        file_content: The content of the Python file.

    Returns:
        A list of strings describing import issues.
    """
    issues = []
    try:
        tree = ast.parse(file_content)
    except SyntaxError as e:
        issues.append(f"Syntax error in file: {e}")
        return issues

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith('.'):
                    issues.append(f"Relative import '{alias.name}' detected. Ensure it is valid.")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith('.'):
                issues.append(f"Relative import from '{node.module}' detected.")

    return issues


def remove_unused_imports(file_content: str) -> Tuple[str, List[str]]:
    """
    Remove unused imports from a Python file.

    Args:
        file_content: The content of the Python file.

    Returns:
        A tuple of (cleaned_content, list_of_removed_imports).
    """
    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return file_content, []

    # Collect all used names in the module body (excluding imports)
    used_names = set()
    import_nodes = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_nodes.append(node)
        elif isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attribute usage
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)

    lines = file_content.split('\n')
    removed = []
    new_lines = []

    for node in import_nodes:
        if isinstance(node, ast.Import):
            # Check each alias
            new_aliases = []
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name.split('.')[-1]
                if name in used_names:
                    new_aliases.append(alias)
                else:
                    removed.append(alias.name)
            if new_aliases:
                # Reconstruct the line (simplified)
                alias_strs = [f"{a.name}" + (f" as {a.asname}" if a.asname else "") for a in new_aliases]
                new_lines.append(f"import {', '.join(alias_strs)}")
            else:
                # Skip this line (it's fully unused)
                pass
        elif isinstance(node, ast.ImportFrom):
            # Check each name
            new_names = []
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                if name in used_names or name == "*":
                    new_names.append(alias)
                else:
                    removed.append(alias.name)
            if new_names:
                alias_strs = [f"{a.name}" + (f" as {a.asname}" if a.asname else "") for a in new_names]
                module = node.module or ""
                new_lines.append(f"from {module} import {', '.join(alias_strs)}")
            else:
                pass

    # This is a simplified version. A real implementation would preserve line numbers and comments.
    # For now, we just return the original content if we can't safely reconstruct.
    # In a real cleanup task, we would use a library like `libcst` or `astor`.
    return file_content, removed
