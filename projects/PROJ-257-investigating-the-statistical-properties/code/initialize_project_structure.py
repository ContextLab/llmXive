import json
import os
from pathlib import Path

def create_directories():
    """Create the required project directory structure."""
    base_dir = Path.cwd()
    
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "output/results",
        "output/figures",
        "logs",
        "src/data",
        "src/analysis",
        "src/viz",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure empty directories are tracked
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

def generate_manifest():
    """Generate the project structure manifest JSON file."""
    base_dir = Path.cwd().resolve()
    
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "output/results",
        "output/figures",
        "logs",
        "src/data",
        "src/analysis",
        "src/viz",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    manifest = {}
    
    for dir_rel_path in directories:
        full_path = base_dir / dir_rel_path
        abs_path = str(full_path.resolve())
        
        # Get subdirectories (children that are directories)
        subdirs = []
        if full_path.exists():
            for child in full_path.iterdir():
                if child.is_dir() and not child.name.startswith('.'):
                    subdirs.append(child.name)
        
        manifest[abs_path] = subdirs
    
    # Write manifest to file
    manifest_path = base_dir / "project_structure_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest_path

def main():
    """Main entry point for project initialization."""
    print("Creating project directory structure...")
    create_directories()
    print("Generating project structure manifest...")
    manifest_path = generate_manifest()
    print(f"Manifest created at: {manifest_path}")
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
