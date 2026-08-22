"""
Script to initialize the test directory structure for the project.
Creates the necessary folders for unit, integration, and contract tests.
"""
import os
from pathlib import Path
import sys

# Add the project root to the path to import config if needed, 
# though we can also derive paths relative to this file's location.
# Assuming this script runs from the project root or code/ directory.

# Determine project root based on script location (code/setup_tests_structure.py)
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
tests_dir = project_root / "tests"

def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main():
    """Create the test directory structure."""
    print(f"Initializing test structure in: {tests_dir}")
    
    # Core test directories
    ensure_dir(tests_dir)
    ensure_dir(tests_dir / "unit")
    ensure_dir(tests_dir / "integration")
    ensure_dir(tests_dir / "contract")
    ensure_dir(tests_dir / "fixtures")
    
    # Create __init__.py files to make them Python packages
    (tests_dir / "__init__.py").touch()
    (tests_dir / "unit" / "__init__.py").touch()
    (tests_dir / "integration" / "__init__.py").touch()
    (tests_dir / "contract" / "__init__.py").touch()
    (tests_dir / "fixtures" / "__init__.py").touch()
    
    # Create placeholder README for tests
    readme_content = """# Tests

This directory contains the test suite for the project.

## Structure
- `unit/`: Unit tests for individual components.
- `integration/`: Integration tests for component interactions.
- `contract/`: Contract tests for API/schema compliance.
- `fixtures/`: Shared test data and fixtures.

## Running Tests
Run tests using pytest from the project root:
```bash
pytest tests/
```
"""
    readme_path = tests_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(readme_content)
        print(f"Created: {readme_path}")
    
    print("Test directory structure initialization complete.")

if __name__ == "__main__":
    main()