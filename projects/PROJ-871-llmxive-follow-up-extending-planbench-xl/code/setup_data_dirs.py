"""
Setup script to create the required data directory structure for the project.
Creates: data/, data/raw, data/derived, data/logs, data/results
"""
import os
import sys
from pathlib import Path

def main():
    """Create the data directory structure."""
    # Determine project root (assumed to be the parent of the 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    data_root = project_root / "data"
    subdirs = ["raw", "derived", "logs", "results"]

    created = []
    for subdir in subdirs:
        target_path = data_root / subdir
        target_path.mkdir(parents=True, exist_ok=True)
        created.append(str(target_path.relative_to(project_root)))
    
    # Ensure root data dir exists explicitly if subdirs loop didn't create it (edge case)
    data_root.mkdir(parents=True, exist_ok=True)
    if str(data_root.relative_to(project_root)) not in created:
        created.insert(0, str(data_root.relative_to(project_root)))

    print(f"Data directories created successfully:")
    for path in sorted(created):
        print(f"  - {path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
