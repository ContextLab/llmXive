"""
tests/test_research.py

Unit tests for Task T013: Verify Research File.
"""

import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
# Assuming tests are in tests/ and code is in code/ relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from verify_research import verify_research_file, RESEARCH_FILE_PATH


class TestVerifyResearchFile:
    """Tests for the verify_research_file function."""

    def test_file_exists_and_readable(self, mocker):
        """
        Test that the function returns True when the file exists and is readable.
        """
        # Mock the path to point to a temporary file that exists
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as tmp:
            tmp.write("# Test Research\n")
            tmp_path = tmp.name

        try:
            # We need to temporarily patch the global path variable
            # Since the function uses a global constant, we patch it in the module
            import verify_research
            original_path = verify_research.RESEARCH_FILE_PATH
            verify_research.RESEARCH_FILE_PATH = Path(tmp_path)

            # Also mock os.access to ensure it returns True
            mocker.patch('verify_research.os.access', return_value=True)
            mocker.patch('os.access', return_value=True)

            result = verify_research.verify_research_file()
            assert result is True
        finally:
            # Restore original path
            verify_research.RESEARCH_FILE_PATH = original_path
            # Clean up temp file
            os.unlink(tmp_path)

    def test_file_missing_raises_file_not_found(self, mocker):
        """
        Test that FileNotFoundError is raised if the file does not exist.
        """
        import verify_research
        fake_path = PROJECT_ROOT / "specs" / "PROJ-308-001-quantifying-entanglement" / "non_existent_file.md"
        
        original_path = verify_research.RESEARCH_FILE_PATH
        verify_research.RESEARCH_FILE_PATH = fake_path

        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                verify_research.verify_research_file()
            
            assert "CRITICAL: Research file not found" in str(exc_info.value)
        finally:
            verify_research.RESEARCH_FILE_PATH = original_path

    def test_file_not_readable_raises_permission_error(self, mocker):
        """
        Test that PermissionError is raised if the file is not readable.
        """
        import verify_research
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as tmp:
            tmp.write("# Test\n")
            tmp_path = tmp.name

        try:
            # Make file unreadable (if running as non-root)
            os.chmod(tmp_path, 0o000)
            
            original_path = verify_research.RESEARCH_FILE_PATH
            verify_research.RESEARCH_FILE_PATH = Path(tmp_path)
            
            # Mock os.access to return False to simulate permission denied
            mocker.patch('verify_research.os.access', return_value=False)

            with pytest.raises(PermissionError) as exc_info:
                verify_research.verify_research_file()
            
            assert "CRITICAL: Research file exists" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(tmp_path, 0o644)
            except:
                pass
            os.unlink(tmp_path)
            verify_research.RESEARCH_FILE_PATH = original_path

    def test_empty_file_raises_value_error(self, mocker):
        """
        Test that ValueError is raised if the file is empty.
        """
        import verify_research
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as tmp:
            # Write nothing
            pass
        tmp_path = tmp.name

        try:
            original_path = verify_research.RESEARCH_FILE_PATH
            verify_research.RESEARCH_FILE_PATH = Path(tmp_path)
            
            # Mock os.access to return True
            mocker.patch('verify_research.os.access', return_value=True)

            with pytest.raises(ValueError) as exc_info:
                verify_research.verify_research_file()
            
            assert "CRITICAL: Research file" in str(exc_info.value) and "empty" in str(exc_info.value).lower()
        finally:
            os.unlink(tmp_path)
            verify_research.RESEARCH_FILE_PATH = original_path
