import os
import tempfile
from pathlib import Path
from unittest.mock import patch

def test_setup_directories_creates_folders(tmp_path):
    """
    Test that setup_directories creates the required subdirectories.
    Uses a temporary path to avoid filesystem side effects.
    """
    # Mock the config paths to point to our temp directory
    temp_data = tmp_path / "data"
    temp_raw = temp_data / "raw"
    temp_processed = temp_data / "processed"
    temp_results = temp_data / "results"

    # Patch the config module values
    with patch('code.config.DATA_DIR', temp_data), \
         patch('code.config.RAW_DIR', temp_raw), \
         patch('code.config.PROCESSED_DIR', temp_processed), \
         patch('code.config.RESULTS_DIR', temp_results):
        
        from code.setup_data_dirs import setup_directories
        
        # Execute
        result = setup_directories()

        # Verify return
        assert result is True

        # Verify directories exist
        assert temp_data.exists()
        assert temp_raw.exists()
        assert temp_processed.exists()
        assert temp_results.exists()

        # Verify they are directories
        assert temp_raw.is_dir()
        assert temp_processed.is_dir()
        assert temp_results.is_dir()
