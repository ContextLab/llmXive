import os
import json
from pathlib import Path
from typing import List

def create_directories(root_dir: Path) -> List[Path]:
    """Create the standard project directory structure."""
    dirs = [
        root_dir / "code",
        root_dir / "data" / "raw",
        root_dir / "data" / "processed",
        root_dir / "data" / "metadata",
        root_dir / "tests",
        root_dir / "docs",
        root_dir / "specs" / "001-quantifying-disorder-effect" / "contracts",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def create_gitkeep_files(root_dir: Path) -> List[Path]:
    """Create .gitkeep files in data and docs directories to ensure they are tracked."""
    target_dirs = [
        root_dir / "data" / "raw",
        root_dir / "data" / "processed",
        root_dir / "data" / "metadata",
        root_dir / "docs",
        root_dir / "specs" / "001-quantifying-disorder-effect" / "contracts",
    ]
    created_files = []
    for d in target_dirs:
        d.mkdir(parents=True, exist_ok=True)
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            created_files.append(gitkeep)
    return created_files

def verify_structure(root_dir: Path) -> bool:
    """Verify that all required directories and .gitkeep files exist."""
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/metadata",
        "tests",
        "docs",
        "specs/001-quantifying-disorder-effect/contracts",
    ]
    for rel_path in required_dirs:
        if not (root_dir / rel_path).exists():
            print(f"Missing directory: {root_dir / rel_path}")
            return False

    required_gitkeeps = [
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "data/metadata/.gitkeep",
        "docs/.gitkeep",
        "specs/001-quantifying-disorder-effect/contracts/.gitkeep",
    ]
    for rel_path in required_gitkeeps:
        if not (root_dir / rel_path).exists():
            print(f"Missing .gitkeep: {root_dir / rel_path}")
            return False

    return True

def main():
    root_dir = Path(__file__).resolve().parent.parent
    print(f"Setting up project structure in: {root_dir}")
    
    dirs = create_directories(root_dir)
    print(f"Created directories: {[str(d) for d in dirs]}")
    
    gitkeeps = create_gitkeep_files(root_dir)
    if gitkeeps:
        print(f"Created .gitkeep files: {[str(g) for g in gitkeeps]}")
    else:
        print("All .gitkeep files already exist.")
    
    if verify_structure(root_dir):
        print("Project structure verification: PASSED")
    else:
        print("Project structure verification: FAILED")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
