"""
Script to run Black code formatter on the project.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Execute Black formatter on the code directory."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)

    print(f"Running Black formatter on {code_dir}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--line-length", "88", str(code_dir)],
            check=True,
            capture_output=False,
        )
        print("Formatting completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Formatting failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: Black is not installed. Please install it with: pip install black")
        sys.exit(1)

if __name__ == "__main__":
    main()
