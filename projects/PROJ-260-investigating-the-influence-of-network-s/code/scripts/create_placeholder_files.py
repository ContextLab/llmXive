"""
Script to create placeholder __init__.py files for all required packages.
This ensures the directory structure is recognized as Python packages.
"""
import os
import sys
from pathlib import Path

def create_placeholder_files():
    """Create __init__.py files for all package directories."""
    base = Path(__file__).resolve().parent.parent.parent
    
    # Define all package directories that need __init__.py
    package_dirs = [
        "src",
        "src/models",
        "src/services",
        "src/cli",
        "src/lib",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created = []
    for dir_path in package_dirs:
        full_path = base / dir_path
        init_file = full_path / "__init__.py"
        
        # Ensure directory exists first
        full_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py if it doesn't exist or is empty
        if not init_file.exists() or init_file.stat().st_size == 0:
            init_file.write_text(f'"""{dir_path} package."""\n')
            created.append(str(init_file.relative_to(base)))
    
    return created

def main():
    """Main entry point."""
    print("Creating placeholder __init__.py files...")
    created = create_placeholder_files()
    print(f"Created {len(created)} __init__.py files:")
    for f in sorted(created):
        print(f"  - {f}")
    print("Placeholder file creation complete.")

if __name__ == "__main__":
    main()
