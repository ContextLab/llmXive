"""
setup_skeleton.py

This script creates the canonical project directory tree required for the
"Predicting Molecular Properties from Vibrational Spectra" project, adds empty
`__init__.py` files to ensure directories are treated as Python packages,
and performs the required verification steps:
1. Compiles the code directory to ensure syntactical correctness.
2. Generates a sorted report of all directories in the project root.
"""

import os
import subprocess
import sys
from pathlib import Path

def main() -> int:
    # 1. Define the canonical directory tree as specified in T101
    DIRS = [
        "code",
        "code/data",
        "code/models",
        "code/evaluation",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/external",
        "results",
        "logs",
        "specs/001-predict-molecular-properties",
        "specs/001-predict-molecular-properties/contracts",
    ]

    # Create directories
    for d in DIRS:
        p = Path(d)
        p.mkdir(parents=True, exist_ok=True)

    # 2. Create empty __init__.py files for Python packages
    INIT_FILES = [
        "code/__init__.py",
        "code/data/__init__.py",
        "code/models/__init__.py",
        "code/evaluation/__init__.py",
        "code/utils/__init__.py",
        "tests/__init__.py",
    ]
    for f in INIT_FILES:
        Path(f).touch(exist_ok=True)

    # 3. Verification: Run compileall on the code directory
    # This ensures that the created skeleton (and any existing code) is syntactically valid.
    try:
        subprocess.run(
            [sys.executable, "-m", "compileall", "code/"],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e.stderr}")
        return 1

    # 4. Verification: Generate the structure report
    # We use the shell command 'find . -type d | sort' as explicitly required by the task verification.
    # This ensures the output format exactly matches the expectation.
    try:
        # Ensure the results directory exists before redirecting
        Path("results").mkdir(parents=True, exist_ok=True)
        
        # Use shell=True to allow the pipe and redirection
        subprocess.run(
            "find . -type d | sort > results/structure_report.txt",
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Structure report generation failed: {e.stderr}")
        return 1

    print("Project skeleton created and verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())