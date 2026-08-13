"""
Unit Tests for Canonical Map Derivation (T013)
"""
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import sys
import os

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.canonical_map import derive_canonical_map
from src.clustering import save_null_hypothesis_flag, save_cluster_centers


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def mock_cluster_data_valid(temp_dir):
    """Creates a valid cluster_centers.json"""
    centers = [
        [0.1, 0.2, 0.3],
        [0.8, 0.7, 0.6]
    ]
    data = {
        "centers": centers,
        "k": 2,
        "silhouette": 0.45
    }
    path = temp_dir / "cluster_centers.json"
    with open(path, "w") as f:
        json.dump(data, f)
    return path


@pytest.fixture
def mock_cluster_data_null(temp_dir):
    """Creates a null_hypothesis_flag.json indicating fallback"""
    data = {
        "is_null_hypothesis": True,
        "reason": "Silhouette score < 0.25",
        "global_average_vector": [0.5, 0.5, 0.5]
    }
    path = temp_dir / "null_hypothesis_flag.json"
    with open(path, "w") as f:
        json.dump(data, f)
    return path

def mock_raw_cache(tmp_path: Path):
    """Create mock .npy files in the routing cache."""
    # Create a mock tensor with shape [10, 100, 5] (10 blocks, 100 timesteps, 5 history_dim)
    mock_tensor = np.random.rand(10, 100, 5).astype(np.float32)
    cache_file = tmp_path / "image_0.npy"
    np.save(cache_file, mock_tensor)
    return cache_file

@pytest.fixture
def mock_raw_cache(temp_dir):
    """Creates a mock cache directory structure"""
    (temp_dir / "data").mkdir(parents=True)
    (temp_dir / "data" / "routing_cache").mkdir()
    return temp_dir / "data" / "routing_cache"


def test_derive_canonical_map_valid_clusters(temp_dir):
    """Test derivation when valid clusters exist"""
    # Setup
    centers_path = temp_dir / "cluster_centers.json"
    centers_data = {
        "centers": [[0.1, 0.2], [0.9, 0.8]],
        "k": 2,
        "silhouette": 0.5
    }
    with open(centers_path, "w") as f:
        json.dump(centers_data, f)

    null_path = temp_dir / "null_hypothesis_flag.json"
    # No null flag (or empty/false)
    with open(null_path, "w") as f:
        json.dump({"is_null_hypothesis": False}, f)

    output_path = temp_dir / "canonical_map.json"

    # Execute
    result = derive_canonical_map(
        cluster_centers_path=centers_path,
        null_flag_path=null_path,
        output_path=output_path
    )

    # Verify
    assert result is not None
    assert "blocks" in result
    assert "dominant" in result["blocks"]
    assert result["source"] == "dominant_cluster"
    
    # Verify file on disk
    assert output_path.exists()
    with open(output_path, "r") as f:
        saved = json.load(f)
    assert saved == result

    # Mock load_routing_cache to return a non-empty list
    mock_load_cache.return_value = [mock_tensor]

def test_derive_canonical_map_null_hypothesis(temp_dir):
    """Test derivation when null hypothesis is active (fallback to global average)"""
    # Setup
    centers_path = temp_dir / "cluster_centers.json" # Not used
    with open(centers_path, "w") as f:
        json.dump({"centers": []}, f)

    null_path = temp_dir / "null_hypothesis_flag.json"
    null_data = {
        "is_null_hypothesis": True,
        "global_average_vector": [0.3, 0.3, 0.3]
    }
    with open(null_path, "w") as f:
        json.dump(null_data, f)

    output_path = temp_dir / "canonical_map.json"

    # Execute
    result = derive_canonical_map(
        cluster_centers_path=centers_path,
        null_flag_path=null_path,
        output_path=output_path
    )

    # Verify
    assert result["source"] == "global_average"
    assert "global" in result["blocks"]
    assert np.allclose(result["blocks"]["global"], [0.3, 0.3, 0.3])
    assert output_path.exists()


def test_derive_canonical_map_missing_file(temp_dir):
    """Test that missing cluster centers raises an error"""
    output_path = temp_dir / "canonical_map.json"
    
    # No files exist
    with pytest.raises(FileNotFoundError):
        derive_canonical_map(
            cluster_centers_path=temp_dir / "missing.json",
            null_flag_path=temp_dir / "missing_null.json",
            output_path=output_path
        )


def test_derive_canonical_map_output_file_created(temp_dir):
    """Verify the output file is created with correct schema"""
    # Setup valid data
    centers_path = temp_dir / "cluster_centers.json"
    with open(centers_path, "w") as f:
        json.dump({"centers": [[1.0, 2.0]], "k": 1, "silhouette": 0.1}, f)
    
    null_path = temp_dir / "null_hypothesis_flag.json"
    with open(null_path, "w") as f:
        json.dump({"is_null_hypothesis": False}, f)
    
    output_path = temp_dir / "canonical_map.json"

    derive_canonical_map(
        cluster_centers_path=centers_path,
        null_flag_path=null_path,
        output_path=output_path
    )

    assert output_path.exists()
    with open(output_path, "r") as f:
        data = json.load(f)
    
    # Verify schema keys
    assert "source" in data
    assert "blocks" in data
    # Verify at least one block exists
    assert len(data["blocks"]) > 0
    block_key = list(data["blocks"].keys())[0]
    assert isinstance(data["blocks"][block_key], list)