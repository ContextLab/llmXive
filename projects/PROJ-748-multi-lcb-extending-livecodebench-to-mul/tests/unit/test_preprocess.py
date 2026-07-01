"""
Unit tests for the preprocessing and contamination filter module.
"""
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import (
    convert_test_case_to_unified_format,
    apply_release_date_cutoff,
    preprocess_dataset,
    setup_logging
)
from config import ProjectConfig

class TestConvertTestCase:
    def test_stdin_stdout_conversion(self):
        raw_tc = {
            "input": "1 2",
            "output": "3",
            "stdin": "",
            "stdout": ""
        }
        unified = convert_test_case_to_unified_format(raw_tc, "python")
        assert unified["stdin"] == "1 2"
        assert unified["stdout"] == "3"
        assert unified["input"] == "1 2"
        assert unified["output"] == "3"

    def test_already_unified(self):
        raw_tc = {
            "input": "1 2",
            "output": "3",
            "stdin": "1 2",
            "stdout": "3",
            "function_call": "add(1, 2)"
        }
        unified = convert_test_case_to_unified_format(raw_tc, "python")
        assert unified["stdin"] == "1 2"
        assert unified["stdout"] == "3"
        assert unified["function_call"] == "add(1, 2)"

class TestApplyReleaseDateCutoff:
    def test_filtering_logic(self):
        tasks = [
            {"task_id": "1", "release_date": "2022-01-01"},
            {"task_id": "2", "release_date": "2023-06-01"},
            {"task_id": "3", "release_date": "2024-01-01"},
        ]
        cutoff = "2023-01-01"
        
        # Mock logger
        logger = MagicMock()
        
        filtered, excluded, total = apply_release_date_cutoff(tasks, cutoff, logger)
        
        assert total == 3
        assert excluded == 2 # 2023-06-01 and 2024-01-01 are >= 2023-01-01
        assert len(filtered) == 1
        assert filtered[0]["task_id"] == "1"

    def test_missing_metadata_warning(self):
        tasks = [
            {"task_id": "1", "release_date": "2022-01-01"},
            {"task_id": "2"}, # Missing release_date
        ]
        cutoff = "2023-01-01"
        logger = MagicMock()
        
        filtered, excluded, total = apply_release_date_cutoff(tasks, cutoff, logger)
        
        assert len(filtered) == 2 # Missing date included by default
        assert excluded == 0
        logger.warning.assert_called_with("Missing release_date for task 2. Including by default.")

class TestPreprocessDatasetIntegration:
    @pytest.fixture
    def temp_data_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir)
            # Create mock config
            with patch('data.preprocess.get_data_path', return_value=data_path):
                with patch('data.preprocess.get_logs_path', return_value=data_path / "logs"):
                    with patch('data.preprocess.get_config', return_value={"contamination_cutoff_date": "2023-01-01"}):
                        yield data_path

    def test_full_pipeline(self, temp_data_dir):
        # Create mock raw dataset
        raw_data = {
            "tasks": [
                {"task_id": "t1", "language": "python", "release_date": "2022-01-01", "test_cases": [{"input": "1", "output": "1"}]},
                {"task_id": "t2", "language": "cpp", "release_date": "2023-06-01", "test_cases": [{"input": "2", "output": "2"}]},
            ]
        }
        raw_path = temp_data_dir / "raw_dataset.json"
        with open(raw_path, 'w') as f:
            json.dump(raw_data, f)

        # Run preprocessing
        from data.preprocess import preprocess_dataset
        import logging
        
        logger = logging.getLogger("test")
        logger.setLevel(logging.INFO)
        
        results = preprocess_dataset(logger)
        
        assert results["total_tasks"] == 2
        assert results["filtered_tasks"] == 1
        assert results["excluded_tasks"] == 1
        
        # Check output file
        output_path = temp_data_dir / "preprocessed_dataset.json"
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            out_data = json.load(f)
        
        assert len(out_data["tasks"]) == 1
        assert out_data["tasks"][0]["task_id"] == "t1"
        assert out_data["tasks"][0]["test_cases"][0]["stdin"] == "1"