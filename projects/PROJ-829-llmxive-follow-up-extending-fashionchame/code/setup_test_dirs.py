import os
import sys
from pathlib import Path

def main():
    """Create test directory structure at repository root."""
    # Determine repository root (assuming code/ is at root)
    # We assume the script is run from the repository root or code/ directory
    # To be safe, we resolve relative to the script location's parent if in code/
    script_path = Path(__file__).resolve()
    if script_path.name == "setup_test_dirs.py" and script_path.parent.name == "code":
        repo_root = script_path.parent.parent
    else:
        # Fallback: assume current working directory is repo root
        repo_root = Path.cwd()

    # Define test directories
    test_dirs = [
        repo_root / "tests" / "unit",
        repo_root / "tests" / "integration",
    ]

    # Create directories
    created_dirs = []
    for dir_path in test_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(dir_path.relative_to(repo_root)))
        print(f"Created directory: {dir_path.relative_to(repo_root)}")

    # Create __init__.py files to make them proper Python packages
    for dir_path in test_dirs:
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Test package\n")
            print(f"Created __init__.py: {init_file.relative_to(repo_root)}")

    print(f"Test directory structure created successfully in: {repo_root}")
    return 0

if __name__ == "__main__":
    sys.exit(main())