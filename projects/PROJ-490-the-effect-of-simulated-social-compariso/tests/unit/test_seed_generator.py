"""
Unit Tests for Seed File Generation (T011c)

Tests the generate_seed_file function to ensure it:
1. Creates the correct file structure.
2. Contains the expected ground truth parameters.
3. Handles directory creation.
4. Validates JSON schema compliance.
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

# Import the function to test
from data.seed_generator import generate_seed_file


class TestSeedGenerator:
    """Test suite for the seed generation module."""

    def test_seed_file_creation(self, tmp_path):
        """Test that the seed file is created at the specified path."""
        output_file = tmp_path / "test_seed.json"
        
        result_path = generate_seed_file(output_path=output_file)
        
        assert result_path == output_file
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_seed_file_structure(self, tmp_path):
        """Test that the generated JSON has the correct top-level keys."""
        output_file = tmp_path / "test_seed.json"
        
        generate_seed_file(output_path=output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "ground_truth_parameters" in data
        assert "generated_at" in data["metadata"]
        assert "task_id" in data["metadata"]
        assert data["metadata"]["task_id"] == "T011c"

    def test_ground_truth_parameters(self, tmp_path):
        """Test that the ground truth parameters match the specification."""
        output_file = tmp_path / "test_seed.json"
        
        generate_seed_file(output_path=output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        params = data["ground_truth_parameters"]
        
        # Verify specific ground truth values from T010
        assert params["intercept"] == 0.0
        assert params["main_effect_avatar"] == 0.1
        assert params["main_effect_comparison"] == 0.1
        assert params["interaction_beta"] == 0.2
        assert params["noise_sigma"] == 1.0
        assert params["sample_size"] >= 100
        assert params["label"] == "Pipeline Validation Only"

    def test_custom_parameters(self, tmp_path):
        """Test that custom parameters can be passed and saved."""
        custom_params = {
            "intercept": 5.0,
            "main_effect_avatar": 0.5,
            "main_effect_comparison": 0.5,
            "interaction_beta": 0.8,
            "noise_sigma": 2.0,
            "sample_size": 200,
            "random_seed": 42,
            "label": "Custom Test Run"
        }
        output_file = tmp_path / "custom_seed.json"
        
        generate_seed_file(output_path=output_file, ground_truth_params=custom_params)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data["ground_truth_parameters"] == custom_params

    def test_directory_creation(self, tmp_path):
        """Test that the function creates parent directories if they don't exist."""
        nested_dir = tmp_path / "subdir" / "deep" / "nested"
        output_file = nested_dir / "seed.json"
        
        # Ensure directory does not exist yet
        assert not nested_dir.exists()
        
        result_path = generate_seed_file(output_path=output_file)
        
        assert nested_dir.exists()
        assert result_path.exists()

    def test_json_validity(self, tmp_path):
        """Test that the output is valid JSON."""
        output_file = tmp_path / "valid_json.json"
        
        generate_seed_file(output_path=output_file)
        
        # This will raise an exception if the file is not valid JSON
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, dict)

    def test_timestamp_format(self, tmp_path):
        """Test that the timestamp is in ISO8601 format."""
        output_file = tmp_path / "timestamp_test.json"
        
        generate_seed_file(output_path=output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        timestamp_str = data["metadata"]["generated_at"]
        
        # Basic check for ISO format (YYYY-MM-DDTHH:MM:SS)
        assert "T" in timestamp_str
        # Try to parse it to ensure it's valid
        try:
            # Handle the trailing 'Z' if present
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            datetime.fromisoformat(timestamp_str)
        except ValueError:
            pytest.fail(f"Timestamp {timestamp_str} is not a valid ISO8601 date.")