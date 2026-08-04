"""
Utility functions for code refactoring and cleanup.

This module provides helper functions for:
- Code analysis
- Pattern matching
- File manipulation
- Import validation
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
import logging

from utils.logging import get_logger

logger = get_logger(__name__)

# Common patterns for code quality checks
COMMON_PATTERNS = {
    'placeholder': [
        r'#\s*TODO:',
        r'#\s*FIXME:',
        r'#\s*XXX:',
        r'#\s*HACK:',
        r'raise\s+NotImplementedError',
    ],
    'unused_variable': [
        r'^\s*#\s*unused',
        r'^\s*#\s*noqa:\s*F841',
    ],
    'duplicate_import': [
        r'^(import\s+\w+|from\s+\w+\s+import\s+\w+)',
    ],
    'magic_number': [
        r'(?<!["\'])\b([0-9]+\.?[0-9]*)\b(?!["\'])',
    ],
}

def analyze_code_quality(file_path: Path) -> Dict[str, List[str]]:
    """
    Analyze a Python file for code quality issues.
    
    Args:
        file_path: Path to the Python file
    
    Returns:
        Dictionary with issue types as keys and lists of issues as values
    """
    issues = {
        'placeholders': [],
        'unused_variables': [],
        'duplicate_imports': [],
        'magic_numbers': [],
        'complex_functions': [],
        'long_lines': [],
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for placeholder patterns
        for i, line in enumerate(lines, 1):
            for pattern in COMMON_PATTERNS['placeholder']:
                if re.search(pattern, line, re.IGNORECASE):
                    issues['placeholders'].append(f"Line {i}: {line.strip()}")
        
        # Check for long lines (> 120 characters)
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues['long_lines'].append(f"Line {i}: {len(line)} characters")
        
        # Check for magic numbers (excluding 0, 1, 2)
        for i, line in enumerate(lines, 1):
            if 'def ' in line or 'class ' in line:
                continue
            matches = re.findall(r'(?<!["\'])\b([3-9]\d*|1\d{2,})\b(?!["\'])', line)
            for match in matches:
                issues['magic_numbers'].append(f"Line {i}: {match}")
        
        # Check function complexity
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Simple complexity check based on number of lines
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno + 10
                    line_count = end_line - node.lineno
                    if line_count > 50:
                        issues['complex_functions'].append(
                            f"Function {node.name} at line {node.lineno}: {line_count} lines"
                        )
        except SyntaxError as e:
            issues['complex_functions'].append(f"Syntax error in {file_path}: {e}")
    
    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
    
    return issues

def extract_imports(file_path: Path) -> Tuple[List[str], List[str]]:
    """
    Extract all imports from a Python file.
    
    Args:
        file_path: Path to the Python file
    
    Returns:
        Tuple of (standard_imports, from_imports)
    """
    standard_imports = []
    from_imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    standard_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    from_imports.append(f"{module}.{alias.name}")
    
    except Exception as e:
        logger.error(f"Error extracting imports from {file_path}: {e}")
    
    return standard_imports, from_imports

def validate_imports(file_path: Path, allowed_modules: Set[str]) -> List[str]:
    """
    Validate that imports are from allowed modules.
    
    Args:
        file_path: Path to the Python file
        allowed_modules: Set of allowed module names
    
    Returns:
        List of invalid imports
    """
    invalid_imports = []
    standard_imports, from_imports = extract_imports(file_path)
    
    for imp in standard_imports:
        # Extract base module name
        base_module = imp.split('.')[0]
        if base_module not in allowed_modules and not base_module.startswith('_'):
            invalid_imports.append(f"Import: {imp}")
    
    for imp in from_imports:
        # Extract base module name
        base_module = imp.split('.')[0]
        if base_module not in allowed_modules and not base_module.startswith('_'):
            invalid_imports.append(f"From import: {imp}")
    
    return invalid_imports

def format_code(content: str) -> str:
    """
    Format code content with standard formatting rules.
    
    Args:
        content: Python code content
    
    Returns:
        Formatted code content
    """
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        # Strip trailing whitespace
        line = line.rstrip()
        
        # Ensure consistent indentation (4 spaces)
        if line.strip():
            # Count leading spaces
            leading_spaces = len(line) - len(line.lstrip())
            # Ensure it's a multiple of 4
            if leading_spaces % 4 != 0:
                # Round to nearest multiple of 4
                new_spaces = ((leading_spaces + 2) // 4) * 4
                line = ' ' * new_spaces + line.lstrip()
        
        formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

def remove_duplicate_lines(content: str) -> str:
    """
    Remove consecutive duplicate lines.
    
    Args:
        content: Python code content
    
    Returns:
        Content with duplicate lines removed
    """
    lines = content.split('\n')
    result = []
    prev_line = None
    
    for line in lines:
        if line != prev_line or line.strip() == '':
            result.append(line)
        prev_line = line
    
    return '\n'.join(result)

def add_missing_docstrings(content: str) -> str:
    """
    Add missing docstrings to functions and classes.
    
    Args:
        content: Python code content
    
    Returns:
        Content with added docstrings
    """
    try:
        tree = ast.parse(content)
        lines = content.split('\n')
        new_lines = []
        
        for i, node in enumerate(ast.walk(tree)):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                # Check if node has a docstring
                if not ast.get_docstring(node):
                    # Add a placeholder docstring
                    indent = ' ' * (node.col_offset)
                    docstring = f'{indent}"""TODO: Add docstring."""'
                    # Insert after the definition line
                    # This is a simplified approach
                    pass
        
        return content
    
    except SyntaxError:
        return content

def get_code_statistics(file_path: Path) -> Dict[str, int]:
    """
    Get basic statistics about a Python file.
    
    Args:
        file_path: Path to the Python file
    
    Returns:
        Dictionary with file statistics
    """
    stats = {
        'total_lines': 0,
        'code_lines': 0,
        'comment_lines': 0,
        'blank_lines': 0,
        'functions': 0,
        'classes': 0,
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        stats['total_lines'] = len(lines)
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                stats['blank_lines'] += 1
            elif stripped.startswith('#'):
                stats['comment_lines'] += 1
            else:
                stats['code_lines'] += 1
        
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                stats['functions'] += 1
            elif isinstance(node, ast.ClassDef):
                stats['classes'] += 1
    
    except Exception as e:
        logger.error(f"Error getting statistics for {file_path}: {e}")
    
    return stats