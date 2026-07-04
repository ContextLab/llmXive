"""
Script to initialize the tests/ directory structure for the project.
This script creates the tests/ directory and a placeholder conftest.py
to ensure the directory exists and is ready for test files.
"""
import os
import sys
from pathlib import Path

# Ensure the script is run from the project root
def main():
    root = Path.cwd()
    tests_dir = root / "tests"

    if tests_dir.exists():
        print(f"Directory {tests_dir} already exists.")
    else:
        tests_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {tests_dir}")

    # Create a placeholder conftest.py if it doesn't exist
    conftest = tests_dir / "conftest.py"
    if not conftest.exists():
        conftest.write_text(
            "# Shared fixtures and configuration for pytest\n"
            "# Add shared fixtures here as the project grows.\n"
            "\n"
            "import pytest\n"
            "from pathlib import Path\n"
            "\n"
            "@pytest.fixture(scope=\"session\")\n"
            "def project_root() -> Path:\n"
            "    \"\"\"Return the path to the project root.\"\"\"\n"
            "    return Path(__file__).parent.parent\n"
            "\n"
            "@pytest.fixture(scope=\"session\")\n"
            "def data_dir(project_root: Path) -> Path:\n"
            "    \"\"\"Return the path to the data directory.\"\"\"\n"
            "    return project_root / \"data\"\n"
            "\n"
            "@pytest.fixture(scope=\"session\")\n"
            "def code_dir(project_root: Path) -> Path:\n"
            "    \"\"\"Return the path to the code directory.\"\"\"\n"
            "    return project_root / \"code\"\n"
        )
        print(f"Created placeholder file: {conftest}")
    else:
        print(f"File {conftest} already exists.")

    print("Tests directory setup complete.")

if __name__ == "__main__":
    main()