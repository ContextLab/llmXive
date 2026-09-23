"""
Script to initialize and install pre-commit hooks for the project.

This script:
1. Initializes the pre-commit git hook system
2. Installs the pre-commit hook to .git/hooks/pre-commit
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✓ {description} completed successfully\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed!")
        print(f"Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def main() -> int:
    """Main entry point for pre-commit setup."""
    project_root = Path(__file__).parent.parent
    config_path = project_root / ".pre-commit-config.yaml"
    
    # Verify config file exists
    if not config_path.exists():
        print(f"Error: Pre-commit config file not found at {config_path}")
        print("Please ensure .pre-commit-config.yaml exists in the project root.")
        return 1
    
    print(f"Found pre-commit config at: {config_path}")
    print("=" * 60)
    
    # Step 1: Initialize pre-commit
    success = run_command(
        ["pre-commit", "init"],
        "Initialize pre-commit"
    )
    
    if not success:
        print("Failed to initialize pre-commit. Aborting.")
        return 1
    
    # Step 2: Install the hook
    success = run_command(
        ["pre-commit", "install"],
        "Install pre-commit hook"
    )
    
    if not success:
        print("Failed to install pre-commit hook. Aborting.")
        return 1
    
    print("=" * 60)
    print("Pre-commit setup completed successfully!")
    print("You can now run 'pre-commit run --all-files' to test on all files.")
    print("Hooks will automatically run on 'git commit'.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
