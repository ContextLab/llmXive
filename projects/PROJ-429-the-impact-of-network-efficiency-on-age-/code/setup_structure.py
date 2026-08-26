import os
import json
from pathlib import Path
from datetime import datetime
from config import ensure_dirs

def create_directories():
    """
    Creates the standard project directory structure as defined in plan.md.
    Directories: code/, data/, state/, tests/, docs/
    Also creates subdirectories for data organization.
    """
    base_dirs = [
        "code",
        "data",
        "state",
        "tests",
        "docs"
    ]

    sub_dirs = [
        "data/raw",
        "data/processed",
        "data/processed/connectivity_matrices",
        "data/quality",
        "data/results",
        "data/config",
        "code/data",
        "code/network",
        "code/stats",
        "code/viz",
        "code/tools",
        "tests/unit",
        "tests/integration",
        "tests/benchmark",
        "docs/decisions",
        "specs"
    ]

    all_dirs = base_dirs + sub_dirs

    created = []
    for d in all_dirs:
        path = Path(d)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
        else:
            # Ensure they are actually directories
            if not path.is_dir():
                raise FileExistsError(f"Path {path} exists but is not a directory")
    
    return created

def create_manifest(created_dirs):
    """
    Creates a manifest file documenting the project structure.
    This serves as evidence for T001 that the structure exists.
    """
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "task_id": "T001",
        "description": "Project structure creation per plan.md",
        "directories_created": created_dirs,
        "total_count": len(created_dirs),
        "status": "success"
    }

    manifest_path = Path("data/quality/structure_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest_path

def main():
    """
    Main entry point for T001 execution.
    1. Ensures config paths are ready (via config.py)
    2. Creates all required directories
    3. Generates a manifest file as proof of creation
    """
    print("Starting T001: Creating project structure...")
    
    # Ensure base config directories exist first
    ensure_dirs()
    
    # Create the rest of the structure
    created = create_directories()
    print(f"Created {len(created)} directories.")
    
    # Generate manifest
    manifest_path = create_manifest(created)
    print(f"Manifest written to: {manifest_path}")
    
    # List contents for verification
    print("\nProject Structure Snapshot:")
    for root, dirs, files in os.walk("."):
        # Skip hidden and git directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if not file.startswith('.'):
                print(f'{subindent}{file}')
    
    print("\nT001 completed successfully.")
    return 0

if __name__ == "__main__":
    main()
