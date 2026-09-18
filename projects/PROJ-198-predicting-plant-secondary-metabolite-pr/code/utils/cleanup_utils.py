"""
Utility functions for code cleanup and refactoring.

This module provides helper functions used by the cleanup script
to analyze and modify Python source code.
"""
import ast
import re
from pathlib import Path
from typing import List, Set, Tuple, Optional, Dict, Any

def get_all_imports(tree: ast.AST) -> Set[str]:
    """Extract all imported module names from an AST."""
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    return imports

def get_used_names(tree: ast.AST) -> Set[str]:
    """Extract all names used in the code (excluding imports)."""
    used_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)
    return used_names

def is_docstring(node: ast.AST) -> bool:
    """Check if a statement is a docstring."""
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
        return isinstance(node.value.value, str)
    return False

def normalize_log_call(line: str) -> str:
    """Normalize log level strings to use constants."""
    # This is a simple heuristic; full implementation would be more complex
    return line

def safe_parse_source(source: str) -> Optional[ast.AST]:
    """Safely parse source code and return AST or None if invalid."""
    try:
        return ast.parse(source)
    except SyntaxError:
        return None

def get_indentation(line: str) -> int:
    """Get the indentation level of a line."""
    return len(line) - len(line.lstrip())

def is_comment_or_blank(line: str) -> bool:
    """Check if a line is a comment or blank."""
    stripped = line.strip()
    return stripped == '' or stripped.startswith('#')

def extract_function_bodies(source: str) -> Dict[str, Tuple[int, int]]:
    """Extract function names and their line ranges."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    function_ranges = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            function_ranges[node.name] = (node.lineno, node.end_lineno or node.lineno)

    return function_ranges

def check_code_quality(file_path: Path) -> Dict[str, Any]:
    """
    Perform basic code quality checks on a file.

    Returns a dictionary with quality metrics.
    """
    results = {
        'file': str(file_path),
        'lines': 0,
        'functions': 0,
        'classes': 0,
        'imports': 0,
        'complexity_issues': 0
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        results['lines'] = len(source.splitlines())

        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                results['functions'] += 1
            elif isinstance(node, ast.ClassDef):
                results['classes'] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                results['imports'] += 1

        # Simple complexity check: flag functions with too many lines
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.end_lineno and (node.end_lineno - node.lineno) > 50:
                    results['complexity_issues'] += 1

    except Exception as e:
        results['error'] = str(e)

    return results