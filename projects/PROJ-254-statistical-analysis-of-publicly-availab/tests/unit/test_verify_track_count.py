import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from code.ingest import verify_track_count_file

class TestVerifyTrackCountFile:
    """
    Unit tests for verify_track_count_file function.
    """

    def setup_method(self):
        """
        Setup test fixtures.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "track_count.txt")

    def teardown_method(self):
        """
        Cleanup test fixtures.
        """
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_not_found(self):
        """
        Test that FileNotFoundError is raised when file does not exist.
        """
        non_existent_path = os.path.join(self.temp_dir, "non_existent.txt")
        with pytest.raises(FileNotFoundError) as exc_info:
            verify_track_count_file(non_existent_path)
        assert "not found" in str(exc_info.value).lower()

    def test_valid_integer_content(self):
        """
        Test that a valid integer is returned when file contains a valid integer.
        """
        valid_count = 12345
        with open(self.test_file_path, "w") as f:
            f.write(str(valid_count))
        
        result = verify_track_count_file(self.test_file_path)
        assert result == valid_count

    def test_invalid_content_raises_value_error(self):
        """
        Test that ValueError is raised when file content is not a valid integer.
        """
        invalid_content = "not_a_number"
        with open(self.test_file_path, "w") as f:
            f.write(invalid_content)
        
        with pytest.raises(ValueError) as exc_info:
            verify_track_count_file(self.test_file_path)
        assert "invalid" in str(exc_info.value).lower() or "invalid literal" in str(exc_info.value).lower()

    def test_empty_file_raises_value_error(self):
        """
        Test that ValueError is raised when file is empty.
        """
        with open(self.test_file_path, "w") as f:
            f.write("")
        
        with pytest.raises(ValueError) as exc_info:
            verify_track_count_file(self.test_file_path)
        assert "invalid" in str(exc_info.value).lower()

    def test_whitespace_content_raises_value_error(self):
        """
        Test that ValueError is raised when file contains only whitespace.
        """
        with open(self.test_file_path, "w") as f:
            f.write("   \n\t  ")
        
        with pytest.raises(ValueError) as exc_info:
            verify_track_count_file(self.test_file_path)
        assert "invalid" in str(exc_info.value).lower()

    def test_large_integer(self):
        """
        Test that a large integer is handled correctly.
        """
        large_count = 10**9
        with open(self.test_file_path, "w") as f:
            f.write(str(large_count))
        
        result = verify_track_count_file(self.test_file_path)
        assert result == large_count