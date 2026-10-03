import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging
import io

# We need to mock the config.get_paths to point to our temp directory
# so the src/data_warning module writes to the right place during tests.

@pytest.fixture
def temp_project_dirs():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        data_raw = root / "data" / "raw"
        logs = root / "logs"
        state = root / "state"
        
        data_raw.mkdir(parents=True)
        logs.mkdir(parents=True)
        state.mkdir(parents=True)
        
        yield {
            "root": root,
            "data_raw": data_raw,
            "logs": logs,
            "state": state
        }

@pytest.fixture
def mock_get_paths(temp_project_dirs):
    def _get_paths():
        return {
            "root": temp_project_dirs["root"],
            "data_raw": temp_project_dirs["data_raw"],
            "logs": temp_project_dirs["logs"],
            "state": temp_project_dirs["state"]
        }
    with patch('src.data_warning.get_paths', _get_paths):
        yield

class TestDataWarning:
    
    def test_insufficient_data_logs_warning(self, temp_project_dirs, mock_get_paths):
        """
        Test that if N < 10, a warning is logged to logs/warning.log
        with the specific message "Insufficient data (N<10). Regression blocked."
        """
        # Create 5 dummy files in data/raw
        for i in range(5):
            (temp_project_dirs["data_raw"] / f"file_{i}.txt").touch()
        
        # Write a fetch_count.log to simulate T005a output (optional but good practice)
        fetch_log = temp_project_dirs["logs"] / "fetch_count.log"
        fetch_log.write_text("5")

        # Import after mocking paths
        from src.data_warning import check_and_log_warning, main
        
        # Reset logger handlers to ensure clean state
        logger = logging.getLogger("data_warning")
        logger.handlers = []
        
        # Call the function
        result = check_and_log_warning(5)
        
        assert result is True, "Function should return True if warning logged"
        
        # Verify log file exists
        warning_log = temp_project_dirs["logs"] / "warning.log"
        assert warning_log.exists(), "logs/warning.log should exist"
        
        # Verify content
        content = warning_log.read_text()
        assert "Insufficient data (N<10). Regression blocked." in content, \
            f"Expected specific message in log, got: {content}"

    def test_sufficient_data_no_warning(self, temp_project_dirs, mock_get_paths):
        """
        Test that if N >= 10, no warning is logged.
        """
        # Create 10 dummy files
        for i in range(10):
            (temp_project_dirs["data_raw"] / f"file_{i}.txt").touch()
        
        from src.data_warning import check_and_log_warning
        
        logger = logging.getLogger("data_warning")
        logger.handlers = []
        
        result = check_and_log_warning(10)
        
        assert result is False, "Function should return False if no warning needed"
        
        warning_log = temp_project_dirs["logs"] / "warning.log"
        # Log file might not exist if nothing was ever written
        if warning_log.exists():
            content = warning_log.read_text()
            assert "Insufficient data" not in content, \
                "Warning message should not appear if data is sufficient"

    def test_empty_raw_directory_logs_warning(self, temp_project_dirs, mock_get_paths):
        """
        Test behavior when data/raw/ is empty (N=0).
        """
        from src.data_warning import check_and_log_warning
        
        logger = logging.getLogger("data_warning")
        logger.handlers = []
        
        result = check_and_log_warning(0)
        
        assert result is True
        
        warning_log = temp_project_dirs["logs"] / "warning.log"
        assert warning_log.exists()
        content = warning_log.read_text()
        assert "Insufficient data (N<10). Regression blocked." in content

    def test_main_writes_warning(self, temp_project_dirs, mock_get_paths):
        """
        Test the main() entry point which counts files and triggers logging.
        """
        # Create 3 files
        for i in range(3):
            (temp_project_dirs["data_raw"] / f"test_{i}.dat").touch()
        
        from src.data_warning import main
        
        logger = logging.getLogger("data_warning")
        logger.handlers = []
        
        # Capture stdout to ensure it runs without error
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            main()
        finally:
            sys.stdout = old_stdout
        
        warning_log = temp_project_dirs["logs"] / "warning.log"
        assert warning_log.exists(), "main() should create warning.log if N < 10"
        assert "Insufficient data (N<10). Regression blocked." in warning_log.read_text()