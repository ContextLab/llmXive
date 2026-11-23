"""
Unit tests for T019b traceability functionality.
"""
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis.task019b_traceability import (
    load_checksum_manifest,
    load_single_run_results,
    find_checksum_for_run,
    update_run_metadata,
    save_updated_results
)
from data_models import SimulationRun

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_checksum_manifest(temp_dir):
    """Test loading a valid checksum manifest."""
    manifest_data = {
        "checksums": [
            {"run_id": "run_001", "hash": "abc123", "file": "matrix.npy"},
            {"run_id": "run_002", "hash": "def456", "file": "matrix2.npy"}
        ]
    }
    
    manifest_path = temp_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f)
    
    result = load_checksum_manifest(manifest_path)
    assert result == manifest_data
    assert len(result["checksums"]) == 2

def test_load_checksum_manifest_missing_file(temp_dir):
    """Test loading a non-existent manifest raises error."""
    with pytest.raises(FileNotFoundError):
        load_checksum_manifest(temp_dir / "nonexistent.json")

def test_load_single_run_results(temp_dir):
    """Test loading valid single run results."""
    results_data = {
        "run_id": "run_001",
        "N": 1000,
        "seed": 42,
        "theta": 2.5,
        "eigenvalues": [2.5, 1.9, 1.8]
    }
    
    results_path = temp_dir / "results.json"
    with open(results_path, 'w') as f:
        json.dump(results_data, f)
    
    result = load_single_run_results(results_path)
    assert result == results_data
    assert result["run_id"] == "run_001"

def test_find_checksum_for_run(temp_dir):
    """Test finding checksum for a specific run."""
    manifest_data = {
        "checksums": [
            {"run_id": "run_001", "hash": "abc123"},
            {"run_id": "run_002", "hash": "def456"}
        ]
    }
    
    # Mock manifest dict
    checksum = find_checksum_for_run(manifest_data, "run_001")
    assert checksum == "abc123"
    
    with pytest.raises(ValueError):
        find_checksum_for_run(manifest_data, "run_nonexistent")

def test_find_checksum_for_run_invalid_manifest(temp_dir):
    """Test finding checksum with invalid manifest format."""
    invalid_manifest = {"data": []}
    with pytest.raises(ValueError):
        find_checksum_for_run(invalid_manifest, "run_001")

def test_update_run_metadata(temp_dir):
    """Test updating run metadata with checksum."""
    results = {
        "run_id": "run_001",
        "N": 1000,
        "seed": 42,
        "theta": 2.5
    }
    checksum_hash = "abc123def456"
    
    # Mock logger
    class MockLogger:
        def info(self, msg): pass
        def error(self, msg): pass
    
    simulation_run = update_run_metadata(results, checksum_hash, MockLogger())
    
    assert isinstance(simulation_run, SimulationRun)
    assert simulation_run.run_id == "run_001"
    assert simulation_run.N == 1000
    assert simulation_run.seed == 42
    assert simulation_run.theta == 2.5
    assert simulation_run.checksum == checksum_hash
    assert simulation_run.status == "registered"

def test_update_run_metadata_missing_fields(temp_dir):
    """Test updating metadata with missing required fields."""
    results = {"run_id": "run_001"}  # Missing N, seed
    
    class MockLogger:
        def info(self, msg): pass
        def error(self, msg): pass
    
    with pytest.raises(ValueError):
        update_run_metadata(results, "hash", MockLogger())

def test_save_updated_results(temp_dir):
    """Test saving updated results to registry."""
    simulation_run = SimulationRun(
        run_id="run_001",
        N=1000,
        seed=42,
        theta=2.5,
        checksum="abc123",
        timestamp=datetime.now(timezone.utc).isoformat(),
        source_file="data/raw/matrix.npy",
        status="registered"
    )
    
    registry_path = temp_dir / "registry.json"
    
    class MockLogger:
        def info(self, msg): pass
        def error(self, msg): pass
    
    save_updated_results(registry_path, simulation_run, MockLogger())
    
    assert registry_path.exists()
    
    with open(registry_path, 'r') as f:
        registry = json.load(f)
    
    assert "runs" in registry
    assert len(registry["runs"]) == 1
    assert registry["runs"][0]["run_id"] == "run_001"
    assert registry["runs"][0]["checksum"] == "abc123"

def test_save_updated_results_update_existing(temp_dir):
    """Test updating an existing run in the registry."""
    # Create initial registry
    initial_registry = {
        "runs": [
            {
                "run_id": "run_001",
                "N": 500,
                "seed": 123,
                "theta": 1.5,
                "checksum": "old_hash"
            }
        ]
    }
    
    registry_path = temp_dir / "registry.json"
    with open(registry_path, 'w') as f:
        json.dump(initial_registry, f)
    
    # Create new simulation run with same ID but different data
    simulation_run = SimulationRun(
        run_id="run_001",
        N=1000,
        seed=42,
        theta=2.5,
        checksum="new_hash",
        timestamp=datetime.now(timezone.utc).isoformat(),
        source_file="data/raw/matrix.npy",
        status="registered"
    )
    
    class MockLogger:
        def info(self, msg): pass
        def error(self, msg): pass
    
    save_updated_results(registry_path, simulation_run, MockLogger())
    
    with open(registry_path, 'r') as f:
        registry = json.load(f)
    
    # Should have updated the existing entry
    assert len(registry["runs"]) == 1
    assert registry["runs"][0]["N"] == 1000
    assert registry["runs"][0]["checksum"] == "new_hash"