"""
Unit tests for the validator module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Mock the dataset loading to avoid network calls in unit tests
@pytest.fixture
def mock_dataset():
    """Create a mock dataset with known span counts."""
    data = [
        {"id": "traj_1", "spans": [1, 2, 3, 4, 5]},  # 5 spans
        {"id": "traj_2", "spans": [1, 2, 3]},        # 3 spans
        {"id": "traj_3", "spans": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}, # 10 spans
        {"id": "traj_4", "spans": [1, 2]},           # 2 spans
        {"id": "traj_5", "spans": [1, 2, 3, 4, 5, 6]}, # 6 spans
    ]
    return iter(data)

@pytest.fixture
def mock_streaming_dataset(mock_dataset):
    """Mock load_dataset to return our mock dataset."""
    with patch('validator.load_dataset') as mock_load:
        mock_load.return_value = {'train': mock_dataset}
        yield mock_load

def test_validate_cutoff_depth(mock_streaming_dataset):
    """
    Test that validate_cutoff_depth correctly analyzes span distribution
    and writes the result to the expected output file.
    """
    from validator import validate_cutoff_depth

    # Ensure the output directory exists for the test
    output_path = Path("data/processed/cutoff_depth_validation.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Run the validation
    result = validate_cutoff_depth(dataset_id="test/dummy")

    # Verify the result structure
    assert "current_cutoff_depth" in result
    assert "recommended_cutoff_depth" in result
    assert "justification" in result
    assert "statistics" in result
    assert "valid" in result

    # Verify statistics
    stats = result["statistics"]
    assert "mean_spans" in stats
    assert "median_spans" in stats
    assert "min_spans" in stats
    assert "max_spans" in stats
    assert "sample_size" in stats

    # Verify calculated stats against our mock data
    # Mock data: [5, 3, 10, 2, 6] -> mean=5.2, median=5, min=2, max=10
    expected_mean = 5.2
    expected_median = 5.0
    expected_min = 2
    expected_max = 10
    
    assert np.isclose(stats["mean_spans"], expected_mean, atol=0.1)
    assert np.isclose(stats["median_spans"], expected_median, atol=0.1)
    assert stats["min_spans"] == expected_min
    assert stats["max_spans"] == expected_max
    assert stats["sample_size"] == 5

    # Verify the file was written
    assert output_path.exists(), f"Output file {output_path} was not created"

    # Verify file contents match the return value
    with open(output_path, 'r') as f:
        file_content = json.load(f)
    
    assert file_content == result

def test_validate_cutoff_depth_short_trajectories(mock_streaming_dataset):
    """
    Test that the validator correctly identifies and reports short trajectories.
    """
    from validator import validate_cutoff_depth

    # Run validation
    result = validate_cutoff_depth(dataset_id="test/dummy")

    # Check that truncated_count reflects trajectories with < 3 spans
    # In our mock data: [5, 3, 10, 2, 6] -> only 1 trajectory has < 3 spans (the one with 2)
    stats = result["statistics"]
    assert stats["truncated_count"] == 1
    assert stats["truncated_percentage"] == 20.0  # 1 out of 5 is 20%

def test_validate_cutoff_depth_empty_dataset():
    """
    Test that the validator raises an error if no valid trajectories are found.
    """
    from validator import validate_cutoff_depth

    # Create an empty iterator
    empty_data = iter([])

    with patch('validator.load_dataset') as mock_load:
        mock_load.return_value = {'train': empty_data}
        
        with pytest.raises(ValueError, match="No valid trajectories found"):
            validate_cutoff_depth(dataset_id="test/empty")

def test_validate_cutoff_depth_output_file_content(mock_streaming_dataset):
    """
    Test that the output file contains all required fields with correct types.
    """
    from validator import validate_cutoff_depth

    output_path = Path("data/processed/cutoff_depth_validation.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = validate_cutoff_depth(dataset_id="test/dummy")

    # Verify file exists
    assert output_path.exists()

    # Read and verify file content types
    with open(output_path, 'r') as f:
        content = json.load(f)

    # Check top-level fields
    assert isinstance(content["current_cutoff_depth"], float)
    assert isinstance(content["recommended_cutoff_depth"], float)
    assert isinstance(content["justification"], str)
    assert isinstance(content["valid"], bool)
    assert isinstance(content["statistics"], dict)

    # Check statistics fields
    stats = content["statistics"]
    assert isinstance(stats["mean_spans"], float)
    assert isinstance(stats["median_spans"], float)
    assert isinstance(stats["min_spans"], int)
    assert isinstance(stats["max_spans"], int)
    assert isinstance(stats["sample_size"], int)
    assert isinstance(stats["truncated_count"], int)
    assert isinstance(stats["truncated_percentage"], float)