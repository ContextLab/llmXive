import subprocess
import sys
from pathlib import Path

def main():
    """
    Setup pytest configuration and verify installation.
    This script ensures pytest is installed and creates a basic pytest.ini
    if it doesn't exist, then runs a quick discovery to verify configuration.
    """
    print("Setting up pytest environment...")

    # Ensure pytest is installed
    try:
        import pytest
        print(f"pytest version {pytest.__version__} found.")
    except ImportError:
        print("Installing pytest...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov"])
        import pytest
        print(f"pytest version {pytest.__version__} installed.")

    # Create pytest.ini if it doesn't exist
    root_dir = Path(__file__).resolve().parent.parent
    pytest_ini = root_dir / "pytest.ini"

    if not pytest_ini.exists():
        print(f"Creating {pytest_ini}...")
        content = """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
    ignore::UserWarning
"""
        pytest_ini.write_text(content)
        print(f"Created {pytest_ini}")
    else:
        print(f"{pytest_ini} already exists.")

    # Verify configuration by running a dry-run collection
    print("Verifying pytest configuration...")
    try:
        # Run pytest --collect-only to check config without executing tests
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            cwd=root_dir,
            capture_output=True,
            text=True
        )
        # We don't fail if no tests are found yet, just check for config errors
        if "ERROR" in result.stderr or "INTERNALERROR" in result.stderr:
            print(f"Configuration Error:\n{result.stderr}")
            sys.exit(1)
        else:
            print("pytest configuration verified successfully.")
    except Exception as e:
        print(f"Error verifying configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()