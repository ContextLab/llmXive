"""
Unit tests for T043: Semantic Similarity Threshold Validator.
Tests the validation logic and retry mechanisms for injected redundancy.
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Import the module under test
from data_loader import (
    validate_injected_similarity,
    run_validation_pipeline,
    DataInjectionFailureError,
    TARGET_SIMILARITY_THRESHOLD
)

@pytest.fixture
def mock_injected_data():
    """Create a mock injected dataset with known similarity values."""
    return {
        "name": "test_dataset",
        "clusters": [
            {"cluster_id": "c1", "members": ["d1", "d2", "d3"], "avg_similarity": 0.96},
            {"cluster_id": "c2", "members": ["d4", "d5"], "avg_similarity": 0.97},
            {"cluster_id": "c3", "members": ["d6", "d7", "d8"], "avg_similarity": 0.94}
        ]
    }

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_validate_sim_success(temp_data_dir, mock_injected_data):
    """Test validation when similarity threshold is met."""
    # Save mock data
    dataset_name = "test"
    path = os.path.join(temp_data_dir, f"injected_{dataset_name}.json")
    with open(path, 'w') as f:
        json.dump(mock_injected_data, f)

    # Run validation
    result = validate_injected_similarity(
        dataset_name=dataset_name,
        data_dir=temp_data_dir,
        target_threshold=0.95
    )

    assert result["status"] == "success"
    assert result["dataset"] == dataset_name
    assert result["achieved_avg_similarity"] >= 0.95
    assert result["target_threshold"] == 0.95

def test_validate_sim_partial_success(temp_data_dir, mock_injected_data):
    """Test validation when similarity is below threshold but non-zero."""
    # Modify mock data to have lower similarity
    mock_injected_data["clusters"][0]["avg_similarity"] = 0.90
    mock_injected_data["clusters"][1]["avg_similarity"] = 0.89
    mock_injected_data["clusters"][2]["avg_similarity"] = 0.91

    path = os.path.join(temp_data_dir, "injected_test.json")
    with open(path, 'w') as f:
        json.dump(mock_injected_data, f)

    # Run validation
    result = validate_injected_similarity(
        dataset_name="test",
        data_dir=temp_data_dir,
        target_threshold=0.95
    )

    assert result["status"] == "partial_success"
    assert result["achieved_avg_similarity"] < 0.95
    assert "Proceeding with achieved similarity" in result["details"]["message"]

def test_validate_sim_missing_file(temp_data_dir):
    """Test validation when dataset file is missing."""
    result = validate_injected_similarity(
        dataset_name="nonexistent",
        data_dir=temp_data_dir,
        target_threshold=0.95
    )

    assert result["status"] == "failed"
    assert "Dataset not found" in result["details"]["reason"]

def test_validate_sim_empty_clusters(temp_data_dir):
    """Test validation when clusters list is empty."""
    path = os.path.join(temp_data_dir, "injected_test.json")
    with open(path, 'w') as f:
        json.dump({"name": "test", "clusters": []}, f)

    result = validate_injected_similarity(
        dataset_name="test",
        data_dir=temp_data_dir,
        target_threshold=0.95
    )

    assert result["status"] == "failed"
    assert "Empty clusters list" in result["details"]["reason"]

def test_run_validation_pipeline(temp_data_dir, mock_injected_data):
    """Test the full validation pipeline for multiple datasets."""
    # Create multiple dataset files
    for name in ["ds1", "ds2"]:
        path = os.path.join(temp_data_dir, f"injected_{name}.json")
        with open(path, 'w') as f:
            json.dump(mock_injected_data, f)

    output_file = os.path.join(temp_data_dir, "validation_status.json")

    # Run pipeline
    results = run_validation_pipeline(
        dataset_names=["ds1", "ds2"],
        data_dir=temp_data_dir,
        output_file=output_file,
        target_threshold=0.95
    )

    assert "validation_timestamp" in results
    assert "target_threshold" in results
    assert len(results["datasets"]) == 2
    assert os.path.exists(output_file)

    # Verify file content
    with open(output_file, 'r') as f:
        saved_results = json.load(f)
    assert saved_results == results

def test_validation_tolerance(temp_data_dir):
    """Test that small tolerance is handled correctly."""
    # Create data with similarity exactly at threshold
    mock_data = {
        "name": "test",
        "clusters": [
            {"cluster_id": "c1", "members": ["d1"], "avg_similarity": 0.95}
        ]
    }
    path = os.path.join(temp_data_dir, "injected_test.json")
    with open(path, 'w') as f:
        json.dump(mock_data, f)

    result = validate_injected_similarity(
        dataset_name="test",
        data_dir=temp_data_dir,
        target_threshold=0.95
    )

    # Should succeed as 0.95 >= 0.95
    assert result["status"] == "success"

def test_validation_below_threshold(temp_data_dir):
    """Test validation with significantly below threshold."""
    mock_data = {
        "name": "test",
        "clusters": [
            {"cluster_id": "c1", "members": ["d1"], "avg_similarity": 0.80}
        ]
    }
    path = os.path.join(temp_data_dir, "injected_test.json")
    with open(path, 'w') as f:
        json.dump(mock_data, f)

    result = validate_injected_similarity(
        dataset_name="test",
        data_dir=temp_data_dir,
        target_threshold=0.95
    )

    assert result["status"] == "partial_success"
    assert result["achieved_avg_similarity"] == 0.80
    assert result["details"]["clusters_below_threshold"] == 1
    assert result["details"]["clusters_above_threshold"] == 0
