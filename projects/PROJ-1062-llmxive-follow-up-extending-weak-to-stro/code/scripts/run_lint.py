"""
Script to run Ruff linter on the project.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Execute Ruff linter on the code directory."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)

    print(f"Running Ruff linter on {code_dir}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--fix", str(code_dir)],
            check=True,
            capture_output=False,
        )
        print("Linting completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Linting failed with exit code {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: Ruff is not installed. Please install it with: pip install ruff")
        sys.exit(1)

if __name__ == "__main__":
    main()
