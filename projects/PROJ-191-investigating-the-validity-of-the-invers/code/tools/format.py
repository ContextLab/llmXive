"""
Formatting tool wrapper for Black.
Ensures code adheres to the project's formatting standards.
"""
import subprocess
import sys
from pathlib import Path

def run_command():
    """Run Black formatter on the project code directory."""
    project_root = Path(__file__).resolve().parent.parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    cmd = [
        sys.executable, "-m", "black",
        "--config", str(project_root / "pyproject.toml"),
        str(code_dir),
        str(tests_dir)
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("Formatting failed. Please check the output above.")
        sys.exit(result.returncode)
    
    print("Formatting successful.")
    return 0

def main():
    """Entry point for the format script."""
    run_command()

if __name__ == "__main__":
    main()
