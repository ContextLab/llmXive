"""
Utility module to programmatically verify linting and formatting configurations.
This script ensures that the project's flake8 and black configurations are valid
and can be executed without error.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and report status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,  # We handle exit codes manually
            cwd=Path(__file__).parent.parent.parent
        )
        
        if result.returncode == 0:
            print(f"  ✓ {description} passed")
            return True
        else:
            print(f"  ✗ {description} failed")
            if result.stdout:
                print(f"    Output: {result.stdout[:200]}")
            if result.stderr:
                print(f"    Errors: {result.stderr[:200]}")
            return False
    except FileNotFoundError:
        print(f"  ✗ {description} failed: Command not found")
        return False
    except Exception as e:
        print(f"  ✗ {description} failed with exception: {e}")
        return False

def main():
    """Verify linting and formatting configurations."""
    root_dir = Path(__file__).parent.parent.parent
    os.chdir(root_dir)

    print("=== Linting and Formatting Configuration Verification ===\n")

    # Check if tools are installed
    tools_installed = True
    
    # Check black
    black_ok = run_command(
        [sys.executable, "-m", "black", "--check", "--version"],
        "Black installation check"
    )
    if not black_ok:
        tools_installed = False

    # Check flake8
    flake8_ok = run_command(
        [sys.executable, "-m", "flake8", "--version"],
        "Flake8 installation check"
    )
    if not flake8_ok:
        tools_installed = False

    if not tools_installed:
        print("\n⚠️  Linting/formatting tools not installed. Run:")
        print("    pip install black flake8")
        return 1

    # Verify configuration files exist
    black_config = root_dir / "pyproject.toml"
    flake8_config = root_dir / ".flake8"

    if not black_config.exists():
        print(f"✗ Black config not found: {black_config}")
        return 1
    
    if not flake8_config.exists():
        print(f"✗ Flake8 config not found: {flake8_config}")
        return 1

    print("\nConfiguration files found:")
    print(f"  - {black_config}")
    print(f"  - {flake8_config}")

    # Test configuration validity by running on current code (excluding data/results)
    print("\n--- Validating Configurations ---")

    # Test black config by parsing (dry run on a small subset)
    black_check = run_command(
        [sys.executable, "-m", "black", "--check", "--diff", "code/utils/linting_setup.py"],
        "Black configuration validation"
    )

    # Test flake8 config by running on current file
    flake8_check = run_command(
        [sys.executable, "-m", "flake8", "code/utils/linting_setup.py"],
        "Flake8 configuration validation"
    )

    if black_check and flake8_check:
        print("\n✅ All linting and formatting configurations are valid and working.")
        return 0
    else:
        print("\n⚠️  Some configuration checks failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())