import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=Path(__file__).parent.parent)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False

def main() -> None:
    """Install and configure ruff and black for the project."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    # Ensure config files exist (they are created by this task's artifact generation)
    # but we verify they are present here just in case.
    ruff_config = project_root / ".ruff.toml"
    pyproject = project_root / "pyproject.toml"

    if not ruff_config.exists():
        print("Warning: .ruff.toml not found. Please ensure it was generated.")
    if not pyproject.exists():
        print("Warning: pyproject.toml not found. Please ensure it was generated.")

    # Install dependencies
    print("Installing linting and formatting tools...")
    if not run_command([sys.executable, "-m", "pip", "install", "ruff", "black"]):
        print("Failed to install tools.")
        sys.exit(1)

    # Run initial check (dry run) to verify configuration
    print("Verifying configuration...")
    if not run_command([sys.executable, "-m", "ruff", "check", str(code_dir)]):
        print("Ruff check found issues (expected on initial run).")
    
    if not run_command([sys.executable, "-m", "black", "--check", str(code_dir)]):
        print("Black check found issues (expected on initial run).")

    print("Linting and formatting tools configured successfully.")
    print("To format code, run: black code/")
    print("To fix linting issues, run: ruff check --fix code/")

if __name__ == "__main__":
    main()