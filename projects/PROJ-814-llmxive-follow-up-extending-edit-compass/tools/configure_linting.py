"""
Script to verify and initialize linting and formatting configurations.
This script checks for the presence of configuration files and installs
the necessary development dependencies.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
            shell=False
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        raise

def main():
    """Main entry point for the configuration script."""
    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"
    ruff_path = project_root / ".ruff.toml"
    black_path = project_root / ".black.toml"

    print(f"Project root: {project_root}")

    # Verify configuration files exist
    configs = [
        ("pyproject.toml", pyproject_path),
        (".ruff.toml", ruff_path),
        (".black.toml", black_path),
    ]

    all_present = True
    for name, path in configs:
        if path.exists():
            print(f"✓ {name} found at {path}")
        else:
            print(f"✗ {name} NOT found at {path}")
            all_present = False

    if not all_present:
        print("Error: Missing configuration files. Please ensure they are created.")
        sys.exit(1)

    # Check if dev dependencies are installed
    print("\nChecking for dev dependencies (ruff, black)...")
    try:
        import ruff
        print("✓ ruff is installed")
    except ImportError:
        print("⚠ ruff is not installed. Installing...")
        run_command([sys.executable, "-m", "pip", "install", "ruff"])

    try:
        import black
        print("✓ black is installed")
    except ImportError:
        print("⚠ black is not installed. Installing...")
        run_command([sys.executable, "-m", "pip", "install", "black"])

    # Run a quick syntax check on the project using ruff
    print("\nRunning ruff check on code/...")
    code_dir = project_root / "code"
    if code_dir.exists():
        run_command([sys.executable, "-m", "ruff", "check", str(code_dir)], check=False)
    else:
        print(f"⚠ code/ directory not found at {code_dir}")

    # Run a quick formatting check using black
    print("\nRunning black --check on code/...")
    if code_dir.exists():
        run_command([sys.executable, "-m", "black", "--check", str(code_dir)], check=False)
    else:
        print(f"⚠ code/ directory not found at {code_dir}")

    print("\nLinting and formatting configuration complete.")

if __name__ == "__main__":
    main()