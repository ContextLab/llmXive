"""
Script to install and configure linting (ruff) and formatting (black) tools.
This script ensures the tools are installed and sets up the configuration files.
"""
import subprocess
import sys
import os
import tomllib
from pathlib import Path

def run_command(cmd: list[str]) -> None:
    """Run a command and raise an error if it fails."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

def main() -> None:
    """Main entry point for setup_linting."""
    print("Setting up linting and formatting tools for llmXive...")

    # Ensure we are in the code directory
    code_dir = Path(__file__).resolve().parent.parent
    os.chdir(code_dir)

    # 1. Install ruff and black if not present
    print("\n1. Installing ruff and black...")
    run_command([sys.executable, "-m", "pip", "install", "ruff", "black", "pre-commit"])

    # 2. Verify configuration files exist
    print("\n2. Verifying configuration files...")
    config_files = [
        "pyproject.toml",
        ".ruff.toml",
        ".pre-commit-config.yaml"
    ]

    for config_file in config_files:
        if not (code_dir / config_file).exists():
            print(f"ERROR: Configuration file {config_file} not found in {code_dir}")
            sys.exit(1)
        print(f"   Found: {config_file}")

    # 3. Validate pyproject.toml syntax
    print("\n3. Validating pyproject.toml...")
    try:
        with open(code_dir / "pyproject.toml", "rb") as f:
            tomllib.load(f)
        print("   pyproject.toml is valid TOML.")
    except Exception as e:
        print(f"   ERROR: Invalid pyproject.toml: {e}")
        sys.exit(1)

    # 4. Run ruff check to ensure no immediate errors (ignoring E501 as per config)
    print("\n4. Running initial ruff check...")
    try:
        run_command(["ruff", "check", "src", "tests", "scripts", "--select", "E,F,W,I,C,B"])
        print("   Ruff check passed (no errors found).")
    except subprocess.CalledProcessError as e:
        # This is expected if there are existing linting issues; we don't fail the setup
        print(f"   Note: Ruff found issues (this is expected for new code). Run 'ruff check --fix' to resolve.")

    # 5. Run black --check to ensure formatting is ready
    print("\n5. Running initial black check...")
    try:
        run_command(["black", "--check", "src", "tests", "scripts"])
        print("   Black check passed (code is formatted).")
    except subprocess.CalledProcessError:
        print("   Note: Code needs formatting. Run 'black src tests scripts' to fix.")

    # 6. Install pre-commit hooks
    print("\n6. Installing pre-commit hooks...")
    run_command(["pre-commit", "install"])
    print("   Pre-commit hooks installed successfully.")

    print("\n✅ Linting and formatting setup complete!")
    print("\nUsage:")
    print("  - Run linter: ruff check src tests scripts")
    print("  - Run formatter: black src tests scripts")
    print("  - Fix linting issues: ruff check --fix src tests scripts")
    print("  - Run on commit: git commit (pre-commit will run automatically)")

if __name__ == "__main__":
    main()
