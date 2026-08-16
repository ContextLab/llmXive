import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.generate_power_analysis import (
    load_pilot_data,
    estimate_variance,
    calculate_min_sample_size,
    run_power_analysis,
    update_state_yaml,
    write_fail_log
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_parquet(temp_data_dir):
    """Create a sample parquet file for testing."""
    data = {
        'timestamp': pd.date_range(start='2023-01-01', periods=1000, freq='s'),
        'latent_delta_magnitude': np.random.normal(loc=0.5, scale=2.0, size=1000),
        'semantic_feature': np.random.rand(1000),
        'turn_label': np.random.choice([0, 1], size=1000)
    }
    df = pd.DataFrame(data)
    output_path = temp_data_dir / "raw_extract.parquet"
    df.to_parquet(output_path)
    return output_path

def test_load_pilot_data_success(sample_parquet, temp_data_dir, monkeypatch):
    """Test successful loading of parquet data."""
    monkeypatch.setattr("data.generate_power_analysis.POWER_ANALYSIS_INPUT_PATH", sample_parquet)
    df = load_pilot_data()
    assert df is not None
    assert 'latent_delta_magnitude' in df.columns
    assert len(df) == 1000

def test_load_pilot_data_missing_file(monkeypatch):
    """Test loading when file is missing."""
    monkeypatch.setattr("data.generate_power_analysis.POWER_ANALYSIS_INPUT_PATH", Path("/nonexistent/path.parquet"))
    df = load_pilot_data()
    assert df is None

def test_load_pilot_data_empty_file(temp_data_dir, monkeypatch):
    """Test loading when file is empty."""
    empty_df = pd.DataFrame(columns=['timestamp', 'latent_delta_magnitude'])
    output_path = temp_data_dir / "empty.parquet"
    empty_df.to_parquet(output_path)
    monkeypatch.setattr("data.generate_power_analysis.POWER_ANALYSIS_INPUT_PATH", output_path)
    df = load_pilot_data()
    assert df is None

def test_load_pilot_data_missing_column(temp_data_dir, monkeypatch):
    """Test loading when required column is missing."""
    data = {
        'timestamp': pd.date_range(start='2023-01-01', periods=100, freq='s'),
        'other_col': np.random.rand(100)
    }
    df = pd.DataFrame(data)
    output_path = temp_data_dir / "missing_col.parquet"
    df.to_parquet(output_path)
    monkeypatch.setattr("data.generate_power_analysis.POWER_ANALYSIS_INPUT_PATH", output_path)
    result = load_pilot_data()
    assert result is None

def test_estimate_variance(sample_parquet, temp_data_dir, monkeypatch):
    """Test variance estimation."""
    monkeypatch.setattr("data.generate_power_analysis.POWER_ANALYSIS_INPUT_PATH", sample_parquet)
    df = load_pilot_data()
    variance, std_dev = estimate_variance(df)
    assert variance > 0
    assert std_dev > 0
    assert np.isclose(std_dev ** 2, variance)

def test_calculate_min_sample_size():
    """Test sample size calculation logic."""
    variance = 4.0 # std_dev = 2
    # Assuming effect_size_d = 0.2 (default)
    # n = 2 * ((1.96 + 0.84) / 0.2)^2 = 2 * (14)^2 = 2 * 196 = 392
    n = calculate_min_sample_size(variance, effect_size_d=0.2)
    assert n > 0
    assert isinstance(n, int)

def test_run_power_analysis(sample_parquet, temp_data_dir, monkeypatch):
    """Test full power analysis run."""
    monkeypatch.setattr("data.generate_power_analysis.POWER_ANALYSIS_INPUT_PATH", sample_parquet)
    df = load_pilot_data()
    results = run_power_analysis(df)
    
    assert 'expected_variance' in results
    assert 'min_sample_size' in results
    assert 'status' in results
    assert results['status'] == 'success'
    assert results['min_sample_size'] > 0
    assert results['expected_variance'] > 0

def test_write_fail_log(temp_data_dir, monkeypatch):
    """Test failure log writing."""
    log_path = temp_data_dir / "fail.log"
    monkeypatch.setattr("data.generate_power_analysis.POWER_ANALYSIS_FAIL_LOG_PATH", log_path)
    write_fail_log("Test reason")
    assert log_path.exists()
    with open(log_path, 'r') as f:
        content = f.read()
    assert "Test reason" in content

def test_update_state_yaml(temp_data_dir, monkeypatch):
    """Test state.yaml update."""
    state_path = temp_data_dir / "state.yaml"
    monkeypatch.setattr("data.generate_power_analysis.STATE_YAML_PATH", state_path)
    update_state_yaml("completed")
    assert state_path.exists()
    import yaml
    with open(state_path, 'r') as f:
        data = yaml.safe_load(f)
    assert 'projects' in data
    assert 'PROJ-964-llmxive-follow-up-extending-wan-streamer' in data['projects']
    assert data['projects']['PROJ-964-llmxive-follow-up-extending-wan-streamer']['power_analysis_status'] == 'completed'
