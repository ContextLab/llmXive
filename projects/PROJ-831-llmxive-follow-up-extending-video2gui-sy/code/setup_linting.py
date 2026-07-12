"""
Setup script for linting and formatting tools.

This script installs Ruff and Black via pip and generates
their configuration files in the project root.
"""
import subprocess
import sys
from pathlib import Path

def install_tools():
    """Install ruff and black using pip."""
    print("Installing linting and formatting tools...")
    
    tools = [
        "ruff>=0.1.6",
        "black>=23.11.0",
        "pre-commit>=3.5.0"
    ]
    
    for tool in tools:
        print(f"  Installing {tool}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", tool],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"  Error installing {tool}:")
            print(result.stderr)
            sys.exit(1)
        print(f"  ✓ {tool} installed")
    
    print("\nAll tools installed successfully.")

def run_config_generator():
    """Run the linting configuration generator."""
    config_script = Path(__file__).parent / "config" / "linting.py"
    if config_script.exists():
        print("\nGenerating configuration files...")
        result = subprocess.run(
            [sys.executable, str(config_script)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("Error running config generator:")
            print(result.stderr)
            sys.exit(1)
        print(result.stdout)
    else:
        print(f"Warning: Config script not found at {config_script}")

def setup_git_hooks():
    """Initialize pre-commit git hooks."""
    print("\nInitializing pre-commit hooks...")
    result = subprocess.run(
        ["pre-commit", "install"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("Warning: Could not install pre-commit hooks:")
        print(result.stderr)
    else:
        print("✓ Pre-commit hooks installed")

def main():
    """Main entry point for setup."""
    print("=" * 60)
    print("Setting up Linting and Formatting Tools")
    print("=" * 60)
    
    install_tools()
    run_config_generator()
    setup_git_hooks()
    
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("\nTo run linting:")
    print("  ruff check .")
    print("\nTo run formatting:")
    print("  black .")
    print("\nTo run pre-commit hooks manually:")
    print("  pre-commit run --all-files")
    print("=" * 60)

if __name__ == "__main__":
    main()