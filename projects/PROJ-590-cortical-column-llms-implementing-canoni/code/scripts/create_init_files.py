"""
Script to create __init__.py files in all src/ and tests/ directories (T002).
"""
import os
from pathlib import Path

def ensure_init_files(root_path: Path) -> None:
    """
    Creates empty __init__.py files in all src/ and tests/ subdirectories.
    """
    # Directories that need __init__.py
    target_roots = ["src", "tests"]
    
    created_count = 0
    
    for root_dir in target_roots:
        base_path = root_path / root_dir
        if not base_path.exists():
            print(f"Warning: {base_path} does not exist, skipping.")
            continue
        
        # Walk through all subdirectories
        for dirpath, dirnames, filenames in os.walk(base_path):
            init_file = Path(dirpath) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                created_count += 1
                print(f"Created: {init_file}")
            else:
                # Optionally update existing files with version info
                pass
    
    print(f"Created {created_count} __init__.py files.")

def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    print(f"Project root: {project_root}")
    ensure_init_files(project_root)
    print("__init__.py creation complete.")

if __name__ == "__main__":
    main()