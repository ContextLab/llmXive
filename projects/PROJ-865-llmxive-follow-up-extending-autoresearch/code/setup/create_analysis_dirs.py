"""
Task T001j: Create directory `code/04_analysis/` at repository root.

This script ensures the existence of the analysis directory required for
User Story 3 (Statistical Analysis & Error Taxonomy).
"""
import os
import sys
from pathlib import Path


def main():
    """Create the code/04_analysis/ directory if it does not exist."""
    # Determine project root (assuming script is in code/setup/)
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    
    target_dir = project_root / "code" / "04_analysis"
    
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {target_dir}")
    else:
        print(f"Directory already exists: {target_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())