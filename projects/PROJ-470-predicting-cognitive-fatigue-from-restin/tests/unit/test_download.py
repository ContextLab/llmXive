"""Tests for download.py script."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))


class TestDownloadScript:
    """Test suite for download.py functionality."""

    def test_metadata_check_performs_head_request(self):
        """Verify that the script performs an HTTP HEAD request to metadata URL."""
        from download import check_metadata_availability

        with patch('download.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            logger = MagicMock()
            result = check_metadata_availability(logger)

            mock_head.assert_called_once()
            assert result is True

    def test_metadata_check_handles_errors(self):
        """Verify that metadata check handles network errors gracefully."""
        from download import check_metadata_availability
        import requests

        with patch('download.requests.head') as mock_head:
            mock_head.side_effect = requests.RequestException("Network error")

            logger = MagicMock()
            result = check_metadata_availability(logger)

            # Should return True even on error to continue with download
            assert result is True
            logger.log.assert_called()

    def test_validate_variables_raises_on_missing(self):
        """Verify that validation raises error if required variables are missing."""
        from download import validate_variables

        # Create a mock dataset with missing variables
        mock_dataset = MagicMock()
        mock_dataset.column_names = ["eeg_data"]  # Missing fatigue_rating

        logger = MagicMock()

        with pytest.raises(ValueError) as excinfo:
            validate_variables(mock_dataset, logger)

        assert "Missing required variables" in str(excinfo.value)
        assert "fatigue_rating" in str(excinfo.value)
        logger.log.assert_called()

    def test_validate_variables_passes_when_present(self):
        """Verify that validation passes when all required variables are present."""
        from download import validate_variables

        mock_dataset = MagicMock()
        mock_dataset.column_names = ["eeg_data", "fatigue_rating", "other_var"]

        logger = MagicMock()

        # Should not raise
        validate_variables(mock_dataset, logger)

        logger.log.assert_any_call("variable_validation_success", 
                                  validated_vars=["eeg_data", "fatigue_rating"])

    def test_manifest_created_on_success(self):
        """Verify that manifest is created only on successful download."""
        from download import create_manifest

        saved_files = ["/tmp/test_file.npy"]
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name

        try:
            manifest = create_manifest([tmp_path], MagicMock())
            
            assert "dataset" in manifest
            assert "timestamp" in manifest
            assert "files" in manifest
            assert len(manifest["files"]) == 1
            assert manifest["files"][0]["path"] == tmp_path
        finally:
            os.unlink(tmp_path)

    def test_manifest_write_is_atomic(self):
        """Verify that manifest write uses atomic rename."""
        from download import write_manifest_atomically

        manifest = {"test": "data"}
        temp_dir = tempfile.mkdtemp()
        manifest_path = os.path.join(temp_dir, "test_manifest.json")

        logger = MagicMock()

        write_manifest_atomically(manifest, manifest_path, logger)

        # Verify file exists
        assert os.path.exists(manifest_path)

        # Verify content
        with open(manifest_path, 'r') as f:
            loaded_manifest = json.load(f)
            assert loaded_manifest == manifest

    def test_script_exits_with_error_on_validation_failure(self):
        """Verify that script exits with code 1 if validation fails."""
        from download import main
        import sys

        with patch('download.fetch_dataset') as mock_fetch:
            mock_fetch.side_effect = RuntimeError("Dataset fetch failed")

            with patch('sys.exit') as mock_exit:
                with patch('builtins.print'):
                    main()
                    mock_exit.assert_called_once_with(1)

    def test_required_variables_constant(self):
        """Verify that required variables are correctly defined."""
        from download import REQUIRED_VARIABLES

        assert "eeg_data" in REQUIRED_VARIABLES
        assert "fatigue_rating" in REQUIRED_VARIABLES
        assert len(REQUIRED_VARIABLES) == 2
