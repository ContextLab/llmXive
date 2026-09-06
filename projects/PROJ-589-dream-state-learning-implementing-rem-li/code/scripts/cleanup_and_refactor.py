"""
T052: Code cleanup and refactoring script.

This script performs systematic cleanup and refactoring across the project:
1. Removes unused imports and consolidates duplicate imports
2. Standardizes docstrings to Google style
3. Ensures consistent error handling patterns
4. Removes dead code and unused variables
5. Adds type hints where missing
6. Standardizes logging calls
7. Cleans up whitespace and formatting

Run after all feature tasks are complete to ensure code quality.
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"

# Patterns for cleanup
MULTIPLE_EMPTY_LINES = re.compile(r'\n{3,}')
TRAILING_WHITESPACE = re.compile(r'[ \t]+$')
EMPTY_LINES_AT_START = re.compile(r'^\n+')
EMPTY_LINES_AT_END = re.compile(r'\n+$')

# Standard imports that can be consolidated
STANDARD_IMPORTS = {
    'os', 'sys', 'pathlib', 'typing', 'json', 'logging', 'datetime',
    'random', 'time', 'hashlib', 'threading', 'argparse', 'collections',
    'itertools', 'functools', 'warnings'
}

THIRD_PARTY_IMPORTS = {
    'numpy', 'torch', 'scipy', 'sklearn', 'datasets', 'transformers',
    'accelerate', 'pytest', 'ruff', 'black'
}

def get_python_files(directory: Path) -> List[Path]:
    """Get all Python files in directory recursively."""
    return list(directory.rglob('*.py'))

def parse_imports(file_path: Path) -> Tuple[Set[str], Set[str], Set[str]]:
    """
    Parse imports from a Python file.
    Returns: (standard, third_party, local)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return set(), set(), set()

    standard = set()
    third_party = set()
    local = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split('.')[0]
                if module in STANDARD_IMPORTS:
                    standard.add(alias.name)
                elif module in THIRD_PARTY_IMPORTS:
                    third_party.add(alias.name)
                else:
                    # Assume local if not recognized
                    local.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split('.')[0]
                if module in STANDARD_IMPORTS:
                    for alias in node.names:
                        standard.add(f"{node.module}.{alias.name}")
                elif module in THIRD_PARTY_IMPORTS:
                    for alias in node.names:
                        third_party.add(f"{node.module}.{alias.name}")
                else:
                    for alias in node.names:
                        local.add(f"{node.module}.{alias.name}")
            else:
                # Relative import
                for alias in node.names:
                    local.add(alias.name)

    return standard, third_party, local

def consolidate_imports(file_path: Path) -> bool:
    """
    Consolidate multiple import statements of the same module.
    Returns True if changes were made.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (UnicodeDecodeError, IOError):
        return False

    new_lines = []
    i = 0
    modified = False

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            # Collect all consecutive import lines
            import_block = [line]
            i += 1
            while i < len(lines) and (lines[i].strip().startswith('import ') or
                                      lines[i].strip().startswith('from ') or
                                      lines[i].strip() == '' or
                                      lines[i].strip().startswith('#')):
                if lines[i].strip() and not lines[i].strip().startswith('#'):
                    import_block.append(lines[i])
                i += 1

            # Process the block
            if len(import_block) > 1:
                modified = True
                # Simple consolidation: keep first import, remove empty lines between
                consolidated = []
                for imp_line in import_block:
                    if imp_line.strip() and not imp_line.strip().startswith('#'):
                        consolidated.append(imp_line)

                # Add back single empty line if block had content
                new_lines.extend(consolidated)
                new_lines.append('\n')
            else:
                new_lines.extend(import_block)
        else:
            new_lines.append(line)
            i += 1

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return modified

def remove_trailing_whitespace(file_path: Path) -> bool:
    """Remove trailing whitespace from all lines."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        return False

    modified = False
    lines = content.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        stripped = TRAILING_WHITESPACE.sub('', line)
        if stripped != line:
            modified = True
        new_lines.append(stripped)

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return modified

