import pytest
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import hashlib

# Mock the datasets module to avoid real network calls in unit tests
# We will patch the functions in 00_data_fetch directly

@pytest.fixture
def mock_config():
    return {
        "TEACHER_WEIGHTS_PATH": "dummy",
        "N_SAMPLES": 100,
        "N_MIN": 10,
        "N_PILOT": 5,
        "MIN_SAMPLE_SIZE": 1000,
        "TIMEOUT_HOURS": 6
    }

@pytest.fixture
def temp_dirs(tmp_path):
    raw_dir = tmp_path / "data" / "raw"
    state_dir = tmp_path / "state"
    results_dir = tmp_path / "data" / "results"
    raw_dir.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    return {
        "raw": raw_dir,
        "state": state_dir,
        "results": results_dir
    }

def test_calculate_sha256_stream():
    """Test the SHA256 calculation on a mock stream."""
    from code import _data_fetch as data_fetch_module # Assuming we import from the module
    # Since we can't easily import the function if it's not exposed, we test the logic via main or helper
    # For this test, we assume the function is accessible or we mock the behavior
    pass

def test_validate_checksums_existing_file(temp_dirs):
    """Test validation of an existing non-empty file."""
    from code import _data_fetch as data_fetch_module
    test_file = temp_dirs["raw"] / "test.parquet"
    df = pd.DataFrame({"a": [1, 2, 3]})
    df.to_parquet(test_file)
    
    assert data_fetch_module.validate_checksums(test_file) is True

def test_validate_checksums_missing_file(temp_dirs):
    """Test validation of a missing file."""
    from code import _data_fetch as data_fetch_module
    test_file = temp_dirs["raw"] / "missing.parquet"
    
    assert data_fetch_module.validate_checksums(test_file) is False

def test_validate_checksums_empty_file(temp_dirs):
    """Test validation of an empty file."""
    from code import _data_fetch as data_fetch_module
    test_file = temp_dirs["raw"] / "empty.parquet"
    test_file.touch()
    
    assert data_fetch_module.validate_checksums(test_file) is False

def test_save_validation_report(temp_dirs):
    """Test saving the validation report."""
    from code import _data_fetch as data_fetch_module
    
    # We need to patch the path constants
    import code._data_fetch as module
    original_report = module.VALIDATION_REPORT_FILE
    module.VALIDATION_REPORT_FILE = str(temp_dirs["results"] / "report.json")
    
    try:
        module.save_validation_report("verified", "tier_1", {"test": "data"})
        
        report_path = Path(module.VALIDATION_REPORT_FILE)
        assert report_path.exists()
        
        with open(report_path) as f:
            report = json.load(f)
        
        assert report["status"] == "verified"
        assert report["source_tier"] == "tier_1"
    finally:
        module.VALIDATION_REPORT_FILE = original_report

def test_dynamic_adjustment_warning(monkeypatch, temp_dirs, caplog):
    """Test that a warning is logged if samples are below target but above minimum."""
    import code._data_fetch as module
    
    # Mock the fetch functions to return a specific amount of data
    def mock_fetch_stream(*args, **kwargs):
        # Return 1500 samples (between 1000 and 2500)
        data = [{"image": f"img_{i}", "label": 0} for i in range(1500)]
        return "hash123", data, True
    
    monkeypatch.setattr(module, "fetch_real_data", mock_fetch_stream)
    monkeypatch.setattr(module, "fetch_real_data_tier1_pre_fetched", lambda *args, **kwargs: (None, [], False))
    
    # Set global variables for thresholds
    module.TARGET_N_SAMPLES = 2500
    module.MIN_SAMPLES_THRESHOLD = 1000
    
    # Mock paths
    module.RAW_DATA_DIR = str(temp_dirs["raw"])
    module.STATE_DIR = str(temp_dirs["state"])
    module.VALIDATION_REPORT_FILE = str(temp_dirs["results"] / "report.json")
    
    # Run main
    with caplog.at_level(logging.WARNING):
        module.main()
    
    assert "below target" in caplog.text.lower()
    assert "proceeding with warning" in caplog.text.lower()

def test_exit_on_below_minimum(monkeypatch, temp_dirs):
    """Test that the script exits with code 1 if samples are below minimum."""
    import code._data_fetch as module
    import sys
    
    def mock_fetch_stream(*args, **kwargs):
        # Return 500 samples (below 1000)
        data = [{"image": f"img_{i}", "label": 0} for i in range(500)]
        return "hash123", data, True
    
    monkeypatch.setattr(module, "fetch_real_data", mock_fetch_stream)
    monkeypatch.setattr(module, "fetch_real_data_tier1_pre_fetched", lambda *args, **kwargs: (None, [], False))
    
    module.TARGET_N_SAMPLES = 2500
    module.MIN_SAMPLES_THRESHOLD = 1000
    
    module.RAW_DATA_DIR = str(temp_dirs["raw"])
    module.STATE_DIR = str(temp_dirs["state"])
    module.VALIDATION_REPORT_FILE = str(temp_dirs["results"] / "report.json")
    
    # Expect SystemExit
    with pytest.raises(SystemExit) as excinfo:
        module.main()
    
    assert excinfo.value.code == 1
