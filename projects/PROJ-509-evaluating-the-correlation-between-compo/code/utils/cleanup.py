"""
Utility functions for code cleanup and standardization.
"""
import ast
import re
from typing import List, Dict, Any, Optional, Tuple


def remove_unused_imports(file_path: str) -> Tuple[bool, str]:
    """
    Remove unused imports from a Python file.

    Args:
        file_path: Path to the Python file.

    Returns:
        Tuple of (success, message).
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        module = tree

        # Find all imported names
        imported_names = set()
        for node in ast.walk(module):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name)

        # Find all used names in the module body (excluding import nodes)
        used_names = set()
        for node in ast.walk(module):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Handle attribute access like `os.path.join`
                current = node
                parts = []
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                    # The base name is the first part (e.g., 'os' in 'os.path.join')
                    used_names.add(parts[-1])

        # Determine which imports are unused
        unused_imports = imported_names - used_names

        if not unused_imports:
            return True, "No unused imports found."

        # Remove unused imports
        lines = source.splitlines()
        new_lines = []
        skip_next = False

        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue

            # Check if this is an import line
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                # Parse the import statement
                try:
                    # Try to parse just this line
                    import_tree = ast.parse(line)
                    import_node = import_tree.body[0]

                    if isinstance(import_node, ast.Import):
                        # Handle: import a, b, c
                        new_aliases = []
                        for alias in import_node.names:
                            name = alias.asname if alias.asname else alias.name
                            if name not in unused_imports:
                                new_aliases.append(alias)

                        if not new_aliases:
                            # Remove the entire line
                            continue
                        else:
                            # Reconstruct the line
                            alias_strs = []
                            for alias in new_aliases:
                                if alias.asname:
                                    alias_strs.append(f"{alias.name} as {alias.asname}")
                                else:
                                    alias_strs.append(alias.name)
                            new_line = f"import {', '.join(alias_strs)}"
                            # Preserve original indentation
                            new_lines.append(line[: len(line) - len(line.lstrip())] + new_line)

                    elif isinstance(import_node, ast.ImportFrom):
                        # Handle: from module import a, b, c
                        new_aliases = []
                        for alias in import_node.names:
                            name = alias.asname if alias.asname else alias.name
                            if name not in unused_imports:
                                new_aliases.append(alias)

                        if not new_aliases:
                            # Remove the entire line
                            continue
                        else:
                            # Reconstruct the line
                            alias_strs = []
                            for alias in new_aliases:
                                if alias.asname:
                                    alias_strs.append(f"{alias.name} as {alias.asname}")
                                else:
                                    alias_strs.append(alias.name)
                            module_name = import_node.module or ""
                            new_line = f"from {module_name} import {', '.join(alias_strs)}"
                            # Preserve original indentation
                            new_lines.append(line[: len(line) - len(line.lstrip())] + new_line)
                    else:
                        new_lines.append(line)
                except SyntaxError:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))

        return True, f"Removed unused imports: {', '.join(unused_imports)}"

    except Exception as e:
        return False, f"Error processing {file_path}: {str(e)}"


def check_imports(file_path: str) -> List[str]:
    """
    Check for unused imports in a Python file without modifying it.

    Args:
        file_path: Path to the Python file.

    Returns:
        List of unused import names.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        module = tree

        # Find all imported names
        imported_names = set()
        for node in ast.walk(module):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name)

        # Find all used names in the module body (excluding import nodes)
        used_names = set()
        for node in ast.walk(module):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                current = node
                parts = []
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                    used_names.add(parts[-1])

        unused_imports = list(imported_names - used_names)
        return sorted(unused_imports)

    except Exception as e:
        return [f"Error: {str(e)}"]


def standardize_docstring(docstring: str) -> str:
    """
    Standardize a docstring to follow the project's conventions.

    Args:
        docstring: The original docstring.

    Returns:
        The standardized docstring.
    """
    if not docstring:
        return ""

    # Normalize whitespace
    lines = docstring.strip().splitlines()
    if not lines:
        return ""

    # Ensure first line is not empty
    while lines and not lines[0].strip():
        lines.pop(0)

    # Ensure last line is not empty
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return ""

    # Standardize format
    result = ['"""']
    result.append(lines[0].strip())

    if len(lines) > 1:
        result.append("")  # Blank line between summary and body
        result.extend(line.rstrip() for line in lines[1:])

    result.append('"""')
    return "\n".join(result)
