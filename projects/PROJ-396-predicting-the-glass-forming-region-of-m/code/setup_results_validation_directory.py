import os
from pathlib import Path
from setup_directories import create_directory, main as setup_main

def main():
    """Create the results/validation/ directory."""
    base_dir = Path(__file__).resolve().parent.parent
    target_path = base_dir / "results" / "validation"
    
    if not target_path.exists():
        create_directory(target_path)
        print(f"Created directory: {target_path}")
    else:
        print(f"Directory already exists: {target_path}")

if __name__ == "__main__":
    main()