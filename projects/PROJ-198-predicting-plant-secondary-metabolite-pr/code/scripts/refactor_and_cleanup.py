"""
Refactoring and Cleanup Script for PROJ-198

This script performs automated code cleanup and refactoring on the
code/data/ and code/modeling/ directories to improve consistency,
remove dead code, and standardize formatting.

It generates a report of changes made.
"""
import os
import sys
import ast
import logging
import re
from pathlib import Path
from typing import List, Set, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from utils.logging import setup_logging, get_logger
from utils.cleanup_utils import (
    get_all_imports,
    get_used_names,
    is_docstring,
    normalize_log_call,
    safe_parse_source,
    get_indentation,
    is_comment_or_blank,
    extract_function_bodies,
    check_code_quality
)
from config import get_data_path, get_config

@dataclass
class CleanupReport:
    """Report structure for cleanup operations."""
    total_files_processed: int = 0
    files_modified: int = 0
    issues_fixed: int = 0
    unused_imports_removed: int = 0
    dead_code_removed: int = 0
    docstrings_standardized: int = 0
    log_levels_normalized: int = 0
    errors: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)

def validate_syntax(file_path: Path) -> bool:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True
    except SyntaxError as e:
        logging.error(f"Syntax error in {file_path}: {e}")
        return False

def remove_unused_imports(source: str, file_path: Path) -> Tuple[str, int]:
    """Remove unused imports from source code."""
    try:
        tree = ast.parse(source)
        imports = get_all_imports(tree)
        used_names = get_used_names(tree)

        lines = source.splitlines()
        new_lines = []
        removed_count = 0
        in_import_block = False
        current_import_block = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check if line is an import statement
            is_import_line = (
                stripped.startswith('import ') or
                stripped.startswith('from ')
            )

            if is_import_line:
                in_import_block = True
                current_import_block.append((i, line))
            else:
                if in_import_block:
                    # End of import block, process it
                    for line_num, import_line in current_import_block:
                        # Parse this specific import line
                        temp_source = '\n'.join([l for _, l in current_import_block])
                        try:
                            temp_tree = ast.parse(temp_source)
                            local_imports = get_all_imports(temp_tree)

                            should_keep = False
                            for imp in local_imports:
                                name = imp.split('.')[0] if '.' in imp else imp
                                if name in used_names:
                                    should_keep = True
                                    break

                            if should_keep:
                                new_lines.append(import_line)
                            else:
                                removed_count += 1
                        except SyntaxError:
                            new_lines.append(import_line)

                    in_import_block = False
                    current_import_block = []
                    new_lines.append(line)
                else:
                    new_lines.append(line)

        # Handle case where file ends with imports
        if in_import_block:
            for line_num, import_line in current_import_block:
                temp_source = '\n'.join([l for _, l in current_import_block])
                try:
                    temp_tree = ast.parse(temp_source)
                    local_imports = get_all_imports(temp_tree)

                    should_keep = False
                    for imp in local_imports:
                        name = imp.split('.')[0] if '.' in imp else imp
                        if name in used_names:
                            should_keep = True
                            break

                    if should_keep:
                        new_lines.append(import_line)
                    else:
                        removed_count += 1
                except SyntaxError:
                    new_lines.append(import_line)

        return '\n'.join(new_lines), removed_count
    except SyntaxError:
        logging.warning(f"Could not parse {file_path} for unused imports")
        return source, 0

def standardize_docstrings(source: str) -> Tuple[str, int]:
    """Standardize docstrings to use triple double quotes."""
    count = 0
    lines = source.splitlines()
    new_lines = []

    for line in lines:
        # Replace single quote docstrings with double quotes
        if re.match(r'^\s*"""\s*$', line) or re.match(r"^^\s*'''\s*$", line):
            new_lines.append(line.replace("'", '"'))
            count += 1
        elif re.match(r'^\s*"""', line) and not re.match(r'^\s*"""', line):
            # Single line docstring
            new_lines.append(line.replace("'", '"'))
            count += 1
        else:
            new_lines.append(line)

    return '\n'.join(new_lines), count

def normalize_log_levels(source: str) -> Tuple[str, int]:
    """Normalize log level usage to use constants instead of strings."""
    count = 0
    patterns = [
        (r'log\.debug\(\s*["\']', 'log.debug("'),
        (r'log\.info\(\s*["\']', 'log.info("'),
        (r'log\.warning\(\s*["\']', 'log.warning("'),
        (r'log\.error\(\s*["\']', 'log.error("'),
        (r'log\.critical\(\s*["\']', 'log.critical("'),
    ]

    new_source = source
    for pattern, replacement in patterns:
        matches = re.findall(pattern, new_source)
        if matches:
            count += len(matches)

    return new_source, count

