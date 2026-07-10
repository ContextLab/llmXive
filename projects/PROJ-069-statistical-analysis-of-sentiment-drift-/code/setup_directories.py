import os
import sys
from pathlib import Path

def initialize_structure(base_dir: Path) -> list[str]:
    """
    Initialize the project directory structure for the llmXive pipeline.
    
    Creates the following directories relative to base_dir:
    - code/
    - data/raw/
    - data/processed/
    - data/metadata/
    - results/
    - tests/
    - artifacts/
    - docs/
    
    Returns a list of created directory paths as strings.
    """
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/metadata",
        "results",
        "tests",
        "artifacts",
        "docs"
    ]
    
    created_paths = []
    
    for dir_name in required_dirs:
        full_path = base_dir / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
        else:
            # Ensure it's actually a directory
            if not full_path.is_dir():
                raise FileExistsError(f"Path exists but is not a directory: {full_path}")
            created_paths.append(str(full_path))
    
    return created_paths

def main():
    """Main entry point for directory initialization."""
    # Determine project root (parent of code/ if running from code/)
    if Path("code/setup_directories.py").exists():
        project_root = Path(__file__).resolve().parent.parent
    else:
        project_root = Path.cwd()
    
    print(f"Initializing project structure at: {project_root}")
    
    try:
        created = initialize_structure(project_root)
        print(f"Successfully created/verified {len(created)} directories:")
        for path in sorted(created):
            print(f"  - {path}")
        
        # Generate a manifest file for verification
        manifest_path = project_root / "data" / ".directory_manifest.txt"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write("# Project Directory Structure Manifest\n")
            f.write(f"# Generated: {Path.cwd()}\n\n")
            for path in sorted(created):
                f.write(f"{path}\n")
        
        print(f"\nManifest written to: {manifest_path}")
        return 0
        
    except Exception as e:
        print(f"Error initializing directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
