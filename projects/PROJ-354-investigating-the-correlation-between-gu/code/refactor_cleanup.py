"""
Code cleanup and refactoring utilities for the Gut Microbiome-Cognitive Correlation Study.

This module provides tools to:
- Remove unused imports from Python files
- Standardize docstrings across the codebase
- Ensure logging consistency
- Validate file structure
- Clean up temporary files
"""

import ast
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from utils.logging import get_logger, log_exception

logger = get_logger(__name__)


def remove_unused_imports(file_path: Path) -> bool:
    """
    Remove unused imports from a Python file.
    
    Args:
        file_path: Path to the Python file to clean up
        
    Returns:
        True if changes were made, False otherwise
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        tree = ast.parse(content)
        
        # Find all names used in the module
        used_names = set()
        
        class NameVisitor(ast.NodeVisitor):
            def visit_Name(self, node):
                used_names.add(node.id)
                self.generic_visit(node)
            
            def visit_Attribute(self, node):
                # Handle attribute access like os.path.join
                current = node
                parts = []
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                    # Add the base name and the full path
                    used_names.add(current.id)
                self.generic_visit(node)
        
        NameVisitor().visit(tree)
        
        # Find import statements
        imports_to_remove = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    if name not in used_names:
                        imports_to_remove.append((node.lineno, node.col_offset, len(node.names)))
            
            elif isinstance(node, ast.ImportFrom):
                names_to_check = []
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    names_to_check.append((alias.name, name))
                
                unused = [name for _, name in names_to_check if name not in used_names]
                if unused:
                    # Mark the whole import line for removal if all are unused
                    # or create a new import line with only used names
                    imports_to_remove.append((node.lineno, node.col_offset, unused, node.module))
        
        if not imports_to_remove:
            return False
        
        # Sort by line number in reverse order to avoid line number shifts
        lines = content.splitlines(keepends=True)
        
        # Handle ImportFrom specially - rewrite with only used imports
        from_imports = [item for item in imports_to_remove if isinstance(item[2], list)]
        regular_imports = [item for item in imports_to_remove if isinstance(item[2], int)]
        
        # Remove regular imports
        for lineno, col, count in sorted(regular_imports, reverse=True):
            # Remove the entire import line
            if lineno - 1 < len(lines):
                del lines[lineno - 1]
        
        # Rewrite ImportFrom statements with only used imports
        for lineno, col, unused_names, module in sorted(from_imports, reverse=True):
            if lineno - 1 < len(lines):
                # This is a simplified approach - in practice, we'd need to parse
                # the specific line to reconstruct it properly
                # For now, we'll just remove lines that are clearly import statements
                # with unused imports
                pass
        
        # For a more robust solution, we'd need to reconstruct the AST
        # and write it back, which is complex. For now, we'll use a simpler approach:
        # Just remove lines that are clearly unused imports based on simple heuristics
        
        new_content = ''.join(lines)
        if new_content != content:
            file_path.write_text(new_content, encoding='utf-8')
            logger.info(f"Removed unused imports from {file_path}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        log_exception(e)
        return False


def standardize_docstrings(file_path: Path) -> bool:
    """
    Standardize docstrings to follow a consistent format.
    
    Args:
        file_path: Path to the Python file to update
        
    Returns:
        True if changes were made, False otherwise
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Pattern to match docstrings
        docstring_pattern = r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')'
        
        # Standard format:
        # """
        # Brief description.
        #
        # Args:
        #     param1: Description
        #
        # Returns:
        #     Description
        # """
        
        # This is a simplified implementation
        # A full implementation would need to parse the AST and reconstruct docstrings
        
        # For now, we'll just ensure docstrings start and end on their own lines
        # and have consistent quote style
        
        lines = content.splitlines(keepends=True)
        modified = False
        
        in_docstring = False
        docstring_start = -1
        quote_style = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    in_docstring = True
                    docstring_start = i
                    quote_style = '"""' if stripped.startswith('"""') else "'''"
            else:
                if quote_style in stripped:
                    in_docstring = False
                    # Ensure docstring ends properly
                    if not stripped.endswith(quote_style):
                        # This is a complex case, skip for now
                        pass
        
        # For a complete implementation, we would need to:
        # 1. Parse the AST
        # 2. Extract docstrings
        # 3. Reformat them
        # 4. Reconstruct the file
        
        # This is a placeholder for the full implementation
        logger.info(f"Docstring standardization for {file_path} requires full AST-based implementation")
        
        return False
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        log_exception(e)
        return False


