import os
import json
import pytest
import tempfile
import shutil
from datetime import datetime

# Add code directory to path for imports
import sys
sys.path.insert(0, 'code')

from initialize_model_availability import initialize_model_availability_file

class TestInitializeModelAvailability:
    
    def test_creates_file_in_nonexistent_directory(self, tmp_path):
        """Test that the function creates the directory if it doesn't exist."""
        output_path = str(tmp_path / "subdir" / "model_availability.json")
        
        # Directory does not exist
        assert not os.path.exists(os.path.dirname(output_path))
        
        initialize_model_availability_file(output_path)
        
        assert os.path.exists(output_path)
        assert os.path.isdir(os.path.dirname(output_path))

    def test_file_is_valid_json(self, tmp_path):
        """Test that the created file is valid JSON."""
        output_path = str(tmp_path / "model_availability.json")
        initialize_model_availability_file(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, dict)

    def test_contains_required_keys(self, tmp_path):
        """Test that the JSON contains all required top-level keys."""
        output_path = str(tmp_path / "model_availability.json")
        initialize_model_availability_file(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "initialized_at" in data
        assert "task_id" in data
        assert "models" in data
        assert "api_status" in data

    def test_contains_expected_models(self, tmp_path):
        """Test that the JSON contains entries for expected models."""
        output_path = str(tmp_path / "model_availability.json")
        initialize_model_availability_file(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        expected_models = [
            "Salesforce/codegen-mono",
            "CodeLlama-7B",
            "CodeLlama-3B"
        ]
        
        for model in expected_models:
            assert model in data["models"]
            assert "status" in data["models"][model]
            assert "last_checked" in data["models"][model]
            assert "availability" in data["models"][model]
            # Initial status should be 'uninitialized'
            assert data["models"][model]["status"] == "uninitialized"

    def test_api_status_structure(self, tmp_path):
        """Test that api_status contains expected keys."""
        output_path = str(tmp_path / "model_availability.json")
        initialize_model_availability_file(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "hf_inference_api" in data["api_status"]
        assert "last_check" in data["api_status"]
        assert data["api_status"]["hf_inference_api"] == "unknown"

    def test_timestamp_format(self, tmp_path):
        """Test that the timestamp is in ISO format."""
        output_path = str(tmp_path / "model_availability.json")
        initialize_model_availability_file(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        timestamp = data["initialized_at"]
        # Should be parseable by fromisoformat (minus the Z suffix)
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Timestamp {timestamp} is not in valid ISO format")
