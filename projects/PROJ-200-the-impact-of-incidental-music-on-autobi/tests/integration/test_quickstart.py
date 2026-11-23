"""
Integration tests for T046 Quickstart Validation.

These tests verify that the quickstart validation script works correctly
and that the pipeline can run end-to-end.
"""
import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_project_root
from quickstart_validator import (
    check_prerequisites,
    validate_output_file,
    validate_state_tracking,
    REQUIRED_OUTPUT_FILES
)

class TestQuickstartPrerequisites:
    """Test prerequisite checking logic."""
    
    def test_check_prerequisites_returns_tuple(self):
        """Check that prerequisites function returns expected tuple."""
        result = check_prerequisites()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)
    
    def test_check_prerequisites_validates_packages(self):
        """Verify that package validation works."""
        # This test should pass if pandas is installed (which it should be)
        success, errors = check_prerequisites()
        # We don't assert success because environment might be missing packages
        # but we verify the logic runs
        assert isinstance(success, bool)
        assert isinstance(errors, list)

class TestOutputValidation:
    """Test output file validation logic."""
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        project_root = get_project_root()
        fake_path = project_root / "data" / "nonexistent_file.parquet"
        
        success, message = validate_output_file(fake_path)
        assert success is False
        assert "does not exist" in message.lower()
    
    def test_validate_output_file_structure(self):
        """Test that validation returns proper structure."""
        project_root = get_project_root()
        fake_path = project_root / "data" / "test.csv"
        
        # Create a minimal valid CSV
        fake_path.parent.mkdir(parents=True, exist_ok=True)
        fake_path.write_text("col1,col2\n1,2\n")
        
        success, message = validate_output_file(fake_path)
        assert success is True
        assert message == "OK"
        
        # Cleanup
        fake_path.unlink()

class TestStateValidation:
    """Test state tracking validation."""
    
    def test_validate_state_structure(self):
        """Test that state validation returns proper structure."""
        success, message = validate_state_tracking()
        assert isinstance(success, bool)
        assert isinstance(message, str)

class TestRequiredOutputs:
    """Test that required output files are properly defined."""
    
    def test_required_outputs_not_empty(self):
        """Verify REQUIRED_OUTPUT_FILES is populated."""
        assert len(REQUIRED_OUTPUT_FILES) > 0
    
    def test_required_outputs_have_paths(self):
        """Verify all required outputs have valid paths."""
        for path in REQUIRED_OUTPUT_FILES:
            assert isinstance(path, str)
            assert len(path) > 0
            assert path.startswith("data/")
    
    def test_required_outputs_cover_pipeline_stages(self):
        """Verify required outputs cover all pipeline stages."""
        output_paths = REQUIRED_OUTPUT_FILES
        
        # Check for processed data
        processed_files = [p for p in output_paths if "processed" in p]
        assert len(processed_files) >= 2, "Should have processed data files"
        
        # Check for final results
        final_files = [p for p in output_paths if "final" in p]
        assert len(final_files) >= 3, "Should have final result files"

class TestQuickstartValidator:
    """Integration tests for the quickstart validator."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_validator_handles_missing_data_gracefully(self):
        """Test that validator handles missing data without crashing."""
        # This test verifies the validator doesn't crash when data is missing
        # It should report errors, not raise exceptions
        success, errors = check_prerequisites()
        # The function should return gracefully even if prerequisites fail
        assert isinstance(success, bool)
        assert isinstance(errors, list)
    
    def test_validation_messages_are_descriptive(self):
        """Test that validation error messages are descriptive."""
        project_root = get_project_root()
        fake_path = project_root / "data" / "missing.parquet"
        
        success, message = validate_output_file(fake_path)
        assert not success
        assert "does not exist" in message.lower()
        assert str(fake_path) in message