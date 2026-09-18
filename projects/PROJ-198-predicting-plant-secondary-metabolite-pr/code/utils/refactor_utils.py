"""
Utility functions for code refactoring and cleanup.

This module provides helper functions used by the cleanup_refactor.py script
to analyze and modify Python source files.
"""
import ast
import re
from pathlib import Path
from typing import List, Set, Tuple, Optional
import logging

from utils.logging import get_logger

logger = get_logger(__name__)


def get_imported_names(tree: ast.AST) -> Set[str]:
    """
    Extract all imported names from an AST.

    Args:
        tree: The parsed AST of a Python file.

    Returns:
        A set of all imported names (handling aliases).
    """
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Get the base name or alias
                name = alias.asname if alias.asname else alias.name
                imports.add(name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.add(name)
    return imports


def get_used_names(tree: ast.AST) -> Set[str]:
    """
    Extract all names used in the AST.

    Args:
        tree: The parsed AST of a Python file.

    Returns:
        A set of all names used in the code.
    """
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            # For attribute access, we only care about the top-level name
            if isinstance(node.value, ast.Name):
                used.add(node.value.id)
    return used


def find_unused_imports(content: str) -> List[str]:
    """
    Find imports that are not used in the code.

    Args:
        content: The content of a Python file.

    Returns:
        A list of unused import names.
    """
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        logger.warning(f"Syntax error in file: {e}")
        return []

    imported = get_imported_names(tree)
    used = get_used_names(tree)

    unused = imported - used
    return list(unused)


def fix_import_section(content: str, unused_imports: List[str]) -> str:
    """
    Remove unused imports from the content.

    Args:
        content: The content of a Python file.
        unused_imports: List of import names to remove.

    Returns:
        The content with unused imports removed.
    """
    if not unused_imports:
        return content

    lines = content.split("\n")
    new_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this is an import line
        if stripped.startswith("import ") or stripped.startswith("from "):
            # Collect all lines that are part of this import statement
            import_lines = [line]
            j = i + 1
            while j < len(lines) and (lines[j].startswith(" ") or lines[j].startswith("\t")):
                import_lines.append(lines[j])
                j += 1

            # Parse the import block to find what's imported
            import_block = "\n".join(import_lines)
            try:
                tree = ast.parse(import_block)
                current_imports = get_imported_names(tree)

                # Check if any of these imports are unused
                should_keep = False
                for imp in current_imports:
                    if imp not in unused_imports:
                        should_keep = True
                        break

                if should_keep:
                    new_lines.extend(import_lines)

                i = j
                continue
            except SyntaxError:
                # If we can't parse it, keep the line
                new_lines.append(line)
        else:
            new_lines.append(line)

        i += 1

    return "\n".join(new_lines)


def extract_function_signatures(content: str) -> List[Tuple[str, str]]:
    """
    Extract function signatures and their current names.

    Args:
        content: The content of a Python file.

    Returns:
        A list of tuples (function_name, signature).
    """
    functions = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return functions

    lines = content.split("\n")

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Get the function signature
            start_line = node.lineno - 1
            if start_line < len(lines):
                signature = lines[start_line].strip()
                functions.append((node.name, signature))

    return functions


def consolidate_logging_calls(content: str) -> str:
    """
    Consolidate multiple logging calls into a more efficient pattern.

    Args:
        content: The content of a Python file.

    Returns:
        The content with consolidated logging calls.
    """
    # This is a placeholder for more advanced logging optimization
    # A full implementation would analyze logging patterns and optimize them
    return content