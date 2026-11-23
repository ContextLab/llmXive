"""
Setup script to initialize linting (ruff) and formatting (black) tools.

This script:
1. Installs ruff and black into the environment.
2. Verifies the configuration files exist.
3. Runs a dry-run check to ensure tools are functional.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def main():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    
    # Ensure config files exist (created by this task's artifact generation)
    ruff_config = code_dir / ".ruff.toml"
    black_config = code_dir / ".black.toml"
    precommit_config = code_dir / ".pre-commit-config.yaml"

    if not ruff_config.exists():
        print(f"Error: {ruff_config} not found. Please ensure the artifact was created correctly.")
        sys.exit(1)
    if not black_config.exists():
        print(f"Error: {black_config} not found.")
        sys.exit(1)
    if not precommit_config.exists():
        print(f"Error: {precommit_config} not found.")
        sys.exit(1)

    print("Configuration files verified.")

    # Install tools
    print("\n--- Installing Tools ---")
    run_command([sys.executable, "-m", "pip", "install", "ruff", "black", "pre-commit"])

    # Verify installations
    print("\n--- Verifying Tools ---")
    run_command(["ruff", "--version"])
    run_command(["black", "--version"])

    # Initialize pre-commit hook (optional but recommended)
    print("\n--- Initializing Pre-commit ---")
    run_command(["pre-commit", "install"], check=False)
    print("Pre-commit hook installed (if git repo exists).")

    # Run a dry check on the current directory to ensure configs work
    print("\n--- Running Dry Check (Ruff) ---")
    # Use --no-fix to just check, --exit-zero to avoid failing if issues exist in existing code
    run_command(["ruff", "check", str(code_dir), "--config", str(ruff_config), "--exit-zero"])

    print("\n--- Setup Complete ---")
    print("Linting (Ruff) and Formatting (Black) are configured.")
    print("To run manually:")
    print("  ruff check code/")
    print("  black code/")

if __name__ == "__main__":
    main()
