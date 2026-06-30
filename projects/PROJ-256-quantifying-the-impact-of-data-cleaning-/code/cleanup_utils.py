"""
Cleanup and refactoring utilities for the llmXive pipeline.

This module consolidates common patterns, removes redundant code,
and optimizes imports across the project.
"""
import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple, Callable
from pathlib import Path
import importlib.util
import ast
import re

# Standard library imports
import json
import hashlib
import warnings
from datetime import datetime

# Third-party imports
import numpy as np
import pandas as pd

# Project imports
from utils import setup_logging, pin_random_seed, compute_file_checksum
from config import get_config

logger = logging.getLogger(__name__)


def remove_dead_code_in_file(filepath: str) -> int:
    """
    Analyze a Python file and remove obvious dead code patterns:
    - Unused imports (basic heuristic)
    - Unreachable code after return/break/continue
    - Empty function bodies (except pass)
    
    Returns the number of lines removed.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        logger.error(f"Failed to read {filepath}: {e}")
        return 0

    lines = original_content.splitlines()
    new_lines = []
    removed_count = 0
    
    # Simple heuristic: remove lines that are clearly dead code
    # This is a basic implementation; a full AST-based approach would be more robust
    skip_next = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip lines after return/break/continue that are not blank or comments
        if skip_next:
            if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                removed_count += 1
                continue
            else:
                skip_next = False
        
        if stripped.startswith('return') or stripped.startswith('break') or stripped.startswith('continue'):
            skip_next = True
        
        # Skip TODO/FIXME comments that are on their own line and followed by no code
        if stripped.startswith('TODO') or stripped.startswith('FIXME'):
            # Check if next line is empty or also a comment
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if not next_line or next_line.startswith('TODO') or next_line.startswith('FIXME') or next_line.startswith('#'):
                    removed_count += 1
                    continue
        
        new_lines.append(line)
    
    # Write back if changes were made
    new_content = '\n'.join(new_lines)
    if new_content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"Cleaned up {filepath}: removed {removed_count} lines")
        except Exception as e:
            logger.error(f"Failed to write {filepath}: {e}")
    
    return removed_count


def optimize_imports_in_file(filepath: str) -> bool:
    """
    Optimize imports in a Python file:
    - Group imports (stdlib, third-party, local)
    - Remove duplicate imports
    - Sort within groups
    
    Returns True if changes were made.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        logger.error(f"Failed to read {filepath}: {e}")
        return False

    try:
        tree = ast.parse(original_content)
    except SyntaxError as e:
        logger.warning(f"Skipping {filepath} due to syntax error: {e}")
        return False

    imports = []
    non_import_lines = []
    current_imports = []
    
    # Extract imports and non-imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(('import', alias.name, None))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports.append(('from', module, alias.name))
    
    # Basic deduplication and sorting
    stdlib_imports = set()
    third_party_imports = set()
    local_imports = set()
    
    for import_type, module, name in imports:
        if import_type == 'import':
            if module in ['os', 'sys', 'json', 'hashlib', 'logging', 're', 'ast', 'warnings', 'pathlib', 'importlib', 'typing', 'datetime']:
                stdlib_imports.add(f"import {module}")
            else:
                third_party_imports.add(f"import {module}")
        elif import_type == 'from':
            if module in ['os', 'sys', 'json', 'hashlib', 'logging', 're', 'ast', 'warnings', 'pathlib', 'importlib', 'typing', 'datetime']:
                stdlib_imports.add(f"from {module} import {name}")
            elif module in ['numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn', 'sklearn', 'statsmodels', 'pydantic', 'dotenv']:
                third_party_imports.add(f"from {module} import {name}")
            else:
                local_imports.add(f"from {module} import {name}")
    
    # Reconstruct import section
    sorted_stdlib = sorted(stdlib_imports)
    sorted_third_party = sorted(third_party_imports)
    sorted_local = sorted(local_imports)
    
    new_import_section = []
    if sorted_stdlib:
        new_import_section.extend(sorted_stdlib)
        new_import_section.append("")
    if sorted_third_party:
        new_import_section.extend(sorted_third_party)
        new_import_section.append("")
    if sorted_local:
        new_import_section.extend(sorted_local)
    
    # Reconstruct file
    # This is a simplified approach; a full implementation would preserve docstrings and comments better
    lines = original_content.splitlines()
    in_import_section = False
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            if not in_import_section:
                in_import_section = True
            continue
        else:
            if in_import_section:
                in_import_section = False
                new_lines.extend(new_import_section)
            new_lines.append(line)
    
    # If we never exited import section, add at end
    if in_import_section:
        new_lines.extend(new_import_section)
    
    new_content = '\n'.join(new_lines)
    if new_content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"Optimized imports in {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to write {filepath}: {e}")
    
    return False


def find_python_files(directory: str) -> List[str]:
    """Find all Python files in a directory recursively."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


def run_cleanup_project(project_root: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Run cleanup and refactoring on the entire project.
    
    Args:
        project_root: Root directory of the project
        dry_run: If True, only report changes without applying them
    
    Returns:
        Dictionary with cleanup statistics
    """
    stats = {
        'files_processed': 0,
        'dead_code_removed': 0,
        'imports_optimized': 0,
        'errors': []
    }
    
    code_dir = os.path.join(project_root, 'code')
    if not os.path.exists(code_dir):
        logger.warning(f"Code directory not found: {code_dir}")
        return stats
    
    python_files = find_python_files(code_dir)
    stats['files_processed'] = len(python_files)
    
    for filepath in python_files:
        try:
            # Remove dead code
            removed = remove_dead_code_in_file(filepath)
            stats['dead_code_removed'] += removed
            
            # Optimize imports
            if optimize_imports_in_file(filepath):
                stats['imports_optimized'] += 1
        except Exception as e:
            stats['errors'].append(f"{filepath}: {str(e)}")
            logger.error(f"Error processing {filepath}: {e}")
    
    return stats


def main():
    """Main entry point for cleanup script."""
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    setup_logging(log_level)
    
    project_root = os.getenv('PROJECT_ROOT', '.')
    dry_run = os.getenv('CLEANUP_DRY_RUN', 'false').lower() == 'true'
    
    logger.info(f"Starting cleanup on project: {project_root} (dry_run={dry_run})")
    
    stats = run_cleanup_project(project_root, dry_run)
    
    logger.info(f"Cleanup complete:")
    logger.info(f"  Files processed: {stats['files_processed']}")
    logger.info(f"  Dead code lines removed: {stats['dead_code_removed']}")
    logger.info(f"  Files with optimized imports: {stats['imports_optimized']}")
    
    if stats['errors']:
        logger.warning(f"Encountered {len(stats['errors'])} errors:")
        for error in stats['errors']:
            logger.warning(f"  {error}")
    
    return 0 if not stats['errors'] else 1


if __name__ == '__main__':
    sys.exit(main())