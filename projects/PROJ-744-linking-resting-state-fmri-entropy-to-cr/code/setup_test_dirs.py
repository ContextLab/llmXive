import os
import sys
from pathlib import Path

def main():
    """
    Create the 'tests/' directory at the project root.
    This script is idempotent; it will not fail if the directory exists.
    """
    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"

    try:
        tests_dir.mkdir(parents=True, exist_ok=True)
        print(f"Directory created/verified: {tests_dir}")
        
        # Create a placeholder __init__.py to ensure it is treated as a package
        init_file = tests_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Test package for llmXive project\n")
            print(f"Created placeholder: {init_file}")
        
        return True
    except PermissionError:
        print(f"Error: Permission denied creating directory {tests_dir}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error creating directory {tests_dir}: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)