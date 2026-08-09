import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

# Import the function to test
from download import check_validation_and_halt

class TestDownloadValidationHalt:
    """
    Tests for T016c: Halt on Zero Valid Subjects.
    Verifies that check_validation_and_halt raises ValueError with the exact message
    when valid_subjects.json indicates 0 subjects, and logs to validation_errors.log.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup temporary directories for test isolation."""
        self.tmp_dir = tmp_path
        self.processed_dir = self.tmp_dir / "data" / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Patch the paths used by the function
        self.valid_subjects_path = self.processed_dir / "valid_subjects.json"
        self.error_log_path = self.processed_dir / "validation_errors.log"

        # We need to patch the global paths in the download module or pass them?
        # Since the function uses hardcoded paths in the module, we must patch Path() or os.path
        # The function uses: Path("data/processed/valid_subjects.json")
        # We will patch Path to return our tmp_path based paths for specific filenames
        
        self.original_path = Path
        
        def mock_path_constructor(path_str):
            p = self.original_path(path_str)
            if str(p) == "data/processed/valid_subjects.json":
                return self.valid_subjects_path
            if str(p) == "data/processed/validation_errors.log":
                return self.error_log_path
            return p

        self.patch_path = patch('download.Path', side_effect=mock_path_constructor)
        self.patch_path.start()
        
        yield

        self.patch_path.stop()

    def test_halt_on_zero_subjects_raises_error(self):
        """
        Verify that if valid_subjects.json has count 0, a ValueError is raised
        with the exact message: "No valid Fluid Intelligence data found in specified datasets"
        """
        # Arrange: Create valid_subjects.json with count 0
        data = {"subjects": [], "count": 0}
        with open(self.valid_subjects_path, 'w') as f:
            json.dump(data, f)

        # Act & Assert: Expect ValueError with specific message
        with pytest.raises(ValueError) as exc_info:
            check_validation_and_halt()

        assert str(exc_info.value) == "No valid Fluid Intelligence data found in specified datasets"

    def test_halt_on_zero_subjects_logs_error(self):
        """
        Verify that the error is logged to data/processed/validation_errors.log
        with the prefix [VALIDATION_ERROR].
        """
        # Arrange
        data = {"subjects": [], "count": 0}
        with open(self.valid_subjects_path, 'w') as f:
            json.dump(data, f)

        # Act
        try:
            check_validation_and_halt()
        except ValueError:
            pass # Expected

        # Assert
        assert self.error_log_path.exists(), "validation_errors.log was not created"
        
        with open(self.error_log_path, 'r') as f:
            log_content = f.read()
        
        assert "[VALIDATION_ERROR]" in log_content, "Log missing [VALIDATION_ERROR] prefix"
        assert "No valid Fluid Intelligence data found in specified datasets" in log_content

    def test_continues_on_valid_subjects(self):
        """
        Verify that if count > 0, no error is raised and function returns data.
        """
        # Arrange
        data = {"subjects": [{"id": "sub-01", "score": 1.5}], "count": 1}
        with open(self.valid_subjects_path, 'w') as f:
            json.dump(data, f)

        # Act
        result = check_validation_and_halt()

        # Assert
        assert result == data
        assert not self.error_log_path.exists() # Should not create log if success

    def test_halt_on_missing_file(self):
        """
        Verify that if valid_subjects.json does not exist, it is treated as 0 subjects
        and the halt logic triggers.
        """
        # Arrange: Ensure file does not exist
        if self.valid_subjects_path.exists():
            self.valid_subjects_path.unlink()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            check_validation_and_halt()

        assert str(exc_info.value) == "No valid Fluid Intelligence data found in specified datasets"
        assert self.error_log_path.exists()