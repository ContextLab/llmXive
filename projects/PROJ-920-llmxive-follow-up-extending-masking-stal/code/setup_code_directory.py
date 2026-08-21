import os
from pathlib import Path

def main():
    """Create the code/ directory if it doesn't exist."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        code_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {code_dir}")
    else:
        print(f"Directory already exists: {code_dir}")

if __name__ == "__main__":
    main()