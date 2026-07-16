"""
Unit tests for code/download.py

Tests verify:
1. The download script logs the raw record count.
2. The download script does NOT halt on data insufficiency (delegates to T011).
3. No synthetic fallback is used when real data sources fail.
"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.download import fetch_materials_project_data, fetch_openkim_data, save_raw_data, main
from code.utils import setup_logging


class TestDownloadLogging:
    """Tests for logging behavior in download.py"""

    def test_logs_raw_record_count(self, caplog):
        """Verify that the download script logs the raw count"""
        with caplog.at_level(logging.INFO):
            # Mock the API response to simulate a successful fetch
            mock_response = {
                "data": [
                    {"material_id": "mp-123", "structure": "fake_structure"},
                    {"material_id": "mp-124", "structure": "fake_structure"}
                ],
                "total": 2
            }

            with patch('code.download.requests.get') as mock_get:
                mock_get.return_value = MagicMock(
                    status_code=200,
                    json=lambda: mock_response
                )

                # Set up a temporary directory for raw data
                with tempfile.TemporaryDirectory() as tmpdir:
                    result = fetch_materials_project_data(
                        keywords=["grain boundary"],
                        properties=["diffusivity"],
                        output_dir=Path(tmpdir),
                        api_key="fake_key"
                    )

            # Verify the log message contains the count
            assert any("Raw records retrieved" in record.message for record in caplog.records)
            assert "2" in caplog.text  # Check that the count 2 appears in logs

    def test_logs_raw_count_for_openkim(self, caplog):
        """Verify that OpenKIM fetch also logs raw count"""
        with caplog.at_level(logging.INFO):
            mock_response = {
                "results": [
                    {"id": "kim-1", "data": "fake"},
                    {"id": "kim-2", "data": "fake"},
                    {"id": "kim-3", "data": "fake"}
                ]
            }

            with patch('code.download.requests.get') as mock_get:
                mock_get.return_value = MagicMock(
                    status_code=200,
                    json=lambda: mock_response
                )

                with tempfile.TemporaryDirectory() as tmpdir:
                    fetch_openkim_data(
                        keywords=["grain boundary"],
                        output_dir=Path(tmpdir),
                        api_key="fake_key"
                    )

            assert any("Raw records retrieved" in record.message for record in caplog.records)
            assert "3" in caplog.text


class TestDataInsufficiencyHandling:
    """Tests verifying that download.py does NOT halt on insufficiency"""

    def test_does_not_exit_on_low_count(self, caplog):
        """Verify download continues even if count < 500"""
        with caplog.at_level(logging.WARNING):
            mock_response = {
                "data": [{"material_id": "mp-1", "structure": "fake"}],
                "total": 1  # Far below 500
            }

            with patch('code.download.requests.get') as mock_get:
                mock_get.return_value = MagicMock(
                    status_code=200,
                    json=lambda: mock_response
                )

                with tempfile.TemporaryDirectory() as tmpdir:
                    # This should NOT raise SystemExit or DataInsufficiencyError
                    result = fetch_materials_project_data(
                        keywords=["grain boundary"],
                        properties=["diffusivity"],
                        output_dir=Path(tmpdir),
                        api_key="fake_key"
                    )

            # Verify the script logged the low count but did not halt
            assert any("Raw records retrieved: 1" in record.message for record in caplog.records)
            # Ensure no exit or error was raised
            assert not any("Data Insufficiency" in record.message for record in caplog.records)

    def test_no_exit_on_api_failure(self):
        """Verify that API failures don't cause silent exits"""
        with patch('code.download.requests.get') as mock_get:
            mock_get.side_effect = Exception("API Connection Failed")

            with tempfile.TemporaryDirectory() as tmpdir:
                # Should raise an exception, not exit silently or return fake data
                with pytest.raises(Exception, match="API Connection Failed"):
                    fetch_materials_project_data(
                        keywords=["grain boundary"],
                        properties=["diffusivity"],
                        output_dir=Path(tmpdir),
                        api_key="fake_key"
                    )


class TestNoSyntheticFallback:
    """Tests verifying that no synthetic/fake data is generated"""

    def test_no_synthetic_data_on_failure(self):
        """Verify that failed fetches do NOT generate synthetic data"""
        with patch('code.download.requests.get') as mock_get:
            mock_get.side_effect = Exception("API Down")

            with tempfile.TemporaryDirectory() as tmpdir:
                # We expect an exception, not a return of synthetic data
                with pytest.raises(Exception):
                    fetch_materials_project_data(
                        keywords=["grain boundary"],
                        properties=["diffusivity"],
                        output_dir=Path(tmpdir),
                        api_key="fake_key"
                    )

                # Verify no files were created (which would indicate synthetic fallback)
                raw_files = list(Path(tmpdir).glob("*.json"))
                assert len(raw_files) == 0

    def test_no_mock_data_in_results(self):
        """Verify that valid fetches don't contain mock markers"""
        mock_response = {
            "data": [{"material_id": "mp-real", "structure": "real_data"}],
            "total": 1
        }

        with patch('code.download.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )

            with tempfile.TemporaryDirectory() as tmpdir:
                result = fetch_materials_project_data(
                    keywords=["grain boundary"],
                    properties=["diffusivity"],
                    output_dir=Path(tmpdir),
                    api_key="fake_key"
                )

                # Load the saved file and verify it contains real data structure
                saved_files = list(Path(tmpdir).glob("*.json"))
                assert len(saved_files) > 0

                with open(saved_files[0], 'r') as f:
                    saved_data = json.load(f)

                # Verify no synthetic markers
                assert "synthetic" not in str(saved_data).lower()
                assert "mock" not in str(saved_data).lower()
                assert "fake" not in str(saved_data).lower()


class TestMainFunction:
    """Tests for the main() entry point"""

    def test_main_logs_count_and_exits_cleanly(self, caplog):
        """Verify main() logs count and exits with 0 on success"""
        mock_response = {
            "data": [{"material_id": "mp-1", "structure": "fake"}],
            "total": 1
        }

        with patch('code.download.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )

            with tempfile.TemporaryDirectory() as tmpdir:
                # Mock sys.argv to simulate running the script
                original_argv = sys.argv
                sys.argv = ['download.py', '--output', tmpdir]

                try:
                    # This should complete without raising SystemExit
                    # (main() typically calls sys.exit(0) explicitly on success)
                    with patch('sys.exit') as mock_exit:
                        main()
                        mock_exit.assert_called_with(0)
                finally:
                    sys.argv = original_argv

        # Verify logging occurred
        assert any("Raw records retrieved" in record.message for record in caplog.records)