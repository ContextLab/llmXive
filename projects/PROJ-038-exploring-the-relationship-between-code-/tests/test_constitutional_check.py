"""
Tests for the Constitutional Check module.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from src.constitutional_check import ConstitutionalBlockError, verify_amendment_artifact, main


class TestConstitutionalCheck:
    """Test suite for constitutional amendment verification."""

    def test_amendment_exists(self):
        """Test that verification passes when marker file exists and has content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            marker_path = Path(tmpdir) / "amendment_ratified.md"
            marker_path.write_text("Amendment ratified by human on 2023-10-27.")

            result = verify_amendment_artifact(marker_path)
            assert result is True

    def test_amendment_missing_raises_error(self):
        """Test that verification raises error when marker file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            marker_path = Path(tmpdir) / "nonexistent.md"

            with pytest.raises(ConstitutionalBlockError) as excinfo:
                verify_amendment_artifact(marker_path)

            assert "does not exist" in str(excinfo.value)

    def test_amendment_empty_raises_error(self):
        """Test that verification raises error when marker file is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            marker_path = Path(tmpdir) / "amendment_ratified.md"
            marker_path.write_text("")  # Empty file

            with pytest.raises(ConstitutionalBlockError) as excinfo:
                verify_amendment_artifact(marker_path)

            assert "is empty" in str(excinfo.value)

    @patch('src.constitutional_check.verify_amendment_artifact')
    @patch('src.constitutional_check.Path')
    def test_main_returns_zero_on_success(self, mock_path_class, mock_verify):
        """Test that main returns 0 when verification succeeds."""
        mock_path_instance = mock_path_class.return_value
        mock_path_instance.exists.return_value = True
        mock_verify.return_value = True

        # Mock Path.cwd() as well
        with patch('src.constitutional_check.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path("/fake/path")
            mock_cwd.return_value.__truediv__.return_value.exists.return_value = False

            result = main()
            assert result == 0
            mock_verify.assert_called_once()

    @patch('src.constitutional_check.verify_amendment_artifact')
    @patch('src.constitutional_check.Path')
    def test_main_returns_one_on_failure(self, mock_path_class, mock_verify):
        """Test that main returns 1 when verification fails."""
        mock_verify.side_effect = ConstitutionalBlockError("Test error")

        # Mock Path.cwd() as well
        with patch('src.constitutional_check.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path("/fake/path")
            mock_cwd.return_value.__truediv__.return_value.exists.return_value = False

            result = main()
            assert result == 1
            mock_verify.assert_called_once()