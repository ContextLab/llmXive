import json
import os
from pathlib import Path

def create_directories():
    """Create the required project directory structure."""
    root = Path.cwd()
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
        "tests/contract",
    ]
    for d in directories:
        (root / d).mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure empty directories are tracked
        gitkeep = root / d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

def generate_manifest():
    """Generate project_structure_manifest.json with directory details."""
    root = Path.cwd()
    manifest = {}
    for d in ['src', 'tests', 'data', 'output', 'logs']:
        for p in root.glob(f'{d}/**/*'):
            if p.is_dir():
                manifest[str(p.relative_to(root))] = {
                    "type": "directory",
                    "absolute": str(p.absolute())
                }
    
    manifest_path = root / 'project_structure_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    return manifest_path

def main():
    """Main entry point for T001."""
    print("Creating directory structure...")
    create_directories()
    print("Generating manifest...")
    manifest_path = generate_manifest()
    print(f"Manifest created at: {manifest_path}")
    print("T001 complete.")

if __name__ == "__main__":
    main()
