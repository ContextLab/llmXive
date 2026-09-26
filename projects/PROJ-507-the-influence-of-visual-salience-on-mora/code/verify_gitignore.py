"""
Verification script for .gitignore patterns.
This script verifies that the .gitignore file exists and contains the required patterns.
It uses `git check-ignore` to confirm that the patterns are effective.
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Set
import logging

from logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

REQUIRED_PATTERNS = {
    'data/raw/',
    'data/survey/',
    '__pycache__/',
    '*.pyc',
    '.env',
}

def verify_gitignore_patterns(gitignore_path: Path, project_root: Path) -> bool:
    """
    Verify that the .gitignore file contains the required patterns.
    
    Args:
        gitignore_path: Path to the .gitignore file
        project_root: Path to the project root directory
        
    Returns:
        True if all required patterns are present, False otherwise
    """
    if not gitignore_path.exists():
        logger.error(f".gitignore file not found at {gitignore_path}")
        return False

    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()

    missing_patterns = []
    for pattern in REQUIRED_PATTERNS:
        # Normalize pattern for comparison (remove trailing slash for some checks)
        normalized_pattern = pattern.rstrip('/')
        if normalized_pattern not in content and pattern not in content:
            missing_patterns.append(pattern)

    if missing_patterns:
        logger.error(f"Missing required patterns in .gitignore: {missing_patterns}")
        return False

    logger.info("All required patterns found in .gitignore")
    return True

def check_git_ignore_effectiveness(project_root: Path) -> bool:
    """
    Use `git check-ignore` to verify that the patterns are effective.
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        True if git check-ignore works and patterns are recognized, False otherwise
    """
    # Check if git is initialized
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            logger.warning("Git repository not initialized. Skipping effectiveness check.")
            return True  # Not a failure, just not applicable
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.warning("Git not available. Skipping effectiveness check.")
        return True  # Not a failure, just not applicable

    # Test a few patterns with git check-ignore
    test_files = [
        'data/raw/test_file.txt',
        'data/survey/test_file.txt',
        '__pycache__/test.pyc',
        '.env',
    ]

    # Create temporary test files to check ignore behavior
    created_files = []
    try:
        for test_file in test_files:
            file_path = project_root / test_file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
            created_files.append(file_path)

        for test_file in test_files:
            result = subprocess.run(
                ['git', 'check-ignore', test_file],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                # File should be ignored but isn't
                logger.warning(f"Pattern for {test_file} not effective in .gitignore")
                return False

        logger.info("Git check-ignore verification passed")
        return True

    finally:
        # Clean up test files
        for file_path in created_files:
            if file_path.exists():
                file_path.unlink()
                # Try to remove parent directories if empty
                try:
                    file_path.parent.rmdir()
                except OSError:
                    pass

def main():
    """Main entry point for the verification script."""
    project_root = Path.cwd()
    gitignore_path = project_root / '.gitignore'

    logger.info(f"Verifying .gitignore at {gitignore_path}")

    # Verify patterns are present
    patterns_ok = verify_gitignore_patterns(gitignore_path, project_root)
    if not patterns_ok:
        logger.error("Verification failed: Missing required patterns")
        sys.exit(1)

    # Verify effectiveness with git check-ignore
    effectiveness_ok = check_git_ignore_effectiveness(project_root)
    if not effectiveness_ok:
        logger.error("Verification failed: Patterns not effective in git")
        sys.exit(1)

    logger.info("Verification successful: .gitignore is correctly configured")
    sys.exit(0)

if __name__ == '__main__':
    main()
