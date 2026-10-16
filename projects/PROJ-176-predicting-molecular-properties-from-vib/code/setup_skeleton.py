"""
setup_skeleton.py

This script creates the canonical project directory tree required for the
"Predicting Molecular Properties from Vibrational Spectra" feature, adds empty
`__init__.py` files so that the directories are recognised as Python packages,
and writes a sorted list of all directories to `results/structure_report.txt`.
"""

import sys
from pathlib import Path
from llmxive_toolkit import paths

def main() -> int:
    # 1. Define the directory structure as specified in T101
    # We include the contracts folder as it is required by T102
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

    # 2. Create directories and __init__.py files
    for d in DIRS:
        p = Path(d)
        p.mkdir(parents=True, exist_ok=True)
        
        # Create an empty __init__.py for Python packages
        # These are typically under code/ or tests/
        if "code" in p.parts or "tests" in p.parts:
            (p / "__init__.py").touch(exist_ok=True)

    # 3. Generate the structure report
    # Use the toolkit to get the correct results path
    report_path = paths.results("structure_report.txt")
    
    # Find all directories relative to the project root
    # We use Path(".").rglob("*") to mimic 'find . -type d'
    all_dirs = []
    for p in Path(".").rglob("*"):
        if p.is_dir():
            try:
                # Store as string relative to current working directory
                all_dirs.append(str(p.relative_to(Path.cwd())))
            except ValueError:
                continue
    
    all_dirs.sort()

    # Write the sorted list to the report file
    with report_path.open("w", encoding="utf-8") as f:
        for line in all_dirs:
            f.write(line + "\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())