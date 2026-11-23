"""
Causal language linting utilities for llmXive project.

This module provides tools to detect and flag causal language in generated reports
to ensure compliance with scientific rigor and spec assumptions.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from utils.logger import get_logger

# Define causal terms that should be flagged
# These terms imply causality where only correlation or association can be established
CAUSAL_TERMS = {
    "causes", "caused", "cause", "causing",
    "proves", "proved", "prove", "proven",
    "determines", "determined", "determine", "determining",
    "proves that", "demonstrates that", "shows that",
    "leads to", "result in", "results in", "resulted in",
    "is responsible for", "responsible for",
    "creates", "created", "create",
    "induces", "induced", "induce",
    "forces", "forced", "force",
    "compels", "compelled", "compel",
    "necessitates", "necessitated", "necessitate",
    "guarantees", "guaranteed", "guarantee",
    "ensures", "ensured", "ensure",
    "makes", "made", "make",
    "triggers", "triggered", "trigger",
    "initiates", "initiated", "initiate",
    "precipitates", "precipitated", "precipitate",
    "effects", "effected", "effect",  # As verb: to effect change
    "brings about", "brought about",
    "gives rise to", "gave rise to",
    "is the cause of", "are the cause of",
    "is the reason for", "are the reason for",
    "solely due to", "entirely due to",
    "directly causes", "directly leads to",
    "proves conclusively", "demonstrates conclusively",
}

# Case-insensitive pattern for matching causal terms
CAUSAL_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(term) for term in CAUSAL_TERMS) + r')\b',
    re.IGNORECASE
)

def get_logger_for_linting() -> logging.Logger:
    """Get a logger instance for the linter module."""
    return get_logger(__name__)

def check_text_for_causal_claims(
    text: str,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Check text for causal language claims.

    Args:
        text: The text content to analyze.
        logger: Optional logger instance. If None, a default logger is used.

    Returns:
        A dictionary containing:
            - 'has_causal_claims': bool indicating if causal terms were found
            - 'matches': List of dictionaries with 'term', 'position', 'context'
            - 'count': Total number of causal terms found
    """
    if logger is None:
        logger = get_logger_for_linting()

    result = {
        'has_causal_claims': False,
        'matches': [],
        'count': 0
    }

    if not text or not isinstance(text, str):
        logger.warning("Empty or invalid text provided for causal check.")
        return result

    matches = list(CAUSAL_PATTERN.finditer(text))

    if matches:
        result['has_causal_claims'] = True
        result['count'] = len(matches)

        for match in matches:
            term = match.group(0)
            start_pos = match.start()
            end_pos = match.end()

            # Extract context (100 characters before and after)
            context_start = max(0, start_pos - 50)
            context_end = min(len(text), end_pos + 50)
            context = text[context_start:context_end]

            # Add ellipsis if truncated
            if context_start > 0:
                context = "..." + context
            if context_end < len(text):
                context = context + "..."

            result['matches'].append({
                'term': term,
                'position': start_pos,
                'context': context
            })

            logger.warning(f"Causal term detected: '{term}' at position {start_pos}")
            logger.warning(f"Context: {context}")

    return result

def lint_report_file(
    file_path: Path,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Lint a report file for causal language claims.

    Args:
        file_path: Path to the file to lint.
        logger: Optional logger instance.

    Returns:
        A dictionary with linting results including pass/fail status.
    """
    if logger is None:
        logger = get_logger_for_linting()

    result = {
        'file_path': str(file_path),
        'passed': True,
        'has_causal_claims': False,
        'matches': [],
        'count': 0,
        'error_message': None
    }

    if not file_path.exists():
        result['passed'] = False
        result['error_message'] = f"File not found: {file_path}"
        logger.error(result['error_message'])
        return result

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        check_result = check_text_for_causal_claims(content, logger)

        result['has_causal_claims'] = check_result['has_causal_claims']
        result['matches'] = check_result['matches']
        result['count'] = check_result['count']

        if check_result['has_causal_claims']:
            result['passed'] = False
            result['error_message'] = (
                f"Causal language detected in {file_path}: "
                f"{check_result['count']} instance(s) found."
            )
            logger.error(result['error_message'])

    except Exception as e:
        result['passed'] = False
        result['error_message'] = f"Error reading file: {str(e)}"
        logger.error(result['error_message'])

    return result

def lint_multiple_files(
    file_paths: List[Path],
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Lint multiple report files for causal language claims.

    Args:
        file_paths: List of file paths to lint.
        logger: Optional logger instance.

    Returns:
        A dictionary with aggregate linting results.
    """
    if logger is None:
        logger = get_logger_for_linting()

    results = {
        'total_files': len(file_paths),
        'passed': 0,
        'failed': 0,
        'total_causal_claims': 0,
        'file_results': []
    }

    for file_path in file_paths:
        file_result = lint_report_file(file_path, logger)
        results['file_results'].append(file_result)

        if file_result['passed']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['total_causal_claims'] += file_result['count']

    results['overall_passed'] = results['failed'] == 0

    if not results['overall_passed']:
        logger.error(
            f"Linting failed: {results['failed']} file(s) contain causal language."
        )
    else:
        logger.info("All files passed causal language linting.")

    return results

def fail_build_on_causal_claims(
    file_paths: List[Path],
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Check files and raise an exception if causal language is detected.

    This function is designed to be used in CI/CD pipelines to fail the build
    if causal claims are found in output reports.

    Args:
        file_paths: List of file paths to check.
        logger: Optional logger instance.

    Raises:
        ValueError: If causal language is detected in any file.
    """
    if logger is None:
        logger = get_logger_for_linting()

    results = lint_multiple_files(file_paths, logger)

    if not results['overall_passed']:
        error_msg = (
            "BUILD FAILED: Causal language detected in output reports.\n"
            f"Files checked: {results['total_files']}\n"
            f"Failed files: {results['failed']}\n"
            f"Total causal claims: {results['total_causal_claims']}\n\n"
            "Please review the following files and replace causal language "
            "with appropriate correlational or descriptive language:\n"
        )

        for file_result in results['file_results']:
            if not file_result['passed']:
                error_msg += f"\n- {file_result['file_path']}:\n"
                for match in file_result['matches']:
                    error_msg += f"  Found: '{match['term']}' in context: {match['context']}\n"

        raise ValueError(error_msg)

def main() -> None:
    """
    Main entry point for causal language linting.

    This function can be called from command line or CI/CD pipelines
    to lint report files for causal language claims.
    """
    import sys

    logger = get_logger_for_linting()
    logger.info("Starting causal language linting...")

    # Default files to check (can be overridden via command line args)
    files_to_check = [
        Path("data/processed/sensitivity_report.csv"),
        Path("data/processed/robustness_curve.png"),  # Will be skipped (binary)
        Path("data/processed/breaking_point.json"),
    ]

    # Filter to existing text files
    text_files = []
    for f in files_to_check:
        if f.exists():
            # Skip binary files
            try:
                with open(f, 'r', encoding='utf-8') as _:
                    text_files.append(f)
            except (UnicodeDecodeError, IOError):
                logger.warning(f"Skipping binary or unreadable file: {f}")

    if not text_files:
        logger.warning("No text files found to lint.")
        sys.exit(0)

    try:
        fail_build_on_causal_claims(text_files, logger)
        logger.info("All files passed causal language linting.")
        sys.exit(0)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
