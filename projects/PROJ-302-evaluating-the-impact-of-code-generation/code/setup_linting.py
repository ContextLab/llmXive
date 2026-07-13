"""
Setup script for linting and formatting tools.

This script installs and configures ruff and black for the project.
"""

import subprocess
import sys
from pathlib import Path

# Import configuration from utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from code.utils.linting_config import create_combined_config, create_git_hooks

def install_tools():
    """Install black and ruff if not already installed."""
    print("Checking for required tools...")
    
    tools = [
        ("black", "black"),
        ("ruff", "ruff"),
    ]
    
    for package, command in tools:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                capture_output=True,
                check=True
            )
            print(f"✓ {package} is already installed")
        except subprocess.CalledProcessError:
            print(f"Installing {package}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True
            )
            print(f"✓ {package} installed successfully")

def main():
    """Main entry point for setup."""
    print("=" * 60)
    print("Setting up Linting and Formatting Tools")
    print("=" * 60)
    
    # Install tools
    install_tools()
    
    # Create configuration files
    print("\nCreating configuration files...")
    config_path = create_combined_config()
    print(f"✓ Created {config_path}")
    
    # Create git hooks if .git exists
    git_dir = Path(".git")
    if git_dir.exists():
        print("\nCreating git hooks...")
        try:
            create_git_hooks()
            print("✓ Created pre-commit hook")
        except Exception as e:
            print(f"⚠ Warning: Could not create git hooks: {e}")
    else:
        print("\n⚠ No .git directory found. Skipping git hook creation.")
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Format your code: black .")
    print("2. Lint your code: ruff check .")
    print("3. Fix linting issues: ruff check . --fix")
    print("4. (Optional) Commit a test file to trigger the pre-commit hook")

if __name__ == "__main__":
    main()