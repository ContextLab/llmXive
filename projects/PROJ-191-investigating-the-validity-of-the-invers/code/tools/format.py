"""
Formatting tool wrapper for Black.
Runs Black on the codebase to ensure consistent formatting.
"""
import subprocess
import sys
from pathlib import Path


def run_command():
    """Run Black formatter on the project directory."""
    project_root = Path(__file__).resolve().parent.parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    cmd = [
        sys.executable,
        "-m",
        "black",
        "--config",
        str(project_root / "pyproject.toml"),
        str(code_dir),
        str(tests_dir),
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Formatting completed successfully.")
        if result.stdout:
            print(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Formatting failed with exit code {e.returncode}")
        if e.stderr:
            print(e.stderr)
        if e.stdout:
            print(e.stdout)
        return 1


def main():
    """Entry point for the format tool."""
    print("Running Black formatter...")
    sys.exit(run_command())


if __name__ == "__main__":
    main()
