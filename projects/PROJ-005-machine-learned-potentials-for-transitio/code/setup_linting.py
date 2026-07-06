import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and print status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print(f"✓ {description} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ {description} encountered an unexpected error: {e}")
        return False

def main():
    """Main entry point for setting up linting tools."""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("=== Setting up Linting and Formatting Tools ===")

    # 1. Install flake8
    success = run_command(
        [sys.executable, "-m", "pip", "install", "flake8"],
        "Installing flake8"
    )
    if not success:
        print("Failed to install flake8. Aborting.")
        sys.exit(1)

    # 2. Install black
    success = run_command(
        [sys.executable, "-m", "pip", "install", "black"],
        "Installing black"
    )
    if not success:
        print("Failed to install black. Aborting.")
        sys.exit(1)

    # 3. Verify configuration files exist
    config_files = [".flake8", "pyproject.toml"]
    missing = [f for f in config_files if not (project_root / f).exists()]
    if missing:
        print(f"Warning: Configuration files missing: {missing}")
        print("Please ensure .flake8 and pyproject.toml are present in the project root.")

    print("\n=== Linting Setup Complete ===")
    print("To run linter: flake8 code/ tests/")
    print("To format code: black code/ tests/")

if __name__ == "__main__":
    main()
