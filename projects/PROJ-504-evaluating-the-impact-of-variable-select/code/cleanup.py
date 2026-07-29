"""
Code cleanup and refactoring utility for the llmXive project.

This module provides tools to:
1. Identify Python files in the codebase
2. Check syntax validity
3. Validate docstrings presence
4. Validate API surface consistency
5. Remove debug code (print statements, TODOs, etc.)

Usage:
    python code/cleanup.py [--fix]

The --fix flag will automatically remove debug code and report issues.
Without --fix, it only reports issues without modifying files.
"""

from __future__ import annotations

import ast
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Any

from utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Patterns for debug code detection
DEBUG_PATTERNS = [
    re.compile(r'^\s*print\s*\(', re.MULTILINE),
    re.compile(r'^\s*TODO\b', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*FIXME\b', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*DEBUG\b', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*pdb\.set_trace\(\)', re.MULTILINE),
    re.compile(r'^\s*breakpoint\(\)', re.MULTILINE),
    re.compile(r'^\s*import pdb\b', re.MULTILINE),
    re.compile(r'^\s*ipdb\.set_trace\(\)', re.MULTILINE),
]

# Patterns for unused imports (basic detection)
UNUSED_IMPORT_PATTERN = re.compile(
    r'^\s*(from\s+\S+\s+)?import\s+(\w+)\b',
    re.MULTILINE
)

def get_python_files(root_dir: Path) -> List[Path]:
    """
    Recursively find all Python files in the code directory.
    
    Args:
        root_dir: Root directory to search (typically project root)
        
    Returns:
        List of Path objects for all .py files found
    """
    code_dir = root_dir / "code"
    if not code_dir.exists():
        logger.warning(f"Code directory not found: {code_dir}")
        return []
    
    python_files = []
    for py_file in code_dir.rglob("*.py"):
        # Skip __pycache__ and hidden directories
        if "__pycache__" in str(py_file) or py_file.name.startswith("."):
            continue
        python_files.append(py_file)
    
    logger.info(f"Found {len(python_files)} Python files in {code_dir}")
    return python_files

def check_syntax(file_path: Path) -> tuple[bool, str]:
    """
    Check if a Python file has valid syntax.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def check_docstrings(file_path: Path) -> List[Dict[str, Any]]:
    """
    Check for missing docstrings in functions and classes.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        List of dictionaries with missing docstring info
    """
    issues = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if docstring is None:
                    issues.append({
                        "type": "missing_docstring",
                        "line": node.lineno,
                        "name": node.name,
                        "kind": "class" if isinstance(node, ast.ClassDef) else "function"
                    })
    except Exception as e:
        logger.error(f"Error checking docstrings in {file_path}: {e}")
    
    return issues

def validate_api_surface(file_path: Path, expected_exports: Set[str]) -> List[Dict[str, Any]]:
    """
    Validate that a file's public API matches expected exports.
    
    Args:
        file_path: Path to the Python file
        expected_exports: Set of expected public function/class names
        
    Returns:
        List of validation issues
    """
    issues = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        # Find all public definitions (not starting with _)
        public_names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    public_names.add(node.name)
        
        # Check for missing exports
        missing = expected_exports - public_names
        for name in missing:
            issues.append({
                "type": "missing_export",
                "name": name,
                "message": f"Expected public export '{name}' not found"
            })
        
        # Check for unexpected exports
        unexpected = public_names - expected_exports
        for name in unexpected:
            # Only flag if it looks like it should be private (starts with _)
            # or if it's not a standard Python dunder
            if not name.startswith("_") and not name.startswith("__"):
                issues.append({
                    "type": "unexpected_export",
                    "name": name,
                    "message": f"Unexpected public export '{name}'"
                })
                
    except Exception as e:
        logger.error(f"Error validating API surface in {file_path}: {e}")
    
    return issues

def remove_debug_code(file_path: Path, dry_run: bool = True) -> tuple[int, List[str]]:
    """
    Remove debug code patterns from a file.
    
    Args:
        file_path: Path to the Python file
        dry_run: If True, don't actually modify the file, just report
        
    Returns:
        Tuple of (lines_removed, list_of_removed_lines)
    """
    removed_lines = []
    lines_to_remove = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            for pattern in DEBUG_PATTERNS:
                if pattern.search(line):
                    lines_to_remove.append((i, line.rstrip()))
                    break
        
        if not dry_run and lines_to_remove:
            # Remove lines in reverse order to maintain line numbers
            for line_num, _ in sorted(lines_to_remove, reverse=True):
                del lines[line_num - 1]
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            removed_lines = [line for _, line in lines_to_remove]
        elif lines_to_remove:
            removed_lines = [line for _, line in lines_to_remove]
        
        return len(removed_lines), removed_lines
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return 0, []

def main() -> int:
    """
    Main entry point for the cleanup script.
    
    Returns:
        Exit code (0 for success, 1 for issues found)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Code cleanup and refactoring tool")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Actually remove debug code instead of just reporting"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Project root directory (default: parent of this script's directory)"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting code cleanup and refactoring...")
    
    # Get all Python files
    python_files = get_python_files(args.project_root)
    if not python_files:
        logger.error("No Python files found to process")
        return 1
    
    total_issues = 0
    total_debug_lines = 0
    
    for file_path in python_files:
        logger.info(f"Processing: {file_path}")
        
        # Check syntax
        is_valid, error_msg = check_syntax(file_path)
        if not is_valid:
            logger.error(f"  Syntax error: {error_msg}")
            total_issues += 1
            continue
        
        # Check docstrings
        docstring_issues = check_docstrings(file_path)
        for issue in docstring_issues:
            logger.warning(f"  Missing docstring: {issue['kind']} '{issue['name']}' at line {issue['line']}")
            total_issues += 1
        
        # Remove debug code
        lines_removed, removed_lines = remove_debug_code(file_path, dry_run=not args.fix)
        if lines_removed > 0:
            if args.fix:
                logger.info(f"  Removed {lines_removed} debug lines")
            else:
                logger.info(f"  Found {lines_removed} debug lines (use --fix to remove)")
                for line in removed_lines[:5]:  # Show first 5
                    logger.info(f"    {line}")
                if lines_removed > 5:
                    logger.info(f"    ... and {lines_removed - 5} more")
        total_debug_lines += lines_removed
    
    # Summary
    logger.info("=" * 50)
    logger.info("Cleanup Summary:")
    logger.info(f"  Files processed: {len(python_files)}")
    logger.info(f"  Syntax errors: {total_issues}")
    logger.info(f"  Debug lines found: {total_debug_lines}")
    if args.fix:
        logger.info(f"  Debug lines removed: {total_debug_lines}")
    else:
        logger.info("  Use --fix to remove debug lines")
    
    if total_issues > 0 or total_debug_lines > 0:
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
