"""
test_canonical_map.py

Unit tests for the canonical_map module.
"""
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.canonical_map import derive_canonical_map

# Mock data for testing
def mock_cluster_data_valid():
    return {
        "clusters": [
            {"cluster_id": 0, "size": 50, "center": [0.1, 0.2, 0.3]},
            {"cluster_id": 1, "size": 30, "center": [0.4, 0.5, 0.6]}
        ],
        "silhouette_score": 0.45,
        "k": 2
    }

def mock_cluster_data_null():
    return {
        "clusters": [],
        "silhouette_score": 0.1,
        "k": 0
    }

def mock_raw_cache(tmp_path: Path):
    """Create mock .npy files in the routing cache."""
    # Create a mock tensor with shape [10, 100, 5] (10 blocks, 100 timesteps, 5 history_dim)
    mock_tensor = np.random.rand(10, 100, 5).astype(np.float32)
    cache_file = tmp_path / "image_0.npy"
    np.save(cache_file, mock_tensor)
    return cache_file

@patch('src.canonical_map.load_routing_cache')
@patch('src.canonical_map.Path.glob')
def test_derive_canonical_map_valid_clusters(mock_glob, mock_load_cache, tmp_path):
    """Test derive_canonical_map with valid clustering results."""
    # Setup mock data
    mock_cache_path = tmp_path / "cache"
    mock_cache_path.mkdir()
    mock_cluster_path = tmp_path / "cluster_centers.json"
    mock_null_flag_path = tmp_path / "null_flag.json"

    # Create mock cluster centers file
    cluster_data = mock_cluster_data_valid()
    with open(mock_cluster_path, 'w') as f:
        json.dump(cluster_data, f)

    # Create mock null hypothesis flag (not null)
    null_flag_data = {"is_null_hypothesis": False}
    with open(mock_null_flag_path, 'w') as f:
        json.dump(null_flag_data, f)

    # Create mock routing cache file
    mock_tensor = np.random.rand(10, 100, 5).astype(np.float32)
    cache_file = mock_cache_path / "image_0.npy"
    np.save(cache_file, mock_tensor)

    # Mock load_routing_cache to return a non-empty list
    mock_load_cache.return_value = [mock_tensor]

    # Mock Path.glob to return our mock file
    mock_glob.return_value = [cache_file]

    # Call the function
    output_path = tmp_path / "canonical_map.json"
    result = derive_canonical_map(
        routing_cache_path=mock_cache_path,
        cluster_centers_path=mock_cluster_path,
        null_hypothesis_flag_path=mock_null_flag_path,
        output_path=output_path
    )

    # Assertions
    assert result["source"] == "cluster"
    assert result["dominant_cluster_id"] == 0
    assert len(result["entries"]) == 10
    for entry in result["entries"]:
        assert entry["block_id"] in range(10)
        assert entry["source"] == "cluster"
        assert entry["cluster_id"] == 0
        assert len(entry["weight_vector"]) == 5

    # Check file was created
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    assert saved_data["source"] == "cluster"

@patch('src.canonical_map.load_routing_cache')
@patch('src.canonical_map.Path.glob')
def test_derive_canonical_map_null_hypothesis(mock_glob, mock_load_cache, tmp_path):
    """Test derive_canonical_map with null hypothesis (global average)."""
    # Setup mock data
    mock_cache_path = tmp_path / "cache"
    mock_cache_path.mkdir()
    mock_cluster_path = tmp_path / "cluster_centers.json"
    mock_null_flag_path = tmp_path / "null_flag.json"

    # Create mock cluster centers file (empty clusters)
    cluster_data = mock_cluster_data_null()
    with open(mock_cluster_path, 'w') as f:
        json.dump(cluster_data, f)

    # Create mock null hypothesis flag (null)
    null_flag_data = {"is_null_hypothesis": True}
    with open(mock_null_flag_path, 'w') as f:
        json.dump(null_flag_data, f)

    # Create mock routing cache file
    mock_tensor = np.random.rand(10, 100, 5).astype(np.float32)
    cache_file = mock_cache_path / "image_0.npy"
    np.save(cache_file, mock_tensor)

    # Mock load_routing_cache to return a non-empty list
    mock_load_cache.return_value = [mock_tensor]

    # Mock Path.glob to return our mock file
    mock_glob.return_value = [cache_file]

    # Call the function
    output_path = tmp_path / "canonical_map.json"
    result = derive_canonical_map(
        routing_cache_path=mock_cache_path,
        cluster_centers_path=mock_cluster_path,
        null_hypothesis_flag_path=mock_null_flag_path,
        output_path=output_path
    )

    # Assertions
    assert result["source"] == "global_average"
    assert len(result["entries"]) == 10
    for entry in result["entries"]:
        assert entry["block_id"] in range(10)
        assert entry["source"] == "global_average"
        assert len(entry["weight_vector"]) == 5

    # Check file was created
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    assert saved_data["source"] == "global_average"

