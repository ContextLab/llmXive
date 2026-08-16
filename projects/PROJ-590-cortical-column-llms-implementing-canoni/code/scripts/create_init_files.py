import os
from pathlib import Path

def ensure_init_files(root: Path) -> bool:
    """
    Create __init__.py files in all src/ and tests/ directories.
    Returns True if all files were created successfully.
    """
    # Define all directories that need __init__.py
    dirs = [
        "src",
        "src/models",
        "src/data",
        "src/training",
        "src/experiments",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration",
    ]
    
    success = True
    for d in dirs:
        path = root / d / "__init__.py"
        if not path.exists():
            try:
                path.write_text('"""' + d + " package.\n\"\"\"\n")
                print(f"Created: {path}")
            except OSError as e:
                print(f"Error creating {path}: {e}")
                success = False
        else:
            print(f"Exists: {path}")
    
    return success

def main():
    """Main entry point."""
    root = Path(__file__).parent.parent
    print(f"Creating init files in: {root}")
    
    if ensure_init_files(root):
        print("All init files created/verified successfully")
        return 0
    else:
        print("Some init files failed to create", file=__import__('sys').stderr)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())