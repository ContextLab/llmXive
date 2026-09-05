"""
Linting configuration setup and verification script.
This script verifies that flake8 and black configurations are valid
and runs flake8 on a sample file to confirm the setup.
"""
import os
import sys
import subprocess
import tomli
from pathlib import Path

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists at the given path."""
    return Path(filepath).exists()

def validate_black_config() -> bool:
    """Validate that pyproject.toml contains valid black configuration."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("ERROR: pyproject.toml not found")
        return False

    try:
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)

        if "tool" not in config or "black" not in config["tool"]:
            print("ERROR: [tool.black] section not found in pyproject.toml")
            return False

        print("SUCCESS: Black configuration is valid")
        return True
    except Exception as e:
        print(f"ERROR: Failed to parse pyproject.toml: {e}")
        return False

def validate_flake8_config() -> bool:
    """Validate that .flake8 file exists and is readable."""
    flake8_path = Path(".flake8")
    if not flake8_path.exists():
        print("ERROR: .flake8 file not found")
        return False

    try:
        with open(flake8_path, "r") as f:
            content = f.read()
            if "max-line-length" not in content:
                print("WARNING: max-line-length not explicitly set in .flake8")
            else:
                print("SUCCESS: .flake8 configuration is valid")
        return True
    except Exception as e:
        print(f"ERROR: Failed to read .flake8: {e}")
        return False

def run_flake8_on_sample(sample_file: str = "code/tests/linting/sample_code.py") -> bool:
    """Run flake8 on a sample file and return success status."""
    if not check_file_exists(sample_file):
        print(f"ERROR: Sample file not found: {sample_file}")
        return False

    try:
        result = subprocess.run(
            ["flake8", sample_file],
            capture_output=True,
            text=True,
            check=False  # Don't raise on non-zero exit (linting errors are expected)
        )

        if result.returncode == 0:
            print(f"SUCCESS: flake8 passed on {sample_file} (no issues found)")
            return True
        else:
            print(f"INFO: flake8 found issues in {sample_file} (expected):")
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            print("SUCCESS: flake8 ran successfully and reported issues as expected")
            return True
    except FileNotFoundError:
        print("ERROR: flake8 command not found. Please install it: pip install flake8")
        return False
    except Exception as e:
        print(f"ERROR: Failed to run flake8: {e}")
        return False

def main():
    """Main entry point for linting setup verification."""
    print("=" * 60)
    print("Linting Configuration Verification")
    print("=" * 60)

    all_passed = True

    # Check .flake8
    if not validate_flake8_config():
        all_passed = False

    # Check pyproject.toml for black
    if not validate_black_config():
        all_passed = False

    # Run flake8 on sample file
    if not run_flake8_on_sample():
        all_passed = False

    print("=" * 60)
    if all_passed:
        print("OVERALL: All linting verification steps completed successfully")
        sys.exit(0)
    else:
        print("OVERALL: Some verification steps failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
