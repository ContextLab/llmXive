import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the module under test
# Assuming the package structure is code.data.validate
from code.data.validate import (
    check_variable_presence,
    validate_data_content,
    define_generic_roi_grid,
    apply_roi_fallback,
    validate_dataset,
    write_validation_report,
    main
)
from code.config import get_config

class TestCheckVariablePresence:
    def test_hf_dataset_all_present(self):
        mock_ds = Mock()
        mock_ds.column_names = ["gaze_coordinates", "response_times", "emotion_labels", "roi_annotations"]
        present, missing = check_variable_presence(mock_ds, ["gaze_coordinates", "response_times"])
        assert present is True
        assert missing == []

    def test_hf_dataset_missing_one(self):
        mock_ds = Mock()
        mock_ds.column_names = ["gaze_coordinates", "response_times"]
        present, missing = check_variable_presence(mock_ds, ["gaze_coordinates", "emotion_labels"])
        assert present is False
        assert missing == ["emotion_labels"]

    def test_dict_data_all_present(self):
        data = {"gaze_coordinates": [], "response_times": [], "emotion_labels": []}
        present, missing = check_variable_presence(data, ["gaze_coordinates", "response_times"])
        assert present is True
        assert missing == []

    def test_dict_data_missing_multiple(self):
        data = {"gaze_coordinates": []}
        present, missing = check_variable_presence(data, ["gaze_coordinates", "response_times", "emotion_labels"])
        assert present is False
        assert missing == ["response_times", "emotion_labels"]

class TestValidateDataContent:
    def test_empty_dataset(self):
        mock_ds = Mock()
        mock_ds.__len__ = Mock(return_value=0)
        mock_ds.column_names = ["col1"]
        result = validate_data_content(mock_ds)
        assert result["is_valid"] is False
        assert "empty" in result["issues"][0].lower()

    def test_valid_dataset(self):
        mock_ds = Mock()
        mock_ds.__len__ = Mock(return_value=100)
        mock_ds.column_names = ["col1", "col2"]
        result = validate_data_content(mock_ds)
        assert result["is_valid"] is True
        assert result["row_count"] == 100

class TestDefineGenericRoiGrid:
    def test_grid_dimensions(self):
        grid = define_generic_roi_grid(100, 100)
        assert len(grid) == 9
        assert "top_left" in grid
        assert "bottom_right" in grid

class TestApplyRoiFallback:
    def test_apply_fallback_to_dict(self):
        data = {"gaze": []}
        result = apply_roi_fallback(data)
        assert "roi_annotations" in result
        assert len(result["roi_annotations"]) == 9

class TestValidateDataset:
    @patch('code.data.validate.get_logger_wrapper')
    def test_validate_missing_critical(self, mock_logger):
        mock_logger.return_value = Mock()
        mock_ds = Mock()
        mock_ds.column_names = ["gaze_coordinates"] # Missing response_times, emotion_labels
        
        report = validate_dataset(mock_ds)
        
        assert report["status"] == "failed"
        assert "response_times" in report["missing_critical_vars"]
        assert "emotion_labels" in report["missing_critical_vars"]

    @patch('code.data.validate.get_logger_wrapper')
    def test_validate_passed(self, mock_logger):
        mock_logger.return_value = Mock()
        mock_ds = Mock()
        mock_ds.column_names = ["gaze_coordinates", "response_times", "emotion_labels"]
        
        report = validate_dataset(mock_ds)
        
        assert report["status"] == "passed"
        assert report["missing_critical_vars"] == []

class TestWriteValidationReport:
    def test_write_report_json(self, tmp_path):
        report = {"status": "passed", "data": [1, 2, 3]}
        output_file = tmp_path / "test_report.json"
        write_validation_report(report, output_file)
        
        assert output_file.exists()
        with open(output_file) as f:
            loaded = json.load(f)
        assert loaded["status"] == "passed"

class TestMain:
    @patch('code.data.validate.load_from_disk')
    @patch('code.data.validate.get_config')
    @patch('code.data.validate.validate_dataset')
    @patch('code.data.validate.write_validation_report')
    @patch('code.data.validate.Path')
    def test_main_success(self, mock_path, mock_write, mock_validate, mock_config, mock_load):
        # Setup mocks
        mock_config.return_value = {
            "data_raw_path": "/fake/path",
            "validation_report_path": "/fake/report.json"
        }
        
        mock_ds = Mock()
        mock_ds.column_names = ["gaze_coordinates", "response_times", "emotion_labels"]
        mock_load.return_value = mock_ds
        
        mock_report = {"status": "passed"}
        mock_validate.return_value = mock_report
        
        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.mkdir = Mock()
        mock_path.return_value = mock_path_instance
        
        # Mock Path iterdir logic for raw_dir check
        with patch('code.data.validate.Path.iterdir', return_value=[Mock(is_dir=lambda: True)]):
            result = main()
            
        assert result == 0
        mock_validate.assert_called_once()
        mock_write.assert_called_once()

    @patch('code.data.validate.load_from_disk')
    @patch('code.data.validate.get_config')
    @patch('code.data.validate.validate_dataset')
    @patch('code.data.validate.write_validation_report')
    @patch('code.data.validate.Path')
    def test_main_failure_missing_vars(self, mock_path, mock_write, mock_validate, mock_config, mock_load):
        mock_config.return_value = {
            "data_raw_path": "/fake/path",
            "validation_report_path": "/fake/report.json"
        }
        
        mock_ds = Mock()
        mock_ds.column_names = ["gaze_coordinates"]
        mock_load.return_value = mock_ds
        
        mock_report = {"status": "failed", "missing_critical_vars": ["response_times"]}
        mock_validate.return_value = mock_report
        
        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.mkdir = Mock()
        mock_path.return_value = mock_path_instance
        
        with patch('code.data.validate.Path.iterdir', return_value=[Mock(is_dir=lambda: True)]):
            result = main()
            
        assert result == 1
        mock_validate.assert_called_once()
        mock_write.assert_called_once()
