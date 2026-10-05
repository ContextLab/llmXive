"""Script to create the full project directory structure and verify existence."""
import os
import sys
from pathlib import Path
from typing import Optional

def get_project_root() -> Path:
    """Determine the project root directory (parent of 'code' or current dir)."""
    current = Path(__file__).resolve()
    # If running from code/scripts/, go up two levels
    if current.name == "create_project_structure.py":
        return current.parent.parent.parent
    return current.parent.parent

def ensure_directory(path: Path) -> bool:
    """Create a directory if it does not exist. Returns True if created or exists."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main() -> int:
    """Create the required directory structure for the project."""
    root = get_project_root()
    
    # Define the required directories relative to the project root
    # Based on tasks.md T002 and T001 requirements
    required_dirs = [
        # Source subdirectories
        root / "src" / "data",
        root / "src" / "analysis",
        root / "src" / "stats",
        root / "src" / "config",
        root / "src" / "utils",
        root / "src" / "entities",
        
        # Test subdirectories
        root / "tests" / "unit",
        root / "tests" / "integration",
        
        # Root level directories (from T001, ensuring they exist for completeness)
        root / "data",
        root / "reports",
        root / "docs",
        root / "scripts",
        root / "state",
    ]

    success = True
    for dir_path in required_dirs:
        if ensure_directory(dir_path):
            print(f"Created/Verified: {dir_path.relative_to(root)}")
        else:
            success = False
            print(f"FAILED to create: {dir_path.relative_to(root)}", file=sys.stderr)

    # Create __init__.py files to make them packages
    for dir_path in required_dirs:
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            # Write a minimal docstring
            init_file.write_text(f'"""Auto-generated package init for {dir_path.name}.\"""\n')
            print(f"Created: {init_file.relative_to(root)}")

    if success:
        print("\nDirectory structure verification complete.")
        return 0
    else:
        print("\nDirectory structure creation failed.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())