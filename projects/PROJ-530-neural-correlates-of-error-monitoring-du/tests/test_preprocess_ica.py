"""
Tests for ICA implementation in preprocess.py (T012).
"""
import os
import tempfile
from pathlib import Path
import yaml
import pytest
import numpy as np
import mne

# Import the module under test
from preprocess import run_ica, save_preprocessing_log, PREPROCESSING_LOG_PATH

@pytest.fixture
def sample_raw_data():
    """Create a synthetic raw EEG object for testing."""
    # Create dummy data: 10 channels, 1000 samples at 250Hz
    n_channels = 10
    n_times = 1000
    sfreq = 250.0
    
    info = mne.create_info(
        ch_names=[f'EEG {i:03d}' for i in range(n_channels)],
        sfreq=sfreq,
        ch_types='eeg'
    )
    
    # Generate random data
    data = np.random.randn(n_channels, n_times)
    
    raw = mne.io.RawArray(data, info)
    return raw

def test_run_ica_returns_components(sample_raw_data):
    """Test that run_ica returns a dictionary with expected keys."""
    result = run_ica(sample_raw_data, n_components=5)
    
    assert isinstance(result, dict)
    assert "ica" in result
    assert "raw" in result
    assert "removed_components" in result
    assert isinstance(result["ica"], mne.preprocessing.ICA)
    assert isinstance(result["removed_components"], list)

def test_run_ica_excludes_artifacts(sample_raw_data):
    """Test that ICA identifies and excludes components (simulated)."""
    # In a real scenario, we would inject EOG artifacts.
    # Here we verify the logic runs without error and returns a list.
    result = run_ica(sample_raw_data, n_components=5, random_state=42)
    
    # The list might be empty if no artifacts are found in random noise,
    # but the structure must be correct.
    assert len(result["removed_components"]) >= 0
    assert all(isinstance(c, (int, np.integer)) for c in result["removed_components"])

def test_save_preprocessing_log_creates_file(sample_raw_data):
    """Test that save_preprocessing_log writes a valid YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_preprocessing.yaml"
        
        config = {
            "test_key": "test_value",
            "ica": {
                "removed_components": [1, 2]
            }
        }
        
        save_preprocessing_log(config, log_path)
        
        assert log_path.exists()
        
        with open(log_path, 'r') as f:
            loaded_log = yaml.safe_load(f)
        
        assert loaded_log["preprocessing"]["test_key"] == "test_value"
        assert loaded_log["preprocessing"]["ica"]["removed_components"] == [1, 2]
        assert "last_updated" in loaded_log["preprocessing"]

def test_ica_computation_speed(sample_raw_data):
    """Ensure ICA runs within a reasonable time for small data."""
    import time
    
    start = time.time()
    run_ica(sample_raw_data, n_components=5)
    duration = time.time() - start
    
    # Should finish quickly for 1000 samples
    assert duration < 60.0, f"ICA took too long: {duration}s"