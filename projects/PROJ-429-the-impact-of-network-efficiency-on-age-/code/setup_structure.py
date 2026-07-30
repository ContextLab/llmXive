import os
import json
from pathlib import Path
from datetime import datetime
from config import ensure_dirs

def create_directories():
    """
    Create the project directory structure as per plan.md.
    Returns a list of created directory paths.
    """
    base_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/processed/connectivity_matrices",
        "data/quality",
        "data/results",
        "data/config",
        "state",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/benchmark",
        "docs",
        "docs/decisions",
        "specs",
        "contracts"
    ]

    created = []
    for d in base_dirs:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
        created.append(str(path))
    
    return created

def create_manifest(created_dirs):
    """
    Create a manifest file recording the directory structure and creation timestamp.
    This serves as the evidence required for T001 verification.
    """
    manifest_path = Path("state") / "project_structure_manifest.json"
    
    manifest = {
        "created_at": datetime.utcnow().isoformat(),
        "root": str(Path(".").resolve()),
        "directories": sorted(created_dirs),
        "description": "Project structure created per plan.md for PROJ-429"
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    return manifest_path

def main():
    """
    Entry point to create the project structure.
    """
    print("Initializing project structure for PROJ-429...")
    
    # Ensure base config directories exist first
    ensure_dirs()
    
    # Create the rest of the structure
    created = create_directories()
    manifest_path = create_manifest(created)
    
    print(f"Created {len(created)} directories.")
    print(f"Manifest written to: {manifest_path}")
    
    # Verify existence
    missing = [d for d in created if not Path(d).exists()]
    if missing:
        print(f"ERROR: Failed to create: {missing}")
        return 1
    
    print("Project structure verification: PASSED")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