@patch('src.canonical_map.load_routing_cache')
@patch('src.canonical_map.Path.glob')
def test_derive_canonical_map_missing_file(mock_glob, mock_load_cache, tmp_path):
    """Test derive_canonical_map when cluster centers file is missing."""
    # Setup mock data
    mock_cache_path = tmp_path / "cache"
    mock_cache_path.mkdir()
    mock_cluster_path = tmp_path / "cluster_centers.json" # Not created
    mock_null_flag_path = tmp_path / "null_flag.json"

    # Create mock null hypothesis flag (not null)
    null_flag_data = {"is_null_hypothesis": False}
    with open(mock_null_flag_path, 'w') as f:
        json.dump(null_flag_data, f)

    # Create mock routing cache file
    mock_tensor = np.random.rand(10, 100, 5).astype(np.float32)
    cache_file = mock_cache_path / "image_0.npy"
    np.save(cache_file, mock_tensor)

    # Mock load_routing_cache to return a non-empty list
    mock_load_cache.return_value = [mock_tensor]

    # Mock Path.glob to return our mock file
    mock_glob.return_value = [cache_file]

    # Call the function - should raise FileNotFoundError
    output_path = tmp_path / "canonical_map.json"
    with pytest.raises(FileNotFoundError):
        derive_canonical_map(
            routing_cache_path=mock_cache_path,
            cluster_centers_path=mock_cluster_path,
            null_hypothesis_flag_path=mock_null_flag_path,
            output_path=output_path
        )

@patch('src.canonical_map.load_routing_cache')
@patch('src.canonical_map.Path.glob')
def test_derive_canonical_map_output_file_created(mock_glob, mock_load_cache, tmp_path):
    """Test that the output file is created with the correct structure."""
    # Setup mock data
    mock_cache_path = tmp_path / "cache"
    mock_cache_path.mkdir()
    mock_cluster_path = tmp_path / "cluster_centers.json"
    mock_null_flag_path = tmp_path / "null_flag.json"

    # Create mock cluster centers file
    cluster_data = mock_cluster_data_valid()
    with open(mock_cluster_path, 'w') as f:
        json.dump(cluster_data, f)

    # Create mock null hypothesis flag (not null)
    null_flag_data = {"is_null_hypothesis": False}
    with open(mock_null_flag_path, 'w') as f:
        json.dump(null_flag_data, f)

    # Create mock routing cache file
    mock_tensor = np.random.rand(10, 100, 5).astype(np.float32)
    cache_file = mock_cache_path / "image_0.npy"
    np.save(cache_file, mock_tensor)

    # Mock load_routing_cache to return a non-empty list
    mock_load_cache.return_value = [mock_tensor]

    # Mock Path.glob to return our mock file
    mock_glob.return_value = [cache_file]

    # Call the function
    output_path = tmp_path / "canonical_map.json"
    result = derive_canonical_map(
        routing_cache_path=mock_cache_path,
        cluster_centers_path=mock_cluster_path,
        null_hypothesis_flag_path=mock_null_flag_path,
        output_path=output_path
    )

    # Assertions on file structure
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved_data = json.load(f)

    # Check top-level keys
    assert "source" in saved_data
    assert "num_blocks" in saved_data
    assert "num_timesteps" in saved_data
    assert "history_dim" in saved_data
    assert "entries" in saved_data

    # Check entry structure
    for entry in saved_data["entries"]:
        assert "block_id" in entry
        assert "weight_vector" in entry
        assert "source" in entry