import os
import sys
from pathlib import Path
import pytest

class TestDirectoryStructure:
    """Tests to verify the existence of required directory structures."""

    def test_unit_directory_exists(self):
        """Verify that tests/unit directory exists."""
        unit_dir = Path(__file__).parent
        assert unit_dir.exists(), f"Directory {unit_dir} does not exist."
        assert unit_dir.is_dir(), f"{unit_dir} is not a directory."

    def test_integration_directory_exists(self):
        """Verify that tests/integration directory exists."""
        project_root = Path(__file__).parent.parent.parent
        integration_dir = project_root / "tests" / "integration"
        assert integration_dir.exists(), f"Directory {integration_dir} does not exist."
        assert integration_dir.is_dir(), f"{integration_dir} is not a directory."

    def test_unit_init_exists(self):
        """Verify that __init__.py exists in tests/unit."""
        unit_dir = Path(__file__).parent
        init_file = unit_dir / "__init__.py"
        assert init_file.exists(), f"File {init_file} does not exist."

    def test_integration_init_exists(self):
        """Verify that __init__.py exists in tests/integration."""
        project_root = Path(__file__).parent.parent.parent
        integration_dir = project_root / "tests" / "integration"
        init_file = integration_dir / "__init__.py"
        assert init_file.exists(), f"File {init_file} does not exist."
