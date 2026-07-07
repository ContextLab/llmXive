"""
Code cleanup and refactoring utilities for the exoplanet atmosphere pipeline.

This module consolidates common refactoring patterns, improves code consistency,
and provides helper functions for cleaning up legacy code patterns identified
during the project lifecycle.
"""
import logging
import re
from typing import List, Dict, Any, Optional, Callable, Union
from pathlib import Path
import ast
import tokenize
import io
import os

from config import get_config
from utils import setup_logging

logger = logging.getLogger(__name__)


def clean_unused_imports(file_path: Path) -> Dict[str, Any]:
    """
    Analyze a Python file and identify unused imports.
    
    Args:
        file_path: Path to the Python file to analyze
        
    Returns:
        Dictionary with analysis results including unused imports list
    """
    result = {
        "file": str(file_path),
        "unused_imports": [],
        "total_imports": 0,
        "errors": []
    }
    
    if not file_path.exists():
        result["errors"].append(f"File not found: {file_path}")
        return result
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Collect all imported names
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name)
        
        result["total_imports"] = len(imported_names)
        
        # Simple heuristic: check if imported name appears elsewhere in code
        # (excluding import lines themselves)
        lines = content.split('\n')
        code_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith('import ') and not stripped.startswith('from '):
                code_lines.append(line)
        
        code_content = '\n'.join(code_lines)
        
        for name in imported_names:
            # Count occurrences in non-import lines
            count = len(re.findall(r'\b' + re.escape(name) + r'\b', code_content))
            if count == 0:
                result["unused_imports"].append(name)
                
    except SyntaxError as e:
        result["errors"].append(f"Syntax error in {file_path}: {str(e)}")
    except Exception as e:
        result["errors"].append(f"Error analyzing {file_path}: {str(e)}")
    
    return result


