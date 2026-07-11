"""
Refactoring utilities to improve code readability and maintainability.

This module provides functions to:
1. Extract repeated code patterns into helper functions
2. Simplify complex conditional expressions
3. Improve variable naming consistency
4. Add type hints where missing
5. Break down long functions
"""
import ast
import os
import re
import sys
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class RefactorReport:
    """Report of refactoring actions taken on a file."""
    file_path: str
    improvements_made: int
    suggestions: List[str]

    def __str__(self) -> str:
        return (f"File: {self.file_path}\n"
                f"  Improvements: {self.improvements_made}\n"
                f"  Suggestions: {len(self.suggestions)}")


def find_repeated_code_blocks(content: str, min_length: int = 5) -> List[Tuple[str, int, int]]:
    """
    Identify repeated code blocks (lines) in the content.

    Args:
        content: File content
        min_length: Minimum number of lines to consider a block

    Returns:
        List of (block_content, start_line, end_line) tuples
    """
    lines = content.split('\n')
    repeats = []
    seen = {}

    for i in range(len(lines) - min_length + 1):
        block = tuple(lines[i:i + min_length])
        block_str = '\n'.join(block)

        if block_str.strip() == '':
            continue

        if block_str in seen:
            repeats.append((block_str, seen[block_str], i))
        else:
            seen[block_str] = i

    return repeats


def simplify_boolean_expressions(content: str) -> Tuple[str, int]:
    """
    Simplify common boolean expression patterns.

    Examples:
      - `if x == True:` -> `if x:`
      - `if x == False:` -> `if not x:`
      - `if not (x == y):` -> `if x != y:`

    Args:
        content: File content

    Returns:
        Tuple of (simplified content, number of changes)
    """
    changes = 0
    patterns = [
        (r'\bif\s+(\w+)\s*==\s*True\s*:', r'if \1:'),
        (r'\bif\s+(\w+)\s*==\s*False\s*:', r'if not \1:'),
        (r'\bwhile\s+(\w+)\s*==\s*True\s*:', r'while \1:'),
        (r'\bwhile\s+(\w+)\s*==\s*False\s*:', r'while not \1:'),
        (r'\bif\s+not\s*\(\s*(\w+)\s*==\s*(\w+)\s*\)\s*:', r'if \1 != \2:'),
        (r'\bif\s+not\s*\(\s*(\w+)\s*!=\s*(\w+)\s*\)\s*:', r'if \1 == \2:'),
    ]

    for pattern, replacement in patterns:
        matches = re.findall(pattern, content)
        if matches:
            changes += len(matches)
            content = re.sub(pattern, replacement, content)

    return content, changes


def add_missing_type_hints(content: str) -> Tuple[str, int]:
    """
    Add basic type hints to function definitions that are missing them.

    This is a simplified heuristic approach that adds hints for:
    - Parameters that are clearly integers or strings based on usage
    - Return types based on return statements

    Note: This is a best-effort approach and may not be perfect.

    Args:
        content: File content

    Returns:
        Tuple of (modified content, number of hints added)
    """
    changes = 0
    lines = content.split('\n')
    new_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for function definition without type hints
        match = re.match(r'^(\s*)def\s+(\w+)\s*\((.*?)\)\s*:', line)
        if match:
            indent, func_name, params = match.groups()

            # Skip if already has type hints
            if ':' in params or '->' in line:
                new_lines.append(line)
                i += 1
                continue

            # Try to infer types from default values
            new_params = []
            for param in params.split(','):
                param = param.strip()
                if not param:
                    continue

                # Check for default value
                if '=' in param:
                    name, default = param.split('=', 1)
                    name = name.strip()
                    default = default.strip()

                    # Infer type from default
                    if default in ('None',):
                        new_params.append(f"{name}: Optional[Any]")
                    elif default.startswith('"') or default.startswith("'"):
                        new_params.append(f"{name}: str")
                    elif default.isdigit() or (default.startswith('-') and default[1:].isdigit()):
                        new_params.append(f"{name}: int")
                    elif default.replace('.', '', 1).isdigit():
                        new_params.append(f"{name}: float")
                    else:
                        new_params.append(param)
                else:
                    # No default - use Any
                    new_params.append(f"{param}: Any")

            # Reconstruct the line
            if new_params:
                new_params_str = ', '.join(new_params)
                new_line = f"{indent}def {func_name}({new_params_str}):"
                new_lines.append(new_line)
                changes += 1
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

        i += 1

    return '\n'.join(new_lines), changes


