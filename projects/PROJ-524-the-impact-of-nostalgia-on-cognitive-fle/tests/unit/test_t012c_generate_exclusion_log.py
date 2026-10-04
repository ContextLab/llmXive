import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
import sys
sys.path.insert(0, 'code')

from task_t012c_generate_exclusion_log import (
    load_exclusion_counts,
    check_simulation_fallback,
    generate_exclusion_log,
    save_exclusion_log
)

def test_load_exclusion_counts_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "counts.json"
        data = {"ERR_MISSING_AGE_FIELD": 5, "ERR_MISSING_SCORE": 2}
        with open(path, 'w') as f:
            json.dump(data, f)
        
        result = load_exclusion_counts(path)
        assert result == data

def test_load_exclusion_counts_missing_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "missing.json"
        with pytest.raises(FileNotFoundError):
            load_exclusion_counts(path)

def test_check_simulation_fallback_true():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "metadata.json"
        with open(path, 'w') as f:
            json.dump({"simulation_mode": True}, f)
        
        assert check_simulation_fallback(path) is True

def test_check_simulation_fallback_false():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "metadata.json"
        with open(path, 'w') as f:
            json.dump({"simulation_mode": False}, f)
        
        assert check_simulation_fallback(path) is False

def test_check_simulation_fallback_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "missing.json"
        assert check_simulation_fallback(path) is False

def test_generate_exclusion_log():
    counts = {
        "ERR_MISSING_AGE_FIELD": 10,
        "ERR_MISSING_SCORE": 5,
        "ERR_MMSE_IMPAIRED": 2
    }
    log = generate_exclusion_log(counts, simulation_fallback=True)
    
    assert log["ERR_MISSING_AGE_FIELD"] == 10
    assert log["ERR_MISSING_SCORE"] == 5
    assert log["ERR_MMSE_IMPAIRED"] == 2
    assert log["SIMULATION_FALLBACK"] is True

def test_save_exclusion_log():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "log.json"
        data = {"key": "value", "count": 42}
        save_exclusion_log(data, path)
        
        assert path.exists()
        with open(path, 'r') as f:
            loaded = json.load(f)
        assert loaded == data