def refactor_variable_names(
    file_path: Path,
    patterns: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Refactor variable names in a file based on provided patterns.
    
    Args:
        file_path: Path to the Python file
        patterns: List of dictionaries with 'old_pattern' and 'new_name' keys
        
    Returns:
        Dictionary with refactoring results
    """
    result = {
        "file": str(file_path),
        "changes_made": 0,
        "changes": [],
        "errors": []
    }
    
    if not file_path.exists():
        result["errors"].append(f"File not found: {file_path}")
        return result
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for pattern_info in patterns:
            old_pattern = pattern_info.get('old_pattern', '')
            new_name = pattern_info.get('new_name', '')
            
            if not old_pattern or not new_name:
                continue
            
            # Use word boundary matching to avoid partial replacements
            regex = r'\b' + re.escape(old_pattern) + r'\b'
            
            # Count matches
            matches = len(re.findall(regex, content))
            if matches > 0:
                content = re.sub(regex, new_name, content)
                result["changes"].append({
                    "old": old_pattern,
                    "new": new_name,
                    "count": matches
                })
                result["changes_made"] += matches
        
        # Write back only if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
    except Exception as e:
        result["errors"].append(f"Error refactoring {file_path}: {str(e)}")
    
    return result


def standardize_logging_calls(file_path: Path) -> Dict[str, Any]:
    """
    Standardize logging calls to use the module-level logger.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Dictionary with standardization results
    """
    result = {
        "file": str(file_path),
        "changes_made": 0,
        "changes": [],
        "errors": []
    }
    
    if not file_path.exists():
        result["errors"].append(f"File not found: {file_path}")
        return result
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern 1: Replace logging.info/direct calls with logger.info
        # This assumes 'logger' is already defined via setup_logging
        patterns = [
            (r'\blogging\.info\b', 'logger.info'),
            (r'\blogging\.warning\b', 'logger.warning'),
            (r'\blogging\.error\b', 'logger.error'),
            (r'\blogging\.debug\b', 'logger.debug'),
            (r'\blogging\.critical\b', 'logger.critical'),
        ]
        
        for old_pattern, new_pattern in patterns:
            matches = len(re.findall(old_pattern, content))
            if matches > 0:
                content = re.sub(old_pattern, new_pattern, content)
                result["changes"].append({
                    "pattern": old_pattern,
                    "replacement": new_pattern,
                    "count": matches
                })
                result["changes_made"] += matches
        
        # Write back only if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
    except Exception as e:
        result["errors"].append(f"Error standardizing logging in {file_path}: {str(e)}")
    
    return result


def remove_duplicate_imports(file_path: Path) -> Dict[str, Any]:
    """
    Remove duplicate import statements from a file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Dictionary with cleanup results
    """
    result = {
        "file": str(file_path),
        "duplicates_removed": 0,
        "details": [],
        "errors": []
    }
    
    if not file_path.exists():
        result["errors"].append(f"File not found: {file_path}")
        return result
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        seen_imports = {}
        cleaned_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if stripped.startswith('import ') or stripped.startswith('from '):
                # Normalize the import statement
                normalized = stripped
                
                if normalized in seen_imports:
                    result["duplicates_removed"] += 1
                    result["details"].append({
                        "line": i + 1,
                        "import": normalized
                    })
                    continue
                else:
                    seen_imports[normalized] = i + 1
            
            cleaned_lines.append(line)
        
        # Write back only if changes were made
        if len(cleaned_lines) != len(lines):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
                
    except Exception as e:
        result["errors"].append(f"Error removing duplicates in {file_path}: {str(e)}")
    
    return result


def run_code_cleanup(
    directory: Path,
    file_extensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run cleanup operations on all Python files in a directory.
    
    Args:
        directory: Root directory to process
        file_extensions: List of file extensions to process (default: ['.py'])
        
    Returns:
        Dictionary with aggregate cleanup results
    """
    if file_extensions is None:
        file_extensions = ['.py']
    
    result = {
        "directory": str(directory),
        "files_processed": 0,
        "total_changes": 0,
        "files": [],
        "errors": []
    }
    
    if not directory.exists():
        result["errors"].append(f"Directory not found: {directory}")
        return result
    
    # Collect all Python files
    python_files = []
    for ext in file_extensions:
        python_files.extend(directory.rglob(f'*{ext}'))
    
    logger.info(f"Found {len(python_files)} files to process in {directory}")
    
    for file_path in python_files:
        # Skip __pycache__ and other generated directories
        if '__pycache__' in str(file_path):
            continue
        
        file_result = {
            "file": str(file_path),
            "unused_imports": None,
            "logging_standardized": None,
            "duplicates_removed": None
        }
        
        # Analyze unused imports
        unused_result = clean_unused_imports(file_path)
        file_result["unused_imports"] = unused_result["unused_imports"]
        
        # Standardize logging
        logging_result = standardize_logging_calls(file_path)
        file_result["logging_standardized"] = logging_result["changes_made"]
        
        # Remove duplicates
        dup_result = remove_duplicate_imports(file_path)
        file_result["duplicates_removed"] = dup_result["duplicates_removed"]
        
        # Aggregate changes
        total_file_changes = (
            logging_result["changes_made"] + 
            dup_result["duplicates_removed"]
        )
        file_result["total_changes"] = total_file_changes
        result["total_changes"] += total_file_changes
        result["files"].append(file_result)
        result["files_processed"] += 1
        
        if unused_result["errors"]:
            result["errors"].extend(unused_result["errors"])
        if logging_result["errors"]:
            result["errors"].extend(logging_result["errors"])
        if dup_result["errors"]:
            result["errors"].extend(dup_result["errors"])
    
    return result


def main():
    """
    Main entry point for code cleanup and refactoring operations.
    """
    config = get_config()
    setup_logging()
    
    logger.info("Starting code cleanup and refactoring process")
    
    # Define directories to clean up
    code_dir = Path(config.get('project_root', '.')) / 'code'
    tests_dir = Path(config.get('project_root', '.')) / 'tests'
    
    all_results = {
        "code_directory": run_code_cleanup(code_dir),
        "tests_directory": run_code_cleanup(tests_dir)
    }
    
    # Log summary
    total_files = (
        all_results["code_directory"]["files_processed"] + 
        all_results["tests_directory"]["files_processed"]
    )
    total_changes = (
        all_results["code_directory"]["total_changes"] + 
        all_results["tests_directory"]["total_changes"]
    )
    
    logger.info(f"Cleanup complete: {total_files} files processed, {total_changes} changes made")
    
    # Return summary for potential programmatic use
    return all_results


if __name__ == '__main__':
    main()