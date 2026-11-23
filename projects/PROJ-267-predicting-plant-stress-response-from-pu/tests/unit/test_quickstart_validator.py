"""
Unit tests for T034: Quickstart Validator.
Tests the logic of the validator without running the full pipeline.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from quickstart_validator import check_file_exists, check_directory_exists, validate_pipeline_outputs, main

class TestQuickstartValidator:
    """Tests for the quickstart validation logic."""

    def setup_method(self):
        """Create a temporary directory structure for testing."""
        self.tmp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.tmp_dir)
        
        # Create standard directory structure
        (self.project_root / "code").mkdir()
        (self.project_root / "tests").mkdir()
        (self.project_root / "logs").mkdir()
        (self.project_root / "results").mkdir()
        (self.project_root / "docs").mkdir()
        (self.project_root / "data").mkdir()
        (self.project_root / "data" / "raw").mkdir()
        (self.project_root / "data" / "processed").mkdir()
        (self.project_root / "results" / "figures").mkdir()

        # Patch config functions to use our temp dir
        self.config_patch = patch('quickstart_validator.get_project_root', return_value=self.project_root)
        self.data_path_patch = patch('quickstart_validator.get_data_path', return_value=self.project_root / "data")
        self.results_path_patch = patch('quickstart_validator.get_results_path', return_value=self.project_root / "results")
        self.log_path_patch = patch('quickstart_validator.get_log_path', return_value=self.project_root / "logs")
        
        self.config_patch.start()
        self.data_path_patch.start()
        self.results_path_patch.start()
        self.log_path_patch.start()

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.tmp_dir)
        self.config_patch.stop()
        self.data_path_patch.stop()
        self.results_path_patch.stop()
        self.log_path_patch.stop()

    def test_check_file_exists_found(self):
        """Test check_file_exists with an existing file."""
        test_file = self.project_root / "code" / "test.txt"
        test_file.write_text("content")
        assert check_file_exists(test_file, "Test File") is True

    def test_check_file_exists_missing(self):
        """Test check_file_exists with a missing file."""
        test_file = self.project_root / "code" / "missing.txt"
        assert check_file_exists(test_file, "Missing File") is False

    def test_check_file_exists_empty(self):
        """Test check_file_exists with an empty file."""
        test_file = self.project_root / "code" / "empty.txt"
        test_file.touch()
        assert check_file_exists(test_file, "Empty File") is False

    def test_check_directory_exists_found(self):
        """Test check_directory_exists with an existing directory."""
        assert check_directory_exists(self.project_root / "code", "Code Dir") is True

    def test_check_directory_exists_missing(self):
        """Test check_directory_exists with a missing directory."""
        assert check_directory_exists(self.project_root / "nonexistent", "Nonexistent Dir") is False

    @patch('quickstart_validator.validate_dataset_integrity')
    @patch('quickstart_validator.check_sample_counts')
    @patch('quickstart_validator.load_csv')
    @patch('quickstart_validator.load_json')
    def test_validate_pipeline_outputs_success(
        self, mock_load_json, mock_load_csv, mock_check_sample, mock_validate_integrity
    ):
        """Test validate_pipeline_outputs with all files present."""
        # Setup mocks
        mock_df = MagicMock()
        mock_df.empty = False
        mock_load_csv.return_value = mock_df
        mock_validate_integrity.return_value = (True, [])
        mock_check_sample.return_value = {"drought": 10, "heat": 10}
        
        # Create required files
        (self.project_root / "data" / "processed" / "merged_matrix.csv").write_text("a,b\n1,2")
        (self.project_root / "results" / "cv_strategy.json").write_text("{}")
        (self.project_root / "results" / "hyperparameters.json").write_text("{}")
        (self.project_root / "results" / "within_stress_metrics.json").write_text("{}")
        (self.project_root / "results" / "cross_stress_metrics.json").write_text("{}")
        (self.project_root / "results" / "raw_feature_baseline.json").write_text("{}")
        (self.project_root / "results" / "shuffle_control.json").write_text("{}")
        (self.project_root / "results" / "r2_drop.json").write_text("{}")
        (self.project_root / "results" / "null_model_metrics.json").write_text("{}")
        (self.project_root / "results" / "feature_importance.json").write_text("{}")
        (self.project_root / "results" / "figures" / "scatter_predicted_vs_actual.png").write_text("fake_png")
        (self.project_root / "results" / "figures" / "cross_stress_heatmap.png").write_text("fake_png")
        (self.project_root / "results" / "figures" / "feature_importance.png").write_text("fake_png")
        (self.project_root / "results" / "runtime_metrics.json").write_text("{}")
        (self.project_root / "logs" / "pipeline.log").write_text("log")

        assert validate_pipeline_outputs() is True

    @patch('quickstart_validator.validate_dataset_integrity')
    @patch('quickstart_validator.check_sample_counts')
    @patch('quickstart_validator.load_csv')
    def test_validate_pipeline_outputs_missing_file(self, mock_load_csv, mock_check_sample, mock_validate_integrity):
        """Test validate_pipeline_outputs when a required file is missing."""
        # Setup mocks
        mock_df = MagicMock()
        mock_df.empty = False
        mock_load_csv.return_value = mock_df
        mock_validate_integrity.return_value = (True, [])
        mock_check_sample.return_value = {"drought": 10}

        # Create all files EXCEPT one
        (self.project_root / "data" / "processed" / "merged_matrix.csv").write_text("a,b\n1,2")
        (self.project_root / "results" / "cv_strategy.json").write_text("{}")
        # Missing hyperparameters.json
        (self.project_root / "results" / "within_stress_metrics.json").write_text("{}")
        (self.project_root / "results" / "cross_stress_metrics.json").write_text("{}")
        (self.project_root / "results" / "raw_feature_baseline.json").write_text("{}")
        (self.project_root / "results" / "shuffle_control.json").write_text("{}")
        (self.project_root / "results" / "r2_drop.json").write_text("{}")
        (self.project_root / "results" / "null_model_metrics.json").write_text("{}")
        (self.project_root / "results" / "feature_importance.json").write_text("{}")

        assert validate_pipeline_outputs() is False

    def test_main_success(self, caplog):
        """Test main function when validation passes."""
        # Setup minimal valid state
        (self.project_root / "data" / "processed" / "merged_matrix.csv").write_text("a,b\n1,2")
        (self.project_root / "results" / "cv_strategy.json").write_text("{}")
        (self.project_root / "results" / "hyperparameters.json").write_text("{}")
        (self.project_root / "results" / "within_stress_metrics.json").write_text("{}")
        (self.project_root / "results" / "cross_stress_metrics.json").write_text("{}")
        (self.project_root / "results" / "raw_feature_baseline.json").write_text("{}")
        (self.project_root / "results" / "shuffle_control.json").write_text("{}")
        (self.project_root / "results" / "r2_drop.json").write_text("{}")
        (self.project_root / "results" / "null_model_metrics.json").write_text("{}")
        (self.project_root / "results" / "feature_importance.json").write_text("{}")
        (self.project_root / "results" / "figures" / "scatter_predicted_vs_actual.png").write_text("x")
        (self.project_root / "results" / "figures" / "cross_stress_heatmap.png").write_text("x")
        (self.project_root / "results" / "figures" / "feature_importance.png").write_text("x")
        (self.project_root / "results" / "runtime_metrics.json").write_text("{}")
        (self.project_root / "logs" / "pipeline.log").write_text("x")

        with patch('quickstart_validator.validate_dataset_integrity', return_value=(True, [])), \
             patch('quickstart_validator.check_sample_counts', return_value={"d": 1}), \
             patch('quickstart_validator.load_csv', return_value=MagicMock(empty=False)):
            
            result = main()
            assert result == 0
            
            # Check report was written
            report_path = self.project_root / "results" / "quickstart_validation_report.json"
            assert report_path.exists()
            with open(report_path) as f:
                report = json.load(f)
                assert report["status"] == "PASSED"

    def test_main_failure(self, caplog):
        """Test main function when validation fails."""
        # Create incomplete state (missing merged matrix)
        # Just create a few files, not enough to pass
        (self.project_root / "results" / "cv_strategy.json").write_text("{}")
        
        result = main()
        assert result == 1