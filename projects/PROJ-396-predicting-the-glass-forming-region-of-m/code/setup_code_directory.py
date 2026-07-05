import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the 'code/' directory at the repository root."""
    root = Path(__file__).resolve().parents[1]
    code_dir = root / "code"
    create_directory(code_dir)
    print(f"Directory '{code_dir}' created successfully.")
    return code_dir

if __name__ == "__main__":
    main()