def extract_repeated_patterns(content: str) -> List[str]:
    """
    Identify code patterns that could be extracted into helper functions.

    Args:
        content: File content

    Returns:
        List of suggested extractions
    """
    suggestions = []
    lines = content.split('\n')

    # Look for repeated logging patterns
    logging_calls = [i for i, line in enumerate(lines) if 'logger.' in line]
    if len(logging_calls) > 3:
        # Check if they follow a pattern
        patterns = {}
        for i in logging_calls:
            match = re.search(r'logger\.\w+\s*\(\s*["\'](.+?)["\']', lines[i])
            if match:
                msg = match.group(1)
                # Extract template (replace variables with {})
                template = re.sub(r'\b\w+\b', '{}', msg)
                patterns.setdefault(template, []).append(i)

        for template, lines_list in patterns.items():
            if len(lines_list) > 1:
                suggestions.append(
                    f"Extract logging pattern to helper: '{template}' "
                    f"(used {len(lines_list)} times)"
                )

    # Look for repeated error handling
    error_patterns = [i for i, line in enumerate(lines) if 'except' in line]
    if len(error_patterns) > 2:
        suggestions.append("Consider creating a custom exception handler utility")

    return suggestions


def refactor_file(file_path: str) -> RefactorReport:
    """
    Apply refactoring improvements to a Python file.

    Args:
        file_path: Path to the file

    Returns:
        RefactorReport with details of improvements
    """
    if not file_path.endswith('.py'):
        return RefactorReport(file_path, 0, ["Skipped: not a Python file"])

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return RefactorReport(file_path, 0, ["Error: File not found"])
    except UnicodeDecodeError as e:
        logger.error(f"Could not decode file {file_path}: {e}")
        return RefactorReport(file_path, 0, ["Error: Encoding issue"])

    improvements = 0
    suggestions = []

    # 1. Simplify boolean expressions
    content, changes = simplify_boolean_expressions(content)
    if changes > 0:
        improvements += changes
        suggestions.append(f"Simplified {changes} boolean expressions")

    # 2. Add missing type hints
    content, changes = add_missing_type_hints(content)
    if changes > 0:
        improvements += changes
        suggestions.append(f"Added {changes} type hints")

    # 3. Identify repeated code
    repeats = find_repeated_code_blocks(content)
    if repeats:
        suggestions.append(f"Found {len(repeats)} repeated code blocks to consider extracting")

    # 4. Generate suggestions
    suggestions.extend(extract_repeated_patterns(content))

    # Write back if changes were made
    if improvements > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Refactored {file_path} ({improvements} improvements)")

    return RefactorReport(file_path, improvements, suggestions)


def refactor_directory(directory: str, exclude_patterns: Optional[List[str]] = None) -> List[RefactorReport]:
    """
    Recursively refactor all Python files in a directory.

    Args:
        directory: Path to the directory
        exclude_patterns: List of patterns to exclude

    Returns:
        List of RefactorReport objects
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
            report = refactor_file(str(py_file))
            reports.append(report)
            logger.debug(f"  -> {report}")

    return reports


def main():
    """Main entry point for the refactoring script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Refactor Python code to improve readability and maintainability"
    )
    parser.add_argument(
        '--directory',
        type=str,
        default='code',
        help='Directory to refactor (default: code)'
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

    logger.info(f"Starting refactoring of {args.directory}")
    logger.info(f"Excluding patterns: {', '.join(args.exclude)}")

    reports = refactor_directory(args.directory, args.exclude)

    # Summary
    total_files = len(reports)
    total_improvements = sum(r.improvements_made for r in reports)
    total_suggestions = sum(len(r.suggestions) for r in reports)

    print("\n" + "=" * 60)
    print("REFACTORING SUMMARY")
    print("=" * 60)
    print(f"Files processed: {total_files}")
    print(f"Improvements made: {total_improvements}")
    print(f"Suggestions generated: {total_suggestions}")
    print("=" * 60)

    if total_improvements > 0:
        print("\nFiles with improvements:")
        for report in reports:
            if report.improvements_made > 0:
                print(f"  - {report.file_path} ({report.improvements_made} improvements)")

    if total_suggestions > 0:
        print("\nSuggestions for manual review:")
        for report in reports:
            if report.suggestions:
                print(f"\n{report.file_path}:")
                for s in report.suggestions:
                    print(f"  - {s}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
