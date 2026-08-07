import os
import sys
from pathlib import Path

def create_results_directory():
    """
    Creates the 'results' directory under the project root.
    Ensures the directory exists for storing analysis outputs, reports, and figures.
    """
    # Determine project root based on the script's location relative to code/
    # Assuming this script is run from the project root or code/ directory
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent if current_dir.name == "code" else current_dir

    results_dir = project_root / "results"
    
    try:
        results_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully ensured directory exists: {results_dir}")
        return True
    except OSError as e:
        print(f"Error creating directory {results_dir}: {e}", file=sys.stderr)
        return False

def main():
    """Entry point for the script."""
    success = create_results_directory()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()