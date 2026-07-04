"""
Path normalization utilities for FR-009.

This module provides functions to normalize file paths for consistent
comparison and matching across different systems and git representations.
Normalization rules:
1. Convert to lowercase
2. Strip file extensions (e.g., .py, .java, .js)
3. Normalize path separators (forward slashes only)
4. Remove leading/trailing whitespace and slashes
"""

import os
from pathlib import Path
from typing import Union


def normalize_path(path: Union[str, Path]) -> str:
    """
    Normalize a file path according to FR-009 specifications.

    Normalization steps:
    1. Convert to lowercase
    2. Strip common file extensions
    3. Normalize path separators to forward slashes
    4. Remove leading/trailing whitespace and slashes

    Args:
        path: Input path as string or Path object

    Returns:
        Normalized path string

    Examples:
        >>> normalize_path("src/MyClass.py")
        'src/myclass'
        >>> normalize_path("data\\utils\\helper.Java")
        'data/utils/helper'
        >>> normalize_path("  /src/Module.PY  ")
        'src/module'
    """
    # Convert to string and strip whitespace
    normalized = str(path).strip()

    # Convert to lowercase
    normalized = normalized.lower()

    # Normalize path separators (handle both Windows and Unix style)
    normalized = normalized.replace("\\", "/")

    # Remove leading and trailing slashes
    normalized = normalized.strip("/")

    # Strip common file extensions
    # Handle multiple possible extensions (e.g., .pyc, .java, .js, .ts)
    extensions_to_strip = [
        ".py", ".pyc", ".pyo", ".pyd",
        ".java", ".class",
        ".js", ".jsx", ".ts", ".tsx", ".mjs",
        ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp",
        ".go", ".rs", ".rb", ".php", ".swift",
        ".kt", ".kts", ".scala",
        ".sh", ".bash", ".zsh",
        ".yaml", ".yml", ".json", ".xml", ".toml", ".ini", ".cfg"
    ]

    for ext in extensions_to_strip:
        if normalized.endswith(ext):
            normalized = normalized[:-len(ext)]
            break

    # Final cleanup: ensure no double slashes remain
    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    return normalized


def normalize_paths(paths: list) -> list:
    """
    Normalize a list of paths.

    Args:
        paths: List of paths (strings or Path objects)

    Returns:
        List of normalized path strings
    """
    return [normalize_path(p) for p in paths]


def get_extension(path: Union[str, Path]) -> str:
    """
    Extract the file extension from a path.

    Args:
        path: Input path

    Returns:
        Lowercase extension including the dot (e.g., '.py'), or empty string if none
    """
    normalized = str(path).lower()
    # Find the last dot
    last_dot = normalized.rfind(".")
    if last_dot == -1 or last_dot == 0 or last_dot == len(normalized) - 1:
        return ""
    return normalized[last_dot:]


def is_python_file(path: Union[str, Path]) -> bool:
    """
    Check if a path represents a Python file.

    Args:
        path: Input path

    Returns:
        True if the file has a Python extension
    """
    return get_extension(path) in [".py", ".pyc", ".pyo", ".pyd"]


def compare_paths(path1: Union[str, Path], path2: Union[str, Path]) -> bool:
    """
    Compare two paths for equality after normalization.

    Args:
        path1: First path
        path2: Second path

    Returns:
        True if paths are equal after normalization
    """
    return normalize_path(path1) == normalize_path(path2)


def normalize_git_path(git_path: str) -> str:
    """
    Specialized normalization for paths from git output.

    Git paths may have special characters or encoding issues that need handling.

    Args:
        git_path: Raw path from git

    Returns:
        Normalized path string
    """
    if not git_path:
        return ""

    # Handle git's quote escaping for special characters
    if git_path.startswith('"') and git_path.endswith('"'):
        # Git quotesPaths with special characters
        try:
            # Remove quotes and decode escape sequences
            git_path = git_path[1:-1].encode().decode('unicode_escape')
        except (UnicodeDecodeError, AttributeError):
            pass

    return normalize_path(git_path)