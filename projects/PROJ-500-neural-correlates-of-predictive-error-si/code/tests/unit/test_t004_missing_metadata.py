import os
import sys
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Assuming the project root is the parent of 'code'
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.ingest import generate_validation_report, check_and_report_variables

class TestT004MissingMetadata:
    """
    Tests for T004: Log warning and skip datasets with missing metadata rather than crashing.
    """

    def test_skip_dataset_missing_both_variables(self, tmp_path):
        """
        Verify that a dataset missing both 'stimulus_type' and 'response_correctness'
        is skipped and logged as an error, without crashing the pipeline.
        """
        report_path = tmp_path / "validation_report.json"
        
        mock_datasets = [
            {
                "id": "ds_bad",
                "metadata": {}  # Missing both
            }
        ]

        # This should not raise an exception
        result = generate_validation_report(mock_datasets, str(report_path))

        assert result["analysis_mode"] is None or result["analysis_mode"] == "none"
        assert len(result["datasets_skipped"]) == 1
        assert result["datasets_skipped"][0]["id"] == "ds_bad"
        assert "Missing both" in result["datasets_skipped"][0]["reason"]
        
        # Verify file was written
        assert report_path.exists()
        with open(report_path) as f:
            saved_report = json.load(f)
            assert saved_report["analysis_mode"] is None

    def test_fallback_stimulus_driven_missing_response(self, tmp_path):
        """
        Verify that if only 'response_correctness' is missing, the system
        logs a warning, processes the dataset, and sets mode to 'stimulus_driven'.
        """
        report_path = tmp_path / "validation_report.json"
        
        mock_datasets = [
            {
                "id": "ds_partial",
                "metadata": {
                    "stimulus_type": "tactile"
                }
            }
        ]

        result = generate_validation_report(mock_datasets, str(report_path))

        assert result["analysis_mode"] == "stimulus_driven"
        assert len(result["datasets_processed"]) == 1
        assert len(result["warnings"]) == 1
        assert "missing response_correctness" in result["warnings"][0].lower()

    def test_error_signal_mode_present(self, tmp_path):
        """
        Verify that if 'response_correctness' is present, mode is 'error_signal'.
        """
        report_path = tmp_path / "validation_report.json"
        
        mock_datasets = [
            {
                "id": "ds_good",
                "metadata": {
                    "stimulus_type": "tactile",
                    "response_correctness": True
                }
            }
        ]

        result = generate_validation_report(mock_datasets, str(report_path))

        assert result["analysis_mode"] == "error_signal"
        assert len(result["datasets_processed"]) == 1
        assert len(result["datasets_skipped"]) == 0

    def test_mixed_datasets_handling(self, tmp_path):
        """
        Verify handling of a mix of valid, partial, and invalid datasets.
        """
        report_path = tmp_path / "validation_report.json"
        
        mock_datasets = [
            {
                "id": "ds_valid",
                "metadata": {"stimulus_type": "tactile", "response_correctness": True}
            },
            {
                "id": "ds_invalid",
                "metadata": {}
            },
            {
                "id": "ds_partial",
                "metadata": {"stimulus_type": "visual"}
            }
        ]

        result = generate_validation_report(mock_datasets, str(report_path))

        # Should be error_signal because ds_valid has response_correctness
        assert result["analysis_mode"] == "error_signal"
        
        # ds_valid and ds_partial should be processed (ds_partial triggers warning)
        assert len(result["datasets_processed"]) == 2
        # ds_invalid should be skipped
        assert len(result["datasets_skipped"]) == 1
        assert result["datasets_skipped"][0]["id"] == "ds_invalid"