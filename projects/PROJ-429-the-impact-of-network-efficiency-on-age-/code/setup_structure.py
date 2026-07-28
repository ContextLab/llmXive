"""
T001: Create project structure per plan.md.

This script creates the required directory tree:
code/, data/, state/, tests/, docs/

It also creates a manifest file to serve as evidence of completion.
"""
import os
import json
from pathlib import Path
from datetime import datetime

def create_directories():
    """Create the standard project directory structure."""
    root = Path(".")
    
    # Define the required directories relative to project root
    required_dirs = [
        "code",
        "data",
        "state",
        "tests",
        "docs"
    ]
    
    created = []
    for dir_name in required_dirs:
        dir_path = root / dir_name
        # Create parent directories if they don't exist
        dir_path.mkdir(parents=True, exist_ok=True)
        created.append(str(dir_path))
        print(f"Created directory: {dir_path}")
    
    return created

def create_manifest(created_dirs):
    """Create a manifest file documenting the structure creation."""
    manifest_path = Path("docs") / "structure_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest_data = {
        "task_id": "T001",
        "description": "Create project structure per plan.md",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "directories": created_dirs,
        "status": "completed"
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    
    print(f"Created manifest: {manifest_path}")
    return manifest_path

def main():
    """Main entry point for T001."""
    print("Starting T001: Create project structure...")
    created = create_directories()
    manifest = create_manifest(created)
    print(f"T001 Complete. Structure created. Manifest at {manifest}")

if __name__ == "__main__":
    main()
