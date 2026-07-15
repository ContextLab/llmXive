"""
Unit tests for the Canonical Map derivation logic.
"""

import json
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.canonical_map import derive_canonical_map
from src.config import get_routing_cache_path


@pytest.fixture
def mock_cluster_data_valid():
    """Mock cluster data with valid clustering (silhouette >= 0.25)."""
    return {
        "method": "kmeans",
        "n_clusters": 3,
        "silhouette_score": 0.45,
        "is_null_hypothesis": False,
        "centers": [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ],
        "labels": [10, 50, 5]  # Cluster 1 is dominant
    }


@pytest.fixture
def mock_cluster_data_null():
    """Mock cluster data with null hypothesis (low silhouette)."""
    return {
        "method": "kmeans",
        "n_clusters": 1,
        "silhouette_score": 0.15,
        "is_null_hypothesis": True,
        "global_average_vector": [0.5, 0.5, 0.5]
    }


@pytest.fixture
def mock_raw_cache():
    """Mock raw routing cache with 2 blocks and 2 timesteps."""
    return {
        "img_001": {
            "0": {
                "0": [0.1, 0.2, 0.3],
                "1": [0.2, 0.3, 0.4]
            },
            "1": {
                "0": [0.3, 0.4, 0.5],
                "1": [0.4, 0.5, 0.6]
            }
        }
    }


def test_derive_canonical_map_valid_clusters(mock_cluster_data_valid, mock_raw_cache, tmp_path):
    """Test derivation when valid clusters exist."""
    # Setup mock files
    cluster_path = tmp_path / "cluster_centers.json"
    with open(cluster_path, 'w') as f:
        json.dump(mock_cluster_data_valid, f)
    
    # Mock load_routing_cache to return our mock data
    with patch('src.canonical_map.load_routing_cache', return_value=mock_raw_cache):
        result = derive_canonical_map(
            cluster_centers_path=cluster_path,
            output_path=tmp_path / "canonical_map.json"
        )

    assert result["method"] == "dominant_cluster"
    assert result["metadata"]["dominant_cluster_index"] == 1
    assert len(result["data"]) == 2  # 2 blocks
    # All blocks should get the dominant center [0.4, 0.5, 0.6]
    for b_id, vec in result["data"].items():
        assert vec == [0.4, 0.5, 0.6]


def test_derive_canonical_map_null_hypothesis(mock_cluster_data_null, mock_raw_cache, tmp_path):
    """Test derivation falls back to global average on null hypothesis."""
    cluster_path = tmp_path / "cluster_centers.json"
    with open(cluster_path, 'w') as f:
        json.dump(mock_cluster_data_null, f)

    with patch('src.canonical_map.load_routing_cache', return_value=mock_raw_cache):
        result = derive_canonical_map(
            cluster_centers_path=cluster_path,
            output_path=tmp_path / "canonical_map.json"
        )

    assert result["method"] == "global_average"
    assert result["metadata"]["reason"] == "Null hypothesis fallback"
    # All blocks should get the global average [0.5, 0.5, 0.5]
    for b_id, vec in result["data"].items():
        assert vec == [0.5, 0.5, 0.5]


def test_derive_canonical_map_missing_file(tmp_path):
    """Test error handling when cluster file is missing."""
    with pytest.raises(FileNotFoundError):
        derive_canonical_map(
            cluster_centers_path=tmp_path / "non_existent.json",
            output_path=tmp_path / "canonical_map.json"
        )

def test_derive_canonical_map_output_file_created(mock_cluster_data_valid, mock_raw_cache, tmp_path):
    """Test that the output file is actually written to disk."""
    cluster_path = tmp_path / "cluster_centers.json"
    output_path = tmp_path / "canonical_map.json"
    
    with open(cluster_path, 'w') as f:
        json.dump(mock_cluster_data_valid, f)

    with patch('src.canonical_map.load_routing_cache', return_value=mock_raw_cache):
        derive_canonical_map(
            cluster_centers_path=cluster_path,
            output_path=output_path
        )

    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert "data" in saved_data
    assert "method" in saved_data
