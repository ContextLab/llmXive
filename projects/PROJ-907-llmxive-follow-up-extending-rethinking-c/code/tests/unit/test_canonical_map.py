"""
Unit tests for src/canonical_map.py
"""

import json
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.canonical_map import derive_canonical_map, save_canonical_map


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_cluster_data_valid():
    """Mock cluster data with valid clustering results."""
    return {
        "block_0": {
            "centers": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            "silhouette": 0.45,
            "null_hypothesis_triggered": False,
            "null_reason": None
        },
        "block_1": {
            "centers": [[0.7, 0.8, 0.9]],
            "silhouette": 0.60,
            "null_hypothesis_triggered": False,
            "null_reason": None
        }
    }


@pytest.fixture
def mock_cluster_data_null():
    """Mock cluster data with null hypothesis triggered."""
    return {
        "block_0": {
            "centers": [],
            "silhouette": 0.10,
            "null_hypothesis_triggered": True,
            "null_reason": "silhouette < 0.25",
            "global_average": [0.5, 0.5, 0.5]
        },
        "block_1": {
            "centers": [[0.1, 0.2, 0.3]],
            "silhouette": 0.50,
            "null_hypothesis_triggered": False,
            "null_reason": None
        }
    }


@pytest.fixture
def mock_raw_cache(temp_dir, mock_cluster_data_valid):
    """Create a temporary cluster_centers.json file."""
    cache_file = temp_dir / "cluster_centers.json"
    with open(cache_file, 'w') as f:
        json.dump(mock_cluster_data_valid, f)
    return cache_file


@pytest.fixture
def mock_raw_cache_null(temp_dir, mock_cluster_data_null):
    """Create a temporary cluster_centers.json file with null hypothesis."""
    cache_file = temp_dir / "cluster_centers.json"
    with open(cache_file, 'w') as f:
        json.dump(mock_cluster_data_null, f)
    return cache_file


def test_derive_canonical_map_valid_clusters(temp_dir, mock_cluster_data_valid):
    """Test derivation with valid clustering results."""
    cache_file = temp_dir / "cluster_centers.json"
    with open(cache_file, 'w') as f:
        json.dump(mock_cluster_data_valid, f)

    result = derive_canonical_map(cache_file)

    assert "block_0" in result
    assert "block_1" in result
    # Should pick the first center as dominant
    assert result["block_0"] == [0.1, 0.2, 0.3]
    assert result["block_1"] == [0.7, 0.8, 0.9]


def test_derive_canonical_map_null_hypothesis(temp_dir, mock_cluster_data_null):
    """Test derivation when null hypothesis is triggered."""
    cache_file = temp_dir / "cluster_centers.json"
    with open(cache_file, 'w') as f:
        json.dump(mock_cluster_data_null, f)

    result = derive_canonical_map(cache_file)

    assert "block_0" in result
    assert "block_1" in result
    # block_0 should use global_average
    assert result["block_0"] == [0.5, 0.5, 0.5]
    # block_1 should use dominant center
    assert result["block_1"] == [0.1, 0.2, 0.3]


def test_derive_canonical_map_missing_file(temp_dir):
    """Test that FileNotFoundError is raised when file is missing."""
    with pytest.raises(FileNotFoundError):
        derive_canonical_map(temp_dir / "nonexistent.json")


def test_derive_canonical_map_output_file_created(temp_dir, mock_cluster_data_valid):
    """Test that save_canonical_map creates the output file."""
    cache_file = temp_dir / "cluster_centers.json"
    with open(cache_file, 'w') as f:
        json.dump(mock_cluster_data_valid, f)

    canonical_map = derive_canonical_map(cache_file)
    output_file = temp_dir / "canonical_map.json"
    
    save_canonical_map(canonical_map, output_file)

    assert output_file.exists()
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == canonical_map