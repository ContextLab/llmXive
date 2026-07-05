import os
from pathlib import Path
from setup_directories import create_directory, main as setup_main

def main():
    """Create the tests/integration/ directory."""
    root = Path(os.getcwd())
    target = root / "tests" / "integration"
    
    if not target.exists():
        create_directory(target)
        print(f"Created directory: {target}")
    else:
        print(f"Directory already exists: {target}")
    
    return 0

if __name__ == "__main__":
    exit(main())
