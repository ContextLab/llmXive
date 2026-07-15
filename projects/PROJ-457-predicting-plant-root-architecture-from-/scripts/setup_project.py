"""
Script to verify and create the project directory structure.
This script ensures all required directories exist as per T001.
"""
import os
from pathlib import Path

def create_structure():
    base = Path(__file__).parent.parent
    required_dirs = [
        base / "code",
        base / "tests",
        base / "data" / "raw",
        base / "data" / "processed",
        base / "artifacts" / "models",
        base / "artifacts" / "plots",
        base / "artifacts" / "reports",
    ]

    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked by git
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text(f"# {dir_path.name} directory\n")
        print(f"Verified/Created: {dir_path}")

    # Verify structure
    print("\nProject Structure Verification:")
    for dir_path in required_dirs:
        status = "✓" if dir_path.exists() else "✗"
        print(f"{status} {dir_path.relative_to(base)}")

if __name__ == "__main__":
    create_structure()