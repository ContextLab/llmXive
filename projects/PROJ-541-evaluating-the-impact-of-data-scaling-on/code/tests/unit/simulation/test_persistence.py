"""
Tests for the persistence module.
"""
import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simulation.config import SimulationConfig, get_default_config
from simulation.persistence import (
    save_synthetic_data,
    load_synthetic_data,
    list_available_runs,
    get_run_summary,
    SYNTHETIC_DATA_DIR
)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for testing."""
    # Temporarily override the module-level constant
    original_dir = SYNTHETIC_DATA_DIR
    test_dir = tmp_path / "synthetic"
    test_dir.mkdir(parents=True, exist_ok=True)

    # We can't easily change the module constant, so we'll use the fixture
    # and pass explicit paths in tests
    return test_dir

@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return SimulationConfig(
        seed=42,
        sample_size=100,
        distribution_type="normal",
        mean_diff=0.0,
        std_dev=1.0,
        skewness=0.0,
        heteroscedasticity=0.0,
        n_iterations=1
    )

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return {
        "group_a": np.random.randn(100),
        "group_b": np.random.randn(100) + 0.5
    }

def test_save_synthetic_data_creates_files(tmp_path, sample_config, sample_data):
    """Test that save_synthetic_data creates the necessary files."""
    # Override the data directory for this test
    test_data_dir = tmp_path / "synthetic"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    # Save data
    run_id = "test_run_1"
    metadata_path, data_dir = save_synthetic_data(
        data=sample_data,
        config=sample_config,
        seed=42,
        run_id=run_id
    )

    # Check that files were created
    assert os.path.exists(metadata_path), "Metadata file not created"
    assert os.path.exists(data_dir), "Data directory not created"

    # Check individual data files
    for key in sample_data.keys():
        data_file = Path(data_dir) / f"{key}.csv"
        assert data_file.exists(), f"Data file for '{key}' not created"

def test_save_synthetic_data_contains_correct_metadata(tmp_path, sample_config, sample_data):
    """Test that metadata file contains correct information."""
    test_data_dir = tmp_path / "synthetic"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    run_id = "test_run_2"
    metadata_path, _ = save_synthetic_data(
        data=sample_data,
        config=sample_config,
        seed=123,
        run_id=run_id
    )

    # Load and verify metadata
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    assert metadata["run_id"] == run_id
    assert metadata["seed"] == 123
    assert "generated_at" in metadata
    assert "config" in metadata
    assert "data_shape" in metadata
    assert "data_types" in metadata

    # Verify config values
    config_meta = metadata["config"]
    assert config_meta["seed"] == 123
    assert config_meta["sample_size"] == 100
    assert config_meta["distribution_type"] == "normal"

def test_save_synthetic_data_serializes_config_correctly(tmp_path, sample_config, sample_data):
    """Test that config is properly serialized to JSON."""
    test_data_dir = tmp_path / "synthetic"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    run_id = "test_run_3"
    metadata_path, _ = save_synthetic_data(
        data=sample_data,
        config=sample_config,
        seed=42,
        run_id=run_id
    )

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    # Check that all config fields are present and serializable
    config_meta = metadata["config"]
    expected_fields = [
        "seed", "sample_size", "distribution_type", "mean_diff",
        "std_dev", "skewness", "heteroscedasticity", "n_iterations"
    ]

    for field in expected_fields:
        assert field in config_meta, f"Field '{field}' missing from serialized config"

def test_load_synthetic_data(tmp_path, sample_config, sample_data):
    """Test that data can be loaded correctly after saving."""
    test_data_dir = tmp_path / "synthetic"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    run_id = "test_run_4"
    save_synthetic_data(
        data=sample_data,
        config=sample_config,
        seed=42,
        run_id=run_id
    )

    # Load the data
    loaded_data, loaded_metadata = load_synthetic_data(run_id)

    # Verify data
    assert set(loaded_data.keys()) == set(sample_data.keys())

    for key in sample_data.keys():
        np.testing.assert_array_almost_equal(
            loaded_data[key],
            sample_data[key],
            decimal=5,
            err_msg=f"Data mismatch for key '{key}'"
        )

    # Verify metadata
    assert loaded_metadata["seed"] == 42
    assert loaded_metadata["run_id"] == run_id

def test_load_synthetic_data_raises_on_missing_file(tmp_path):
    """Test that load_synthetic_data raises error for non-existent run."""
    with pytest.raises(FileNotFoundError):
        load_synthetic_data("non_existent_run")

def test_list_available_runs(tmp_path, sample_config, sample_data):
    """Test listing available runs."""
    test_data_dir = tmp_path / "synthetic"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    # Initially empty
    runs = list_available_runs()
    assert runs == []

    # Add some runs
    for i in range(3):
        save_synthetic_data(
            data=sample_data,
            config=sample_config,
            seed=42 + i,
            run_id=f"run_{i}"
        )

    runs = list_available_runs()
    assert len(runs) == 3
    assert "run_0" in runs
    assert "run_1" in runs
    assert "run_2" in runs

def test_get_run_summary(tmp_path, sample_config, sample_data):
    """Test getting run summary."""
    test_data_dir = tmp_path / "synthetic"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    run_id = "test_run_5"
    save_synthetic_data(
        data=sample_data,
        config=sample_config,
        seed=99,
        run_id=run_id
    )

    summary = get_run_summary(run_id)

    assert summary is not None
    assert summary["run_id"] == run_id
    assert summary["seed"] == 99
    assert "config" in summary
    assert "data_shape" in summary

def test_get_run_summary_returns_none_for_missing_run(tmp_path):
    """Test that get_run_summary returns None for missing run."""
    result = get_run_summary("non_existent_run")
    assert result is None

def test_save_synthetic_data_with_extra_metadata(tmp_path, sample_config, sample_data):
    """Test saving with extra metadata."""
    test_data_dir = tmp_path / "synthetic"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    extra = {
        "author": "test",
        "version": "1.0",
        "notes": "Test run"
    }

    run_id = "test_run_6"
    metadata_path, _ = save_synthetic_data(
        data=sample_data,
        config=sample_config,
        seed=42,
        run_id=run_id,
        extra_metadata=extra
    )

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    assert metadata["author"] == "test"
    assert metadata["version"] == "1.0"
    assert metadata["notes"] == "Test run"

def test_save_synthetic_data_empty_data_raises_error(tmp_path, sample_config):
    """Test that saving empty data raises ValueError."""
    test_data_dir = tmp_path / "synthetic"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError):
        save_synthetic_data(
            data={},
            config=sample_config,
            seed=42,
            run_id="test_run_7"
        )

def test_serialize_config_handles_numpy_types(tmp_path, sample_config, sample_data):
    """Test that numpy types in config are handled correctly."""
    test_data_dir = tmp_path / "synthetic"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    # Create config with explicit numpy types
    config = SimulationConfig(
        seed=np.int64(42),
        sample_size=np.int32(100),
        distribution_type="normal",
        mean_diff=np.float64(0.0),
        std_dev=np.float32(1.0),
        skewness=0.0,
        heteroscedasticity=0.0,
        n_iterations=np.int64(1)
    )

    run_id = "test_run_8"
    metadata_path, _ = save_synthetic_data(
        data=sample_data,
        config=config,
        seed=42,
        run_id=run_id
    )

    # Should not raise and should be valid JSON
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    # Verify values are preserved
    assert metadata["config"]["seed"] == 42
    assert metadata["config"]["sample_size"] == 100
    assert metadata["config"]["mean_diff"] == 0.0
    assert metadata["config"]["std_dev"] == 1.0