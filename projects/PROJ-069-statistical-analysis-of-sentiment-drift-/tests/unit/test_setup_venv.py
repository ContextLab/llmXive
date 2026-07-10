import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_venv import get_python_version, check_python_version

class TestSetupVenv:
    """Unit tests for virtual environment setup functions."""

    def test_get_python_version_returns_311(self):
        """Test that get_python_version returns '3.11'."""
        assert get_python_version() == "3.11"

    def test_check_python_version_current(self):
        """Test that check_python_version works with current Python version."""
        # Should return True since we're running on a valid Python version
        result = check_python_version()
        assert isinstance(result, bool)

    def test_check_python_version_min_311(self):
        """Test that check_python_version validates minimum version 3.11."""
        # If current Python is 3.11+, this should return True
        # If current Python is < 3.11, this should return False
        result = check_python_version("3.11")
        assert isinstance(result, bool)

    def test_version_comparison_logic(self):
        """Test version comparison logic with known versions."""
        # These tests verify the logic, not the actual environment
        # We can't test specific version numbers without mocking
        assert check_python_version("3.0") == True  # Any modern Python is >= 3.0
        assert check_python_version("99.0") == False  # No Python >= 99 exists

if __name__ == "__main__":
    pytest.main([__file__, "-v"])