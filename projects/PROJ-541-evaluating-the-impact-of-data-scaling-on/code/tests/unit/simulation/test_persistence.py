"""
Tests for data persistence functionality.
"""
import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch

from simulation.config import SimulationConfig
from simulation.persistence import (
    save_synthetic_data,
    load_synthetic_data,
    list_available_runs,
    get_run_summary,
    _ensure_output_dir,
    _generate_run_id,
    _serialize_config
)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for testing."""
    # Patch the OUTPUT_DIR to use the temp directory
    with patch('simulation.persistence.OUTPUT_DIR', tmp_path):
        yield tmp_path

@pytest.fixture
def sample_config():
    """Create a sample SimulationConfig for testing."""
    return SimulationConfig(
        n_samples=100,
        n_features=5,
        distribution_type="normal",
        mean_diff=0.0,
        skewness=0.0,
        heteroscedasticity=0.0,
        seed=42
    )

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return {
        "feature_1": np.random.normal(0, 1, 100),
        "feature_2": np.random.normal(1, 2, 100),
        "label": np.random.binomial(1, 0.5, 100)
    }

def test_save_synthetic_data_creates_files(temp_output_dir, sample_data, sample_config):
    """Test that save_synthetic_data creates both CSV and JSON files."""
    run_id = "test_run_001"
    result_path = save_synthetic_data(
        data=sample_data,
        config=sample_config,
        seed=42,
        run_id=run_id
    )
    
    csv_path = temp_output_dir / f"data_{run_id}.csv"
    meta_path = temp_output_dir / f"meta_{run_id}.json"
    
    assert csv_path.exists(), "CSV file should be created"
    assert meta_path.exists(), "Metadata JSON file should be created"
    assert result_path == str(csv_path)

def test_save_synthetic_data_contains_correct_metadata(temp_output_dir, sample_data, sample_config):
    """Test that saved metadata contains expected fields."""
    run_id = "test_run_002"
    save_synthetic_data(
        data=sample_data,
        config=sample_config,
        seed=123,
        run_id=run_id
    )
    
    meta_path = temp_output_dir / f"meta_{run_id}.json"
    with open(meta_path, 'r') as f:
        metadata = json.load(f)
    
    assert metadata["run_id"] == run_id
    assert metadata["seed"] == 123
    assert "generated_at" in metadata
    assert "config" in metadata
    assert "data_shape" in metadata
    assert metadata["data_shape"]["rows"] == 100
    assert metadata["data_shape"]["columns"] == 3
    assert "statistics" in metadata
    assert all(col in metadata["statistics"] for col in sample_data.keys())

def test_save_synthetic_data_serializes_config_correctly(temp_output_dir, sample_config):
    """Test that config is properly serialized to JSON."""
    run_id = "test_run_003"
    sample_data = {"x": np.random.normal(0, 1, 10)}
    
    save_synthetic_data(
        data=sample_data,
        config=sample_config,
        seed=42,
        run_id=run_id
    )
    
    meta_path = temp_output_dir / f"meta_{run_id}.json"
    with open(meta_path, 'r') as f:
        metadata = json.load(f)
    
    config = metadata["config"]
    assert config["n_samples"] == 100
    assert config["n_features"] == 5
    assert config["distribution_type"] == "normal"
    assert config["mean_diff"] == 0.0

def test_load_synthetic_data(temp_output_dir, sample_data, sample_config):
    """Test that load_synthetic_data retrieves correct data and metadata."""
    run_id = "test_run_004"
    save_synthetic_data(
        data=sample_data,
        config=sample_config,
        seed=42,
        run_id=run_id
    )
    
    df, metadata = load_synthetic_data(run_id)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 100
    assert set(df.columns) == set(sample_data.keys())
    assert metadata["run_id"] == run_id
    assert metadata["seed"] == 42

def test_load_synthetic_data_raises_on_missing_file(temp_output_dir):
    """Test that load_synthetic_data raises FileNotFoundError for missing run."""
    with pytest.raises(FileNotFoundError):
        load_synthetic_data("nonexistent_run")

def test_list_available_runs(temp_output_dir, sample_data, sample_config):
    """Test that list_available_runs returns all saved runs."""
    run_ids = ["run_001", "run_002", "run_003"]
    
    for run_id in run_ids:
        save_synthetic_data(
            data=sample_data,
            config=sample_config,
            seed=42,
            run_id=run_id
        )
    
    available = list_available_runs()
    assert set(available) == set(run_ids)

def test_get_run_summary(temp_output_dir, sample_data, sample_config):
    """Test that get_run_summary returns metadata without loading data."""
    run_id = "test_run_005"
    save_synthetic_data(
        data=sample_data,
        config=sample_config,
        seed=42,
        run_id=run_id
    )
    
    summary = get_run_summary(run_id)
    
    assert summary is not None
    assert summary["run_id"] == run_id
    assert "data_shape" in summary

def test_get_run_summary_returns_none_for_missing_run(temp_output_dir):
    """Test that get_run_summary returns None for missing run."""
    assert get_run_summary("nonexistent_run") is None

def test_save_synthetic_data_with_extra_metadata(temp_output_dir, sample_data, sample_config):
    """Test that extra metadata is included in saved file."""
    run_id = "test_run_006"
    extra_meta = {
        "experiment_name": "test_experiment",
        "author": "test_user"
    }
    
    save_synthetic_data(
        data=sample_data,
        config=sample_config,
        seed=42,
        run_id=run_id,
        metadata_extra=extra_meta
    )
    
    meta_path = temp_output_dir / f"meta_{run_id}.json"
    with open(meta_path, 'r') as f:
        metadata = json.load(f)
    
    assert metadata["experiment_name"] == "test_experiment"
    assert metadata["author"] == "test_user"

def test_save_synthetic_data_empty_data_raises_error(temp_output_dir, sample_config):
    """Test that saving empty data raises ValueError."""
    with pytest.raises(ValueError, match="Data dictionary cannot be empty"):
        save_synthetic_data(
            data={},
            config=sample_config,
            seed=42,
            run_id="test_run_007"
        )

def test_serialize_config_handles_numpy_types(sample_config):
    """Test that _serialize_config properly handles numpy types."""
    result = _serialize_config(sample_config)
    
    # Ensure all values are native Python types
    assert isinstance(result["n_samples"], int)
    assert isinstance(result["n_features"], int)
    assert isinstance(result["mean_diff"], float)
    assert isinstance(result["skewness"], float)
    assert isinstance(result["heteroscedasticity"], float)
    assert isinstance(result["seed"], int)
    assert isinstance(result["distribution_type"], str)