def remove_dead_code(source: str, file_path: Path) -> Tuple[str, int]:
    """Remove obvious dead code (unreachable statements after return/break/continue)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source, 0

    lines = source.splitlines()
    new_lines = []
    removed_count = 0
    skip_until_next_def = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check for control flow statements
        if stripped.startswith('return ') or stripped == 'return':
            new_lines.append(line)
            skip_until_next_def = True
            continue

        if stripped.startswith('break') or stripped.startswith('continue'):
            new_lines.append(line)
            skip_until_next_def = True
            continue

        if stripped.startswith('raise ') or stripped.startswith('except'):
            new_lines.append(line)
            skip_until_next_def = False
            continue

        # Skip lines after return/break/continue until next function/class def
        if skip_until_next_def:
            if (stripped.startswith('def ') or
                stripped.startswith('class ') or
                stripped.startswith('@')):
                skip_until_next_def = False
                new_lines.append(line)
            else:
                removed_count += 1
            continue

        new_lines.append(line)

    return '\n'.join(new_lines), removed_count

def process_file(file_path: Path, report: CleanupReport) -> bool:
    """Process a single Python file."""
    if not file_path.suffix == '.py':
        return False

    logging.info(f"Processing {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_source = f.read()

        source = original_source
        total_issues = 0

        # 1. Remove unused imports
        source, removed = remove_unused_imports(source, file_path)
        report.unused_imports_removed += removed
        total_issues += removed

        # 2. Standardize docstrings
        source, removed = standardize_docstrings(source)
        report.docstrings_standardized += removed
        total_issues += removed

        # 3. Normalize log levels
        source, removed = normalize_log_levels(source)
        report.log_levels_normalized += removed
        total_issues += removed

        # 4. Remove dead code
        source, removed = remove_dead_code(source, file_path)
        report.dead_code_removed += removed
        total_issues += removed

        # Validate syntax after changes
        if not validate_syntax(file_path):
            logging.error(f"Syntax validation failed for {file_path} after modifications")
            report.errors.append(f"Syntax error in {file_path}")
            return False

        # Write back if changed
        if source != original_source:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(source)
            report.files_modified += 1
            report.modified_files.append(str(file_path))
            report.issues_fixed += total_issues
            logging.info(f"Modified {file_path} - fixed {total_issues} issues")
            return True
        else:
            logging.info(f"No changes needed for {file_path}")
            return False

    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        report.errors.append(f"Error in {file_path}: {str(e)}")
        return False

def main():
    """Main entry point for the cleanup script."""
    logger = setup_logging("cleanup", log_level=logging.INFO)

    report = CleanupReport()

    # Define directories to process
    base_path = Path(__file__).parent.parent
    data_dir = base_path / 'data'
    modeling_dir = base_path / 'modeling'

    directories_to_process = []

    if data_dir.exists():
        directories_to_process.append(data_dir)
    else:
        logging.warning(f"Directory not found: {data_dir}")

    if modeling_dir.exists():
        directories_to_process.append(modeling_dir)
    else:
        logging.warning(f"Directory not found: {modeling_dir}")

    if not directories_to_process:
        logging.error("No valid directories to process")
        return report

    # Process all Python files
    for directory in directories_to_process:
        for py_file in directory.rglob('*.py'):
            report.total_files_processed += 1
            process_file(py_file, report)

    # Generate summary
    logging.info("=" * 50)
    logging.info("CLEANUP REPORT")
    logging.info("=" * 50)
    logging.info(f"Total files processed: {report.total_files_processed}")
    logging.info(f"Files modified: {report.files_modified}")
    logging.info(f"Issues fixed: {report.issues_fixed}")
    logging.info(f"  - Unused imports removed: {report.unused_imports_removed}")
    logging.info(f"  - Dead code removed: {report.dead_code_removed}")
    logging.info(f"  - Docstrings standardized: {report.docstrings_standardized}")
    logging.info(f"  - Log levels normalized: {report.log_levels_normalized}")

    if report.errors:
        logging.warning(f"Errors encountered: {len(report.errors)}")
        for err in report.errors:
            logging.warning(f"  - {err}")

    if report.modified_files:
        logging.info("Modified files:")
        for f in report.modified_files:
            logging.info(f"  - {f}")

    return report

if __name__ == '__main__':
    main()