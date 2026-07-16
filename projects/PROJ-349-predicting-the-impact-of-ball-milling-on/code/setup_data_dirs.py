"""
Setup script to create the required data directory structure.
Creates: data/raw, data/processed, data/splits, results
"""
import os
import sys
from pathlib import Path

def setup_directories(base_dir: str = None) -> dict:
    """
    Create the required directory structure for the project.

    Args:
        base_dir: Base directory for data storage. Defaults to 'data' in project root.

    Returns:
        Dictionary mapping directory names to their absolute paths.
    """
    if base_dir is None:
        # Default to 'data' directory in the same location as this script
        base_path = Path(__file__).parent.parent / "data"
    else:
        base_path = Path(base_dir)

    # Define subdirectories
    directories = {
        "raw": base_path / "raw",
        "processed": base_path / "processed",
        "splits": base_path / "splits",
        "flagged": base_path / "flagged",  # For flagged PSD entries
    }

    results_dir = base_path.parent / "results"

    # Create directories
    created = {}
    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)
        created[name] = str(path.resolve())
        print(f"Created directory: {path}")

    # Create results directory
    results_dir.mkdir(parents=True, exist_ok=True)
    created["results"] = str(results_dir.resolve())
    print(f"Created directory: {results_dir}")

    # Create a .gitkeep file in each directory to ensure they are tracked by git
    for path in directories.values():
        gitkeep = path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in: {path}")

    print(f"\nDirectory structure ready. Base path: {base_path}")
    return created

if __name__ == "__main__":
    # Allow command-line argument for base directory
    base_dir = sys.argv[1] if len(sys.argv) > 1 else None
    setup_directories(base_dir)