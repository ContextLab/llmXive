"""
Dependency setup script for llmXive project.
Installs core dependencies and generates requirements.txt with pinned versions.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, check: bool = True) -> None:
    """Run a shell command, raising an error on failure if check=True."""
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"Error output: {e.stderr}", file=sys.stderr)
        raise

def main() -> None:
    """
    Main entry point for dependency installation.
    1. Ensures pip, setuptools, and wheel are installed/upgraded.
    2. Installs core dependencies: pandas, numpy, scipy.
    3. Generates requirements.txt with exact pinned versions via pip freeze.
    """
    print("Starting dependency setup...")

    # Step 1: Ensure build tools are present
    print("Ensuring pip, setuptools, and wheel are installed...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])

    # Step 2: Install core scientific dependencies
    # We install them explicitly first to ensure they are present in the environment
    # before freezing. The version will be resolved by pip.
    print("Installing core dependencies (pandas, numpy, scipy)...")
    run_command([sys.executable, "-m", "pip", "install", "pandas", "numpy", "scipy"])

    # Step 3: Generate requirements.txt with exact pinned versions
    print("Generating requirements.txt with pinned versions...")
    output_path = Path("requirements.txt")
    
    # Run pip freeze to get the exact versions currently installed
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Write the output to requirements.txt
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.stdout)
    
    print(f"Successfully generated {output_path}")
    print("Dependency setup complete.")

if __name__ == "__main__":
    main()
