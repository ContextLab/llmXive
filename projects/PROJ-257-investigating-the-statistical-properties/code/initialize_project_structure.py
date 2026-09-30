"""
T001: Initialize Project Directory Structure and generate manifest.

Creates the required directory tree and outputs a JSON manifest
describing the hierarchy.
"""
import json
import os
from pathlib import Path

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "src",
    "tests",
    "data/raw",
    "data/processed",
    "output/results",
    "output/figures",
    "logs",
    "src/data",
    "src/analysis",
    "src/viz",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]

def create_directories(base_path: Path) -> list[str]:
    """Create all required directories and return list of created paths."""
    created = []
    for dir_path in REQUIRED_DIRS:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created.append(str(full_path))
    return created

def generate_manifest(base_path: Path) -> dict:
    """
    Generate a JSON-compatible dictionary representing the directory structure.
    Keys are directory names, values are lists of their immediate subdirectories.
    """
    manifest = {}
    
    # Helper to get immediate subdirectories of a path
    def get_subdirs(path: Path) -> list[str]:
        if not path.exists():
            return []
        return [d.name for d in path.iterdir() if d.is_dir()]

    # Build the manifest by scanning the created structure
    # We organize by the top-level directories first
    top_level_dirs = ["src", "tests", "data", "output", "logs"]
    
    for top_dir in top_level_dirs:
        top_path = base_path / top_dir
        if top_path.exists():
            subdirs = get_subdirs(top_path)
            manifest[top_dir] = subdirs

    # Ensure 'logs' is included even if empty
    if "logs" not in manifest:
        manifest["logs"] = []

    return manifest

def main():
    project_root = Path(__file__).parent.parent
    print(f"Initializing project structure at: {project_root}")
    
    # Create directories
    created_paths = create_directories(project_root)
    print(f"Created {len(created_paths)} directories.")
    
    # Generate manifest
    manifest = generate_manifest(project_root)
    manifest_path = project_root / "project_structure_manifest.json"
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest written to: {manifest_path}")
    print("Directory structure initialization complete.")

if __name__ == "__main__":
    main()
