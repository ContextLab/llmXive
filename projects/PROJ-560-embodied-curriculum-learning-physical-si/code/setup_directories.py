import os
import sys
from pathlib import Path

def create_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """Create required project directories."""
    root = Path(__file__).resolve().parent.parent
    
    # Code directories
    code_src = root / "code" / "src"
    code_tests = root / "code" / "tests"
    
    create_directory(code_src)
    create_directory(code_tests)
    
    # Ensure __init__.py files exist for Python packages
    (code_src / "__init__.py").touch(exist_ok=True)
    (code_tests / "__init__.py").touch(exist_ok=True)
    
    print("Code directory structure created successfully.")

if __name__ == "__main__":
    main()
