"""
Script to run black formatter on the project.
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Run black format on the project."""
    project_root = Path(__file__).parent.parent.parent
    print(f"Running formatter in: {project_root}")

    try:
        result = subprocess.run(
            ["black", "."],
            cwd=project_root,
            check=True,
            capture_output=False,
        )
        print("Formatting completed successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Formatting failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("Error: 'black' not found. Please install it via 'pip install black'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
