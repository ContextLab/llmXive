"""
Contract tests for the output directory structure.

Ensures that the required directories for figures and reports exist
and are writable.
"""
import os
from pathlib import Path
import pytest

# Import the setup function
import sys
from pathlib import Path

code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_output_dirs import setup_output_directories


class TestOutputDirectoryContract:
    """Contract tests for output directory structure."""

    def test_figures_directory_exists_and_is_writable(self):
        """Verify the figures directory exists and is writable."""
        # Run setup to ensure directories are created
        result = setup_output_directories()
        
        figures_dir = result["figures"]
        
        # Contract: Must be a directory
        assert figures_dir.is_dir(), f"Figures directory {figures_dir} does not exist or is not a directory"
        
        # Contract: Must be writable (test by creating a dummy file)
        test_file = figures_dir / "contract_test.tmp"
        try:
            test_file.write_text("test")
            assert test_file.exists(), "Failed to create test file in figures directory"
            test_file.unlink()
        except (OSError, PermissionError) as e:
            pytest.fail(f"Figures directory is not writable: {e}")

    def test_reports_directory_exists_and_is_writable(self):
        """Verify the reports directory exists and is writable."""
        # Run setup to ensure directories are created
        result = setup_output_directories()
        
        reports_dir = result["reports"]
        
        # Contract: Must be a directory
        assert reports_dir.is_dir(), f"Reports directory {reports_dir} does not exist or is not a directory"
        
        # Contract: Must be writable
        test_file = reports_dir / "contract_test.tmp"
        try:
            test_file.write_text("test")
            assert test_file.exists(), "Failed to create test file in reports directory"
            test_file.unlink()
        except (OSError, PermissionError) as e:
            pytest.fail(f"Reports directory is not writable: {e}")

    def test_directory_structure_matches_spec(self):
        """Verify the directory structure matches the spec: output/figures, output/reports."""
        result = setup_output_directories()
        
        # Check keys
        assert set(result.keys()) == {"figures", "reports"}, "Unexpected keys in result"
        
        # Check relative paths from project root (assuming result paths are absolute)
        # We can't easily determine the project root from here without assuming structure,
        # but we can check that the paths end with the expected names.
        assert result["figures"].name == "figures"
        assert result["reports"].name == "reports"
        
        # Check parent is 'output'
        assert result["figures"].parent.name == "output"
        assert result["reports"].parent.name == "output"