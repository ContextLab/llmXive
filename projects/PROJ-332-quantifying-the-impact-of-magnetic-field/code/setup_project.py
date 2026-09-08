"""
Project initialization script.
Creates the required directory structure for the llmXive science pipeline.
"""
import os
import sys
from pathlib import Path


def main():
    """Create project directories as defined in plan.md."""
    base_dir = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        base_dir / "code",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "artifacts",
        base_dir / "tests",
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(base_dir)}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path.relative_to(base_dir)}")
    
    # Create __init__.py files to ensure Python package recognition
    # in all newly created or existing directories that should be packages
    package_dirs = [
        base_dir / "code",
        base_dir / "tests",
    ]
    
    for dir_path in package_dirs:
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py: {init_file.relative_to(base_dir)}")
        
        # Also create sub-package __init__.py if subdirs exist
        for subdir in dir_path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('.'):
                sub_init = subdir / "__init__.py"
                if not sub_init.exists():
                    sub_init.touch()
                    print(f"Created __init__.py: {sub_init.relative_to(base_dir)}")
    
    # Create data sub-package __init__.py
    data_dir = base_dir / "data"
    if data_dir.exists():
        data_init = data_dir / "__init__.py"
        if not data_init.exists():
            data_init.touch()
            print(f"Created __init__.py: {data_init.relative_to(base_dir)}")
        
        for subdir in data_dir.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('.'):
                sub_init = subdir / "__init__.py"
                if not sub_init.exists():
                    sub_init.touch()
                    print(f"Created __init__.py: {sub_init.relative_to(base_dir)}")
    
    print(f"\nProject structure initialization complete. Created/verified {created_count} directories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
