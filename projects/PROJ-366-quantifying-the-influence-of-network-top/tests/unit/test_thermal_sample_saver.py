"""
Unit tests for thermal_sample_saver (Task T025).
"""
import json
import os
import pickle
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# Adjust import path based on project structure if necessary
from code.simulation.thermal_sample_saver import (
    create_thermal_sample,
    save_thermal_sample,
    save_checksum_manifest,
    process_thermal_samples
)

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_data():
    return {
        "sample_id": "test_sample_001",
        "graph": {
            "nodes": [{"id": 0, "pos": [0, 0, 0]}, {"id": 1, "pos": [1, 1, 1]}],
            "edges": [[0, 1]],
            "features": [1.0, 2.0]
        },
        "conductivity": 12.5,
        "metadata": {
            "converged": True,
            "temperature": 300,
            "topology_metrics": {"avg_degree": 4.5}
        }
    }

def test_create_thermal_sample(sample_data):
    sample = create_thermal_sample(
        sample_id=sample_data["sample_id"],
        graph_data=sample_data["graph"],
        conductivity_value=sample_data["conductivity"],
        metadata=sample_data["metadata"]
    )
    
    assert sample["sample_id"] == "test_sample_001"
    assert sample["conductivity"] == 12.5
    assert sample["checksum"] is None
    assert "graph" in sample
    assert "metadata" in sample

def test_save_thermal_sample_creates_file(temp_output_dir, sample_data):
    sample = create_thermal_sample(
        sample_id=sample_data["sample_id"],
        graph_data=sample_data["graph"],
        conductivity_value=sample_data["conductivity"],
        metadata=sample_data["metadata"]
    )
    
    file_path = save_thermal_sample(sample, temp_output_dir)
    
    assert file_path.exists()
    assert file_path.name == "test_sample_001.pkl"
    
    # Verify content
    with open(file_path, 'rb') as f:
        loaded = pickle.load(f)
    
    assert loaded["sample_id"] == "test_sample_001"
    assert loaded["conductivity"] == 12.5
    assert loaded["checksum"] is not None
    assert len(loaded["checksum"]) == 64  # SHA-256 hex length

def test_save_checksum_manifest(temp_output_dir, sample_data):
    sample = create_thermal_sample(
        sample_id=sample_data["sample_id"],
        graph_data=sample_data["graph"],
        conductivity_value=sample_data["conductivity"],
        metadata=sample_data["metadata"]
    )
    
    file_path = save_thermal_sample(sample, temp_output_dir)
    manifest_path = temp_output_dir / "test_manifest.json"
    
    save_checksum_manifest([file_path], manifest_path)
    
    assert manifest_path.exists()
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    assert len(manifest["files"]) == 1
    assert manifest["files"][0]["path"] == str(file_path)
    assert "checksum" in manifest["files"][0]

def test_process_thermal_samples(temp_output_dir, sample_data):
    # Create a list of sample data
    samples = [sample_data]
    
    saved_paths = process_thermal_samples(samples, temp_output_dir)
    
    assert len(saved_paths) == 1
    assert saved_paths[0].exists()
    
    # Check manifest
    manifest_path = temp_output_dir / "conductivity_samples_manifest.json"
    assert manifest_path.exists()

def test_save_thermal_sample_overwrite(temp_output_dir, sample_data):
    # Save twice to ensure it overwrites correctly
    sample = create_thermal_sample(
        sample_id=sample_data["sample_id"],
        graph_data=sample_data["graph"],
        conductivity_value=sample_data["conductivity"],
        metadata=sample_data["metadata"]
    )
    
    path1 = save_thermal_sample(sample, temp_output_dir)
    sample["conductivity"] = 99.9  # Change value
    path2 = save_thermal_sample(sample, temp_output_dir)
    
    assert path1 == path2
    
    with open(path2, 'rb') as f:
        loaded = pickle.load(f)
    
    assert loaded["conductivity"] == 99.9