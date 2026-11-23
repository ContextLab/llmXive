"""
Unit tests for research file verification.
"""
import os
import tempfile
from pathlib import Path
import pytest

from code.verify_research import verify_research_file, ResearchVerificationError


class TestResearchVerification:
    """Tests for the verify_research_file function."""

    def test_file_exists_and_readable(self):
        """Test that verify_research_file returns True for a valid file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write("# Test Research Document\n\nThis is a test.")
            temp_path = f.name

        try:
            result = verify_research_file(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_file_not_found_raises_error(self):
        """Test that verify_research_file raises error for non-existent file."""
        non_existent_path = "/tmp/this_file_does_not_exist_research.md"
        
        with pytest.raises(ResearchVerificationError) as exc_info:
            verify_research_file(non_existent_path)
        
        assert "not found" in str(exc_info.value).lower()

    def test_file_empty_raises_error(self):
        """Test that verify_research_file raises error for empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            # Write nothing, file is empty
            temp_path = f.name

        try:
            with pytest.raises(ResearchVerificationError) as exc_info:
                verify_research_file(temp_path)
            
            assert "empty" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_default_path_check(self):
        """Test that the function can check the default project path."""
        # This test will fail if the default research file doesn't exist,
        # which is expected behavior - it verifies the file is required.
        project_root = Path(__file__).parent.parent
        default_path = project_root / "specs" / "PROJ-308-001-quantifying-entanglement" / "research.md"
        
        if default_path.exists():
            result = verify_research_file()
            assert result is True
        else:
            # If the file doesn't exist, the function should raise an error
            with pytest.raises(ResearchVerificationError):
                verify_research_file()

    def test_file_readability_check(self):
        """Test that verify_research_file checks file readability."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write("# Test Research Document")
            temp_path = f.name

        try:
            # Make file unreadable
            os.chmod(temp_path, 0o000)
            
            with pytest.raises(ResearchVerificationError) as exc_info:
                verify_research_file(temp_path)
            
            assert "not readable" in str(exc_info.value).lower()
        finally:
            # Restore permissions so we can delete the file
            os.chmod(temp_path, 0o644)
            os.unlink(temp_path)
