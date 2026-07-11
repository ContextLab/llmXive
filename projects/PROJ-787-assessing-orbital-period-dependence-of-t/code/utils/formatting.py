"""
Code formatting utilities to enforce PEP 8 and project-specific style guides.

This module provides functions to:
1. Normalize line endings
2. Enforce line length limits
3. Standardize whitespace
4. Remove trailing whitespace
5. Ensure consistent indentation
"""
import os
import re
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class FormattingReport:
    """Report of formatting changes made to a file."""
    file_path: str
    changes_made: int
    details: List[str]

    def __str__(self) -> str:
        return (f"File: {self.file_path}\n"
                f"  Changes: {self.changes_made}\n"
                f"  Details: {', '.join(self.details[:3])}{'...' if len(self.details) > 3 else ''}")


def normalize_line_endings(content: str) -> Tuple[str, int]:
    """
    Normalize all line endings to Unix style (LF).

    Args:
        content: File content as string

    Returns:
        Tuple of (normalized content, number of changes)
    """
    changes = 0
    # Replace CRLF with LF
    if '\r\n' in content:
        content = content.replace('\r\n', '\n')
        changes += content.count('\n')  # Rough estimate
    # Replace CR with LF
    elif '\r' in content:
        content = content.replace('\r', '\n')
        changes += content.count('\n')

    return content, changes


def enforce_line_length(content: str, max_length: int = 100) -> Tuple[str, int]:
    """
    Enforce maximum line length by warning about violations.

    Note: This function identifies violations but does not automatically fix them
    as automatic line wrapping can break code.

    Args:
        content: File content
        max_length: Maximum allowed line length (default: 100)

    Returns:
        Tuple of (content, number of violations found)
    """
    violations = 0
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        if len(line) > max_length:
            violations += 1
            logger.warning(f"Line {i} exceeds {max_length} characters: {len(line)} chars")

    return content, violations


def remove_trailing_whitespace(content: str) -> Tuple[str, int]:
    """
    Remove trailing whitespace from all lines.

    Args:
        content: File content

    Returns:
        Tuple of (cleaned content, number of lines modified)
    """
    lines = content.split('\n')
    modified_count = 0
    new_lines = []

    for line in lines:
        stripped = line.rstrip()
        if stripped != line:
            modified_count += 1
        new_lines.append(stripped)

    return '\n'.join(new_lines), modified_count


def normalize_indentation(content: str, indent_size: int = 4) -> Tuple[str, int]:
    """
    Normalize indentation to use spaces instead of tabs.

    Args:
        content: File content
        indent_size: Number of spaces per indentation level (default: 4)

    Returns:
        Tuple of (normalized content, number of changes)
    """
    changes = 0
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        if '\t' in line:
            changes += 1
            # Replace tabs with spaces
            new_line = line.replace('\t', ' ' * indent_size)
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    return '\n'.join(new_lines), changes


def ensure_blank_lines_around_functions(content: str) -> Tuple[str, int]:
    """
    Ensure there are exactly two blank lines before function definitions.

    Args:
        content: File content

    Returns:
        Tuple of (normalized content, number of changes)
    """
    lines = content.split('\n')
    changes = 0
    new_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is a function definition
        if re.match(r'^\s*def\s+\w+\s*\(', line):
            # Count preceding blank lines
            blank_count = 0
            j = len(new_lines) - 1
            while j >= 0 and new_lines[j].strip() == '':
                blank_count += 1
                j -= 1

            # Adjust blank lines to exactly 2
            if blank_count < 2:
                # Add missing blank lines
                for _ in range(2 - blank_count):
                    new_lines.append('')
                changes += 1
            elif blank_count > 2:
                # Remove extra blank lines
                for _ in range(blank_count - 2):
                    if new_lines:
                        new_lines.pop()
                changes += 1

        new_lines.append(line)
        i += 1

    return '\n'.join(new_lines), changes


def format_file(file_path: str) -> FormattingReport:
    """
    Apply all formatting rules to a Python file.

    Args:
        file_path: Path to the file

    Returns:
        FormattingReport with details of changes
    """
    if not file_path.endswith('.py'):
        return FormattingReport(file_path, 0, ["Skipped: not a Python file"])

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return FormattingReport(file_path, 0, ["Error: File not found"])
    except UnicodeDecodeError as e:
        logger.error(f"Could not decode file {file_path}: {e}")
        return FormattingReport(file_path, 0, ["Error: Encoding issue"])

    details = []
    total_changes = 0

    # 1. Normalize line endings
    content, changes = normalize_line_endings(content)
    if changes > 0:
        details.append(f"Normalized line endings ({changes} changes)")
        total_changes += changes

    # 2. Remove trailing whitespace
    content, changes = remove_trailing_whitespace(content)
    if changes > 0:
        details.append(f"Removed trailing whitespace ({changes} lines)")
        total_changes += changes

    # 3. Normalize indentation
    content, changes = normalize_indentation(content)
    if changes > 0:
        details.append(f"Normalized indentation ({changes} lines)")
        total_changes += changes

    # 4. Ensure blank lines around functions
    content, changes = ensure_blank_lines_around_functions(content)
    if changes > 0:
        details.append(f"Adjusted blank lines around functions ({changes} changes)")
        total_changes += changes

    # Write back if changes were made
    if total_changes > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Formatted {file_path} ({total_changes} changes)")

    return FormattingReport(file_path, total_changes, details)


def format_directory(directory: str, exclude_patterns: Optional[List[str]] = None) -> List[FormattingReport]:
    """
    Recursively format all Python files in a directory.

    Args:
        directory: Path to the directory
        exclude_patterns: List of patterns to exclude

    Returns:
        List of FormattingReport objects
    """
    if exclude_patterns is None:
        exclude_patterns = ['__pycache__', 'venv', '.git', 'build', 'dist']

    reports = []
    path = Path(directory)

    if not path.exists():
        logger.error(f"Directory not found: {directory}")
        return reports

    for py_file in path.rglob('*.py'):
        # Check exclusions
        excluded = False
        for pattern in exclude_patterns:
            if pattern in str(py_file):
                excluded = True
                break

        if not excluded:
            report = format_file(str(py_file))
            reports.append(report)
            logger.debug(f"  -> {report}")

    return reports


def main():
    """Main entry point for the formatting script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Format Python code according to PEP 8 and project style"
    )
    parser.add_argument(
        '--directory',
        type=str,
        default='code',
        help='Directory to format (default: code)'
    )
    parser.add_argument(
        '--exclude',
        nargs='+',
        default=['__pycache__', 'venv', '.git'],
        help='Patterns to exclude'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info(f"Starting formatting of {args.directory}")
    logger.info(f"Excluding patterns: {', '.join(args.exclude)}")

    reports = format_directory(args.directory, args.exclude)

    # Summary
    total_files = len(reports)
    total_changes = sum(r.changes_made for r in reports)

    print("\n" + "=" * 60)
    print("FORMATTING SUMMARY")
    print("=" * 60)
    print(f"Files processed: {total_files}")
    print(f"Total changes made: {total_changes}")
    print("=" * 60)

    if total_changes > 0:
        print("\nFiles with changes:")
        for report in reports:
            if report.changes_made > 0:
                print(f"  - {report.file_path} ({report.changes_made} changes)")
    else:
        print("\nNo formatting changes needed. Code is already formatted!")

    return 0


if __name__ == '__main__':
    sys.exit(main())
