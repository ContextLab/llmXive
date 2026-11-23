"""
Project structure initialization for llmXive research pipeline.
Creates required directories and placeholder files as per plan.md.
"""
import os
import json
from pathlib import Path
from datetime import datetime
from config import ensure_dirs


def create_directories():
    """Create the required directory structure."""
    base_dir = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "docs",
        "state",
        "tests",
        "figures",
        "data/quality",
        "data/config"
    ]
    
    created_dirs = []
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))
    
    return created_dirs


def create_manifest():
    """Create a manifest file documenting the project structure."""
    base_dir = Path(__file__).resolve().parent.parent
    manifest_path = base_dir / "docs" / "project_structure_manifest.json"
    
    # Scan current directory structure
    structure = {
        "generated_at": datetime.now().isoformat(),
        "base_directory": str(base_dir),
        "directories": [],
        "files": []
    }
    
    for root, dirs, files in os.walk(base_dir):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        rel_root = Path(root).relative_to(base_dir)
        if str(rel_root) != '.':
            structure["directories"].append(str(rel_root))
        
        for file in files:
            if not file.startswith('.'):
                rel_file = rel_root / file
                structure["files"].append(str(rel_file))
    
    with open(manifest_path, 'w') as f:
        json.dump(structure, f, indent=2)
    
    return manifest_path


def main():
    """Main entry point for structure creation."""
    print("Creating project directory structure...")
    dirs = create_directories()
    print(f"Created {len(dirs)} directories:")
    for d in dirs:
        print(f"  - {d}")
    
    # Create placeholder files
    base_dir = Path(__file__).resolve().parent.parent
    placeholders = [
        "code/__init__.py",
        "data/.gitkeep",
        "docs/.gitkeep",
        "state/.gitkeep",
        "tests/.gitkeep",
        "figures/.gitkeep",
        "data/quality/.gitkeep",
        "data/config/.gitkeep"
    ]
    
    for placeholder in placeholders:
        file_path = base_dir / placeholder
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.touch()
            print(f"Created placeholder: {placeholder}")
        else:
            print(f"Placeholder exists: {placeholder}")
    
    manifest = create_manifest()
    print(f"\nProject structure manifest saved to: {manifest}")
    print("Project structure initialization complete.")


if __name__ == "__main__":
    main()