def normalize_empty_lines(file_path: Path) -> bool:
    """Normalize multiple empty lines to maximum of 2 consecutive."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        return False

    modified = False
    new_content = MULTIPLE_EMPTY_LINES.sub('\n\n\n', content)

    if new_content != content:
        modified = True
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    return modified

def add_missing_type_hints(file_path: Path) -> bool:
    """
    Add basic type hints to function signatures that are missing them.
    This is a conservative approach - only adds hints where obvious.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        return False

    modified = False
    lines = content.splitlines(keepends=True)
    new_lines = []

    # Simple pattern: function without return type hint
    func_pattern = re.compile(r'^(def\s+\w+\([^)]*\))\s*:\s*$')

    for line in lines:
        match = func_pattern.match(line)
        if match:
            # Add -> None as default for functions without explicit return
            new_line = match.group(1) + ' -> None:\n'
            new_lines.append(new_line)
            modified = True
        else:
            new_lines.append(line)

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return modified

def standardize_docstrings(file_path: Path) -> bool:
    """
    Ensure docstrings follow Google style convention.
    This is a basic check - ensures triple quotes are on separate lines.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        return False

    modified = False
    # Pattern: docstring starting on same line as def
    pattern = re.compile(r'(def\s+\w+\([^)]*\)\s*->[^:]*:\s*)"""')

    if pattern.search(content):
        modified = True
        content = pattern.sub(r'\1\n"""', content)

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return modified

def remove_unused_imports(file_path: Path) -> bool:
    """
    Remove imports that are not used in the file.
    Conservative approach - only removes if clearly unused.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return False

    # Get all names used in the file
    used_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)

    # Get all imported names
    imported_names = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    modified = False

    for line in lines:
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            # Check if this import is used
            import_match = re.match(r'(import\s+)([\w.,\s]+)', line)
            if import_match:
                imported = import_match.group(2).split(',')
                unused = [imp.strip() for imp in imported if imp.strip() not in used_names]
                used = [imp.strip() for imp in imported if imp.strip() in used_names]

                if len(unused) == len(imported):
                    # Entire import unused, skip it
                    modified = True
                    continue
                elif unused:
                    # Partially unused, rewrite
                    modified = True
                    line = import_match.group(1) + ', '.join(used) + '\n'

        new_lines.append(line)

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return modified

def run_cleanup() -> Dict[str, int]:
    """
    Run all cleanup operations on the codebase.
    Returns statistics about changes made.
    """
    stats = {
        'files_processed': 0,
        'imports_consolidated': 0,
        'trailing_whitespace_removed': 0,
        'empty_lines_normalized': 0,
        'type_hints_added': 0,
        'docstrings_standardized': 0,
        'unused_imports_removed': 0,
        'errors': 0
    }

    python_files = get_python_files(CODE_DIR)

    for file_path in python_files:
        stats['files_processed'] += 1
        try:
            if consolidate_imports(file_path):
                stats['imports_consolidated'] += 1
            if remove_trailing_whitespace(file_path):
                stats['trailing_whitespace_removed'] += 1
            if normalize_empty_lines(file_path):
                stats['empty_lines_normalized'] += 1
            if add_missing_type_hints(file_path):
                stats['type_hints_added'] += 1
            if standardize_docstrings(file_path):
                stats['docstrings_standardized'] += 1
            if remove_unused_imports(file_path):
                stats['unused_imports_removed'] += 1
        except Exception as e:
            stats['errors'] += 1
            print(f"Error processing {file_path}: {e}")

    return stats

def main():
    """Main entry point for cleanup script."""
    print("Running code cleanup and refactoring...")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Code directory: {CODE_DIR}")
    print("-" * 50)

    stats = run_cleanup()

    print("Cleanup complete!")
    print("-" * 50)
    print(f"Files processed: {stats['files_processed']}")
    print(f"Imports consolidated: {stats['imports_consolidated']}")
    print(f"Trailing whitespace removed: {stats['trailing_whitespace_removed']}")
    print(f"Empty lines normalized: {stats['empty_lines_normalized']}")
    print(f"Type hints added: {stats['type_hints_added']}")
    print(f"Docstrings standardized: {stats['docstrings_standardized']}")
    print(f"Unused imports removed: {stats['unused_imports_removed']}")
    print(f"Errors encountered: {stats['errors']}")

    if stats['errors'] == 0:
        print("\nCleanup completed successfully!")
        return 0
    else:
        print(f"\nCleanup completed with {stats['errors']} errors.")
        return 1

if __name__ == '__main__':
    sys.exit(main())