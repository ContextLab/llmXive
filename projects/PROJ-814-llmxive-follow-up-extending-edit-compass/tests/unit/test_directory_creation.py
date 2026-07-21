"""
Test to verify that the tests/unit directory structure exists.

This test serves as a verification that T001f (Create directory tests/unit)
has been successfully completed.
"""
import os
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
code_root = Path(__file__).parent.parent.parent
if str(code_root / "code") not in sys.path:
    sys.path.insert(0, str(code_root / "code"))

class TestUnitDirectoryExists:
    """Test suite to verify the tests/unit directory structure."""

    def test_unit_directory_exists(self):
        """Assert that the tests/unit directory exists."""
        unit_dir = Path(__file__).parent
        assert unit_dir.exists(), f"Directory {unit_dir} does not exist"
        assert unit_dir.is_dir(), f"{unit_dir} exists but is not a directory"

    def test_init_file_exists(self):
        """Assert that __init__.py exists in tests/unit."""
        init_file = Path(__file__).parent / "__init__.py"
        assert init_file.exists(), f"__init__.py missing in {Path(__file__).parent}"

    def test_directory_is_importable(self):
        """Assert that tests.unit can be imported as a package."""
        try:
            import tests.unit
            assert tests.unit is not None
        except ImportError as e:
            pytest.fail(f"Failed to import tests.unit: {e}")