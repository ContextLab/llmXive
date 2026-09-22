"""
Script to run ruff linter on the project.
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Run ruff check on the project."""
    project_root = Path(__file__).parent.parent.parent
    print(f"Running linter in: {project_root}")

    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=project_root,
            check=True,
            capture_output=False,
        )
        print("Linting passed successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Linting failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("Error: 'ruff' not found. Please install it via 'pip install ruff'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
