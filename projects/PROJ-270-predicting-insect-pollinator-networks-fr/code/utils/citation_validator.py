"""
Citation Validator Wrapper for Reference-Validator Agent.

This module provides a programmatic interface to the Reference-Validator Agent
pre-commit hook, allowing for automated citation verification within the
llmXive research pipeline.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Union


class CitationValidationError(Exception):
    """Raised when citation validation fails."""
    pass


def validate_citations(
    file_path: Union[str, Path],
    validator_path: Optional[Union[str, Path]] = None,
    strict_mode: bool = True
) -> bool:
    """
    Validates citations in a given file using the Reference-Validator Agent.

    Args:
        file_path: Path to the file containing citations to validate.
        validator_path: Optional path to the Reference-Validator executable.
                       If None, expects 'reference-validator' in PATH.
        strict_mode: If True, raises an error on any validation failure.
                    If False, returns False but does not raise.

    Returns:
        True if validation passes, False otherwise.

    Raises:
        CitationValidationError: If validation fails in strict mode.
        FileNotFoundError: If the validator executable is not found.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Determine validator command
    if validator_path:
        cmd = [str(validator_path), str(file_path)]
    else:
        # Default to 'reference-validator' in PATH
        cmd = ["reference-validator", str(file_path)]

    try:
        # Run the validator
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False  # Don't raise on non-zero exit
        )

        if result.returncode == 0:
            return True
        
        # Validation failed
        error_msg = (
            f"Citation validation failed for {file_path}:\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        if strict_mode:
            raise CitationValidationError(error_msg)
        
        return False

    except FileNotFoundError:
        raise FileNotFoundError(
            "Reference-Validator Agent not found. "
            "Please install it or provide the path via validator_path argument. "
            "Installation: pip install reference-validator"
        )


def validate_directory(
    directory_path: Union[str, Path],
    extensions: Optional[List[str]] = None,
    validator_path: Optional[Union[str, Path]] = None,
    strict_mode: bool = True
) -> bool:
    """
    Validates citations in all supported files within a directory.

    Args:
        directory_path: Path to the directory to scan.
        extensions: List of file extensions to validate (e.g., ['.md', '.txt']).
                   If None, defaults to ['.md', '.txt', '.rst'].
        validator_path: Optional path to the Reference-Validator executable.
        strict_mode: If True, raises an error on the first validation failure.

    Returns:
        True if all files pass validation, False otherwise.

    Raises:
        CitationValidationError: If any file fails validation in strict mode.
        NotADirectoryError: If the provided path is not a directory.
    """
    directory_path = Path(directory_path)
    
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory_path}")

    if extensions is None:
        extensions = ['.md', '.txt', '.rst']

    all_valid = True
    failed_files = []

    # Collect files to validate
    files_to_check = []
    for ext in extensions:
        files_to_check.extend(directory_path.rglob(f"*{ext}"))

    if not files_to_check:
        return True  # No files to validate

    for file_path in files_to_check:
        try:
            if not validate_citations(
                file_path, 
                validator_path=validator_path, 
                strict_mode=False
            ):
                all_valid = False
                failed_files.append(file_path)
        except Exception as e:
            all_valid = False
            failed_files.append((file_path, str(e)))

    if all_valid:
        return True

    error_details = "\n".join([str(f) for f in failed_files])
    error_msg = (
        f"Citation validation failed for {len(failed_files)} file(s) in {directory_path}:\n"
        f"{error_details}"
    )

    if strict_mode:
        raise CitationValidationError(error_msg)

    return False


def run_pre_commit_hook(
    staged_files: Optional[List[Path]] = None,
    validator_path: Optional[Union[str, Path]] = None
) -> int:
    """
    Simulates the pre-commit hook behavior by validating staged files.

    This function is designed to be called by pre-commit hooks.

    Args:
        staged_files: List of staged file paths. If None, attempts to detect
                     staged files via git.
        validator_path: Optional path to the Reference-Validator executable.

    Returns:
        0 if all validations pass, 1 otherwise.
    """
    if staged_files is None:
        # Attempt to get staged files via git
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )
            staged_files = [Path(f) for f in result.stdout.strip().split('\n') if f]
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Git not available or no staged files
            return 0

    if not staged_files:
        return 0

    failed_count = 0
    for file_path in staged_files:
        if not file_path.exists():
            continue  # Skip deleted files
        
        # Only validate supported file types
        if file_path.suffix.lower() in ['.md', '.txt', '.rst']:
            try:
                if not validate_citations(
                    file_path, 
                    validator_path=validator_path, 
                    strict_mode=False
                ):
                    print(f"Citation validation failed: {file_path}", file=sys.stderr)
                    failed_count += 1
            except Exception as e:
                print(f"Error validating {file_path}: {e}", file=sys.stderr)
                failed_count += 1

    return 1 if failed_count > 0 else 0
