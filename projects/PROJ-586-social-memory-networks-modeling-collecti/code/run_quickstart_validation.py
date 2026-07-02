"""
Runner script for quickstart validation.

This script executes the quickstart validation process as specified in T031.
It runs all commands from quickstart.md and verifies they exit with code 0.

Usage:
    python code/run_quickstart_validation.py
"""

import sys
import os
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from utils.quickstart_validator import main as validate_main


def main():
    """
    Main entry point for quickstart validation.

    Executes the validation against the project's quickstart.md file.
    """
    project_root = code_dir.parent
    quickstart_path = project_root / "quickstart.md"

    if not quickstart_path.exists():
        print(f"Error: quickstart.md not found at {quickstart_path}")
        sys.exit(1)

    # Change to project root for command execution
    os.chdir(project_root)

    # Run validation with appropriate arguments
    sys.argv = [
        'run_quickstart_validation.py',
        '--quickstart', str(quickstart_path),
        '--project-dir', str(project_root),
        '--output', str(project_root / "results" / "quickstart_validation_report.txt")
    ]

    try:
        validate_main()
    except SystemExit as e:
        sys.exit(e.code)


if __name__ == '__main__':
    main()