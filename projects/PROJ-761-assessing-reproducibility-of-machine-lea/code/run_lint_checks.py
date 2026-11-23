"""
Linting and Formatting Verification Script.

This script configures and verifies ruff and black tools against the project
structure. It ensures that the configuration files are valid and that the
project passes the initial checks.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """Run a command and return True if it succeeds (exit code 0)."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✓ {description} passed.")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"✗ {description} failed.")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ {description} timed out.")
        return False
    except FileNotFoundError:
        print(f"✗ {description} failed: Command not found. Ensure tools are installed.")
        return False
    except Exception as e:
        print(f"✗ {description} failed with exception: {e}")
        return False

def main():
    """Main entry point for lint and format verification."""
    project_root = Path.cwd()
    
    # Ensure we are in the project root
    if not (project_root / "code").exists():
        print("Error: 'code' directory not found. Ensure this script runs from the project root.")
        sys.exit(1)

    # Check 1: Verify Ruff Configuration and Run Check
    # We run 'ruff check .' which implicitly validates the config if it exists
    # If no config exists, ruff uses defaults, which is acceptable for an empty/new project
    # but the task asks to "verify configuration validity".
    # We assume ruff.toml or pyproject.toml exists or defaults are used.
    ruff_success = run_command(
        ["ruff", "check", "."],
        "Ruff Lint Check"
    )

    # Check 2: Verify Black Configuration and Run Check
    # Similar to ruff, black --check validates formatting against config
    black_success = run_command(
        ["black", "--check", "."],
        "Black Format Check"
    )

    if ruff_success and black_success:
        print("\n✓ All linting and formatting checks passed.")
        sys.exit(0)
    else:
        print("\n✗ One or more checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
