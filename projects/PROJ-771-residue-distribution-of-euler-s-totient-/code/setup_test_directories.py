import os
from pathlib import Path

def setup_test_directories():
    """
    Creates the required test directory structure:
    - tests/unit/
    - tests/integration/

    Returns True if successful, False otherwise.
    """
    base_dir = Path(__file__).parent.parent
    tests_dir = base_dir / "tests"
    unit_dir = tests_dir / "unit"
    integration_dir = tests_dir / "integration"

    try:
        unit_dir.mkdir(parents=True, exist_ok=True)
        integration_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directories: {unit_dir}, {integration_dir}")
        return True
    except OSError as e:
        print(f"Error creating test directories: {e}")
        return False

if __name__ == "__main__":
    success = setup_test_directories()
    exit(0 if success else 1)