def ensure_logging_consistency(file_path: Path) -> bool:
    """
    Ensure logging calls follow consistent patterns.
    
    Args:
        file_path: Path to the Python file to check
        
    Returns:
        True if changes were made, False otherwise
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check for common logging issues:
        # 1. Missing logger initialization
        # 2. Inconsistent log levels
        # 3. Print statements that should be logging
        
        has_logger_init = 'logger = get_logger' in content or 'logging.getLogger' in content
        has_print = 'print(' in content
        
        changes_made = False
        
        if has_print and not has_logger_init:
            logger.warning(f"File {file_path} has print statements but no logger initialization")
            changes_made = True
        
        # Check for inconsistent log level usage
        log_levels = ['debug', 'info', 'warning', 'error', 'critical']
        found_levels = [level for level in log_levels if f'logger.{level}(' in content]
        
        # Ensure proper log level usage
        # (This is a simplified check)
        
        if changes_made:
            logger.info(f"Logging consistency check completed for {file_path}")
        
        return changes_made
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        log_exception(e)
        return False


def validate_file_structure(root_dir: Path) -> Dict[str, Any]:
    """
    Validate the project file structure.
    
    Args:
        root_dir: Root directory of the project
        
    Returns:
        Dictionary containing validation results
    """
    results = {
        'valid': True,
        'missing_dirs': [],
        'missing_files': [],
        'extra_files': []
    }
    
    required_dirs = [
        'code',
        'data',
        'data/raw',
        'data/processed',
        'results',
        'results/associations',
        'results/sensitivity',
        'results/plots',
        'results/validation',
        'tests',
        'docs'
    ]
    
    required_files = [
        'requirements.txt',
        'README.md',
        'quickstart.md',
        'code/config.py',
        'code/analysis.py',
        'code/download.py',
        'code/preprocess.py',
        'code/visualize.py',
        'code/power_analysis.py',
        'code/refactor_cleanup.py'
    ]
    
    # Check directories
    for dir_path in required_dirs:
        full_path = root_dir / dir_path
        if not full_path.exists():
            results['missing_dirs'].append(dir_path)
            results['valid'] = False
            logger.warning(f"Missing directory: {full_path}")
    
    # Check files
    for file_path in required_files:
        full_path = root_dir / file_path
        if not full_path.exists():
            results['missing_files'].append(file_path)
            results['valid'] = False
            logger.warning(f"Missing file: {full_path}")
    
    # Check for unexpected files in sensitive directories
    sensitive_dirs = ['data/raw', 'data/processed', 'results']
    for sensitive_dir in sensitive_dirs:
        dir_path = root_dir / sensitive_dir
        if dir_path.exists():
            for item in dir_path.iterdir():
                if item.is_file() and item.name.startswith('.'):
                    results['extra_files'].append(str(item))
                    logger.warning(f"Unexpected file in {sensitive_dir}: {item}")
    
    return results


def cleanup_temp_files(root_dir: Path) -> int:
    """
    Remove temporary and backup files from the project.
    
    Args:
        root_dir: Root directory of the project
        
    Returns:
        Number of files removed
    """
    temp_patterns = [
        '*.pyc',
        '__pycache__',
        '*.pyo',
        '*.pyd',
        '.DS_Store',
        '*.swp',
        '*.swo',
        '*~',
        '*.bak',
        '*.tmp'
    ]
    
    removed_count = 0
    
    for pattern in temp_patterns:
        for file_path in root_dir.rglob(pattern):
            try:
                if file_path.is_file():
                    file_path.unlink()
                    removed_count += 1
                    logger.debug(f"Removed temp file: {file_path}")
                elif file_path.is_dir():
                    import shutil
                    shutil.rmtree(file_path)
                    removed_count += 1
                    logger.debug(f"Removed temp directory: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove {file_path}: {e}")
    
    if removed_count > 0:
        logger.info(f"Removed {removed_count} temporary files/directories")
    
    return removed_count


def run_cleanup_pipeline(root_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """
    Run the complete cleanup and refactoring pipeline.
    
    Args:
        root_dir: Root directory of the project
        dry_run: If True, only report what would be done
        
    Returns:
        Dictionary containing cleanup results
    """
    results = {
        'files_processed': 0,
        'files_modified': 0,
        'temp_files_removed': 0,
        'structure_valid': False,
        'errors': []
    }
    
    try:
        # Validate file structure
        structure_results = validate_file_structure(root_dir)
        results['structure_valid'] = structure_results['valid']
        
        if not results['structure_valid']:
            results['errors'].append({
                'type': 'structure',
                'details': structure_results
            })
        
        # Clean up temp files
        if not dry_run:
            results['temp_files_removed'] = cleanup_temp_files(root_dir)
        else:
            # Count temp files without removing
            temp_patterns = ['*.pyc', '__pycache__', '*.pyo', '*.bak', '*.tmp']
            count = 0
            for pattern in temp_patterns:
                count += len(list(root_dir.rglob(pattern)))
            results['temp_files_removed'] = count
        
        # Process Python files
        python_files = list(root_dir.rglob('*.py'))
        results['files_processed'] = len(python_files)
        
        for py_file in python_files:
            # Skip __init__.py and test files for aggressive cleanup
            if py_file.name.startswith('test_') or py_file.name == '__init__.py':
                continue
            
            try:
                # Remove unused imports
                if not dry_run:
                    if remove_unused_imports(py_file):
                        results['files_modified'] += 1
                
                # Check logging consistency
                ensure_logging_consistency(py_file)
                
            except Exception as e:
                results['errors'].append({
                    'type': 'processing',
                    'file': str(py_file),
                    'error': str(e)
                })
                logger.error(f"Error processing {py_file}: {e}")
        
    except Exception as e:
        results['errors'].append({
            'type': 'pipeline',
            'error': str(e)
        })
        log_exception(e)
    
    return results


def main():
    """Main entry point for the cleanup script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run code cleanup and refactoring')
    parser.add_argument('--dry-run', action='store_true', help='Only report what would be done')
    parser.add_argument('--root', type=str, default='.', help='Project root directory')
    
    args = parser.parse_args()
    
    root_dir = Path(args.root).resolve()
    
    if not root_dir.exists():
        logger.error(f"Root directory does not exist: {root_dir}")
        return 1
    
    logger.info(f"Starting cleanup pipeline for {root_dir}")
    logger.info(f"Dry run: {args.dry_run}")
    
    results = run_cleanup_pipeline(root_dir, dry_run=args.dry_run)
    
    # Log results
    logger.info(f"Files processed: {results['files_processed']}")
    logger.info(f"Files modified: {results['files_modified']}")
    logger.info(f"Temp files removed: {results['temp_files_removed']}")
    logger.info(f"Structure valid: {results['structure_valid']}")
    
    if results['errors']:
        logger.warning(f"Encountered {len(results['errors'])} errors during cleanup")
        for error in results['errors']:
            logger.warning(f"  - {error}")
    
    return 0 if results['structure_valid'] and not results['errors'] else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())