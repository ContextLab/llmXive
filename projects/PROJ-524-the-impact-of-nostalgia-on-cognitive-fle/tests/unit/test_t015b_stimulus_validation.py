"""
Unit tests for T015b: Stimulus Validation
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from task_t015b_stimulus_validation import load_metadata, validate_stimulus_doi, main

# Mock setup_logging to avoid side effects in tests
@pytest.fixture(autouse=True)
def mock_setup_logging():
    with patch("task_t015b_stimulus_validation.setup_logging"):
        yield

class TestValidateStimulusDoi:
    def test_doi_present_and_valid(self):
        metadata = {"validation_study_doi": "10.1038/example.doi"}
        assert validate_stimulus_doi(metadata) is True

    def test_doi_missing_key(self):
        metadata = {"dataset_source": "OpenML"}
        assert validate_stimulus_doi(metadata) is False

    def test_doi_is_null(self):
        metadata = {"validation_study_doi": None}
        assert validate_stimulus_doi(metadata) is False

    def test_doi_is_empty_string(self):
        metadata = {"validation_study_doi": ""}
        assert validate_stimulus_doi(metadata) is False

class TestLoadMetadata:
    def test_load_existing_metadata(self, tmp_path):
        # Create a temporary metadata file
        meta_file = tmp_path / "metadata.json"
        data = {"validation_study_doi": "10.123/test"}
        with open(meta_file, 'w') as f:
            json.dump(data, f)
        
        with patch("task_t015b_stimulus_validation.METADATA_PATH", meta_file):
            loaded = load_metadata()
            assert loaded == data

    def test_load_missing_metadata(self, tmp_path):
        non_existent = tmp_path / "non_existent.json"
        
        with patch("task_t015b_stimulus_validation.METADATA_PATH", non_existent):
            with pytest.raises(FileNotFoundError):
                load_metadata()

class TestMain:
    def test_main_valid_doi(self, tmp_path, caplog):
        # Setup temp directories
        data_raw = tmp_path / "data" / "raw"
        data_results = tmp_path / "data" / "results"
        data_raw.mkdir(parents=True)
        data_results.mkdir(parents=True)
        
        meta_file = data_raw / "metadata.json"
        with open(meta_file, 'w') as f:
            json.dump({"validation_study_doi": "10.1000/test"}, f)
        
        # Patch paths
        with patch("task_t015b_stimulus_validation.METADATA_PATH", meta_file), \
             patch("task_t015b_stimulus_validation.RESULTS_DIR", data_results):
            
            main()
            
            # Verify output file created
            status_file = data_results / "stimulus_validation_status.json"
            assert status_file.exists()
            
            with open(status_file) as f:
                report = json.load(f)
            
            assert report["stimulus_validated"] is True
            assert "INFO_STIMULUS_VALIDATED" in report["log_message"]

    def test_main_no_doi(self, tmp_path, caplog):
        # Setup temp directories
        data_raw = tmp_path / "data" / "raw"
        data_results = tmp_path / "data" / "results"
        data_raw.mkdir(parents=True)
        data_results.mkdir(parents=True)
        
        meta_file = data_raw / "metadata.json"
        with open(meta_file, 'w') as f:
            json.dump({"dataset_source": "Simulated"}, f)
        
        # Patch paths
        with patch("task_t015b_stimulus_validation.METADATA_PATH", meta_file), \
             patch("task_t015b_stimulus_validation.RESULTS_DIR", data_results):
            
            main()
            
            # Verify output file created
            status_file = data_results / "stimulus_validation_status.json"
            assert status_file.exists()
            
            with open(status_file) as f:
                report = json.load(f)
            
            assert report["stimulus_validated"] is False
            assert "WARN_STIMULUS_NO_VALIDATION" in report["log_message"]