"""
Refactoring utilities for llmXive project.

This module provides helper functions to clean up and standardize code patterns
across the project, including import consolidation, docstring standardization,
and code formatting helpers.
"""
import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import logging

# Configure logging
logger = logging.getLogger(__name__)

def standardize_docstring(docstring: Optional[str], style: str = "google") -> str:
    """
    Standardize a docstring to a consistent format.
    
    Args:
        docstring: The original docstring or None
        style: The docstring style to use ("google", "numpy", "restructuredtext")
    
    Returns:
        A standardized docstring with consistent formatting
    """
    if not docstring:
        return '"""Module docstring placeholder."""'
    
    # Clean up the docstring
    lines = docstring.strip().split('\n')
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        # Remove leading/trailing whitespace
        line = line.strip()
        
        # Skip empty lines at the start
        if i == 0 and not line:
            continue
        
        # Skip empty lines at the end
        if not line and i == len(lines) - 1:
            continue
        
        cleaned_lines.append(line)
    
    # Join and ensure proper formatting
    result = '"""' + '\n'.join(cleaned_lines) + '"""'
    return result

def consolidate_imports(content: str) -> str:
    """
    Consolidate and sort imports in a Python file.
    
    Args:
        content: The Python file content
    
    Returns:
        Content with consolidated and sorted imports
    """
    lines = content.split('\n')
    imports = []
    other_lines = []
    current_import_block = []
    in_import_block = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if this is an import line
        if stripped.startswith('import ') or stripped.startswith('from '):
            if not in_import_block:
                # Start a new import block
                in_import_block = True
                current_import_block = [line]
            else:
                current_import_block.append(line)
        else:
            if in_import_block:
                # End of import block
                imports.append('\n'.join(current_import_block))
                current_import_block = []
                in_import_block = False
            
            other_lines.append(line)
    
    # Don't forget the last import block
    if in_import_block and current_import_block:
        imports.append('\n'.join(current_import_block))
    
    # Sort import blocks
    imports.sort(key=lambda x: x.lower())
    
    # Reconstruct the file
    result_lines = []
    for imp_block in imports:
        result_lines.append(imp_block)
        result_lines.append('')  # Empty line after imports
    
    result_lines.extend(other_lines)
    
    return '\n'.join(result_lines)

def remove_unused_imports(content: str, used_names: Set[str]) -> str:
    """
    Remove unused imports from Python code.
    
    Args:
        content: The Python file content
        used_names: Set of names that are actually used in the code
    
    Returns:
        Content with unused imports removed
    """
    lines = content.split('\n')
    result_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip import lines that import unused names
        if stripped.startswith('import '):
            # Simple import: import module
            parts = stripped.split('import')
            if len(parts) == 2:
                module_name = parts[1].strip().split()[0] if parts[1].strip() else None
                if module_name and module_name not in used_names:
                    continue  # Skip this import
        
        elif stripped.startswith('from '):
            # From import: from module import name1, name2
            match = re.match(r'from\s+(\S+)\s+import\s+(.+)', stripped)
            if match:
                module = match.group(1)
                imported_names = [name.strip().split(' as ')[0].strip() for name in match.group(2).split(',')]
                used_in_module = [name for name in imported_names if name in used_names]
                
                if not used_in_module:
                    continue  # Skip this entire import line
                elif len(used_in_module) < len(imported_names):
                    # Only keep the used names
                    new_imports = ', '.join(used_in_module)
                    line = f'from {module} import {new_imports}'
        
        result_lines.append(line)
    
    return '\n'.join(result_lines)

def extract_used_names(content: str) -> Set[str]:
    """
    Extract all names used in Python code.
    
    Args:
        content: The Python file content
    
    Returns:
        Set of all names used in the code
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        logger.warning("Could not parse content as valid Python")
        return set()
    
    used_names = set()
    
    class NameVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            used_names.add(node.id)
            self.generic_visit(node)
        
        def visit_Attribute(self, node):
            # Handle attribute access (e.g., os.path)
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)
            self.generic_visit(node)
    
    NameVisitor().visit(tree)
    return used_names

def clean_code_file(file_path: Path, dry_run: bool = True) -> Dict[str, Any]:
    """
    Clean up a single Python file.
    
    Args:
        file_path: Path to the Python file
        dry_run: If True, only analyze without modifying
    
    Returns:
        Dictionary with analysis results
    """
    result = {
        'path': str(file_path),
        'issues_found': [],
        'changes_made': [],
        'success': True
    }
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        result['success'] = False
        result['issues_found'].append(f"Could not read file: {e}")
        return result
    
    # Extract used names
    used_names = extract_used_names(content)
    
    # Check for unused imports
    old_content = content
    content = remove_unused_imports(content, used_names)
    
    if content != old_content:
        result['changes_made'].append("Removed unused imports")
    
    # Consolidate imports
    old_content = content
    content = consolidate_imports(content)
    
    if content != old_content:
        result['changes_made'].append("Consolidated and sorted imports")
    
    # Standardize docstrings (basic check)
    if '"""' in content:
        # Count docstring occurrences to ensure they're properly formatted
        docstring_count = content.count('"""')
        if docstring_count % 2 != 0:
            result['issues_found'].append("Unmatched triple quotes detected")
    
    if not dry_run:
        try:
            file_path.write_text(content, encoding='utf-8')
        except Exception as e:
            result['success'] = False
            result['issues_found'].append(f"Could not write file: {e}")
    
    return result

def refactor_project(code_dir: Path, dry_run: bool = True) -> List[Dict[str, Any]]:
    """
    Refactor all Python files in a directory.
    
    Args:
        code_dir: Path to the code directory
        dry_run: If True, only analyze without modifying
    
    Returns:
        List of results for each file processed
    """
    results = []
    
    if not code_dir.exists():
        logger.error(f"Code directory does not exist: {code_dir}")
        return results
    
    python_files = list(code_dir.glob('**/*.py'))
    
    for py_file in python_files:
        logger.info(f"Processing {py_file}")
        result = clean_code_file(py_file, dry_run)
        results.append(result)
        
        if result['changes_made']:
            logger.info(f"  Changes: {', '.join(result['changes_made'])}")
        if result['issues_found']:
            logger.warning(f"  Issues: {', '.join(result['issues_found'])}")
    
    return results

def main():
    """Main entry point for the refactoring script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Refactor Python code files')
    parser.add_argument('--code-dir', type=Path, default=Path('code'),
                      help='Directory containing Python files to refactor')
    parser.add_argument('--dry-run', action='store_true',
                      help='Only analyze without making changes')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    logger.info(f"Starting refactoring for {args.code_dir}")
    logger.info(f"Dry run mode: {args.dry_run}")
    
    results = refactor_project(args.code_dir, args.dry_run)
    
    total_files = len(results)
    files_with_changes = sum(1 for r in results if r['changes_made'])
    files_with_issues = sum(1 for r in results if r['issues_found'])
    failed_files = sum(1 for r in results if not r['success'])
    
    logger.info(f"Refactoring complete:")
    logger.info(f"  Total files processed: {total_files}")
    logger.info(f"  Files with changes: {files_with_changes}")
    logger.info(f"  Files with issues: {files_with_issues}")
    logger.info(f"  Failed files: {failed_files}")
    
    if failed_files > 0:
        return 1
    return 0

if __name__ == '__main__':
    exit(main())
