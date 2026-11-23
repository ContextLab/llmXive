"""
Verify that the boxplot artifact exists and calculate the correct relative path for the report.

This script ensures that `artifacts/boxplot.png` exists before the report generation proceeds.
If the file is missing, it raises a FileNotFoundError with a descriptive message.
"""

import os
import sys
from pathlib import Path

def verify_boxplot_exists() -> str:
    """
    Verify the existence of the boxplot artifact and return its relative path.

    Returns:
        str: The relative path to the boxplot image.

    Raises:
        FileNotFoundError: If the boxplot image is not found in the expected location.
    """
    # Define the project root relative to this script's location
    # Assuming this script is in code/, and artifacts/ is at the project root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent

    boxplot_path = project_root / "artifacts" / "boxplot.png"

    if not boxplot_path.exists():
        raise FileNotFoundError(
            f"Critical Artifact Missing: {boxplot_path} does not exist. "
            "Please ensure T033 (generate_boxplot) has been run successfully "
            "before proceeding with report generation."
        )

    # Return the relative path as expected by the report template
    # The template expects: artifacts/boxplot.png
    relative_path = "artifacts/boxplot.png"
    return relative_path

def main():
    """Main entry point for verification."""
    try:
        path = verify_boxplot_exists()
        print(f"SUCCESS: Boxplot verified at {path}")
        return 0
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
