import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from drift_scoring import export_results
from config import get_path, ensure_directories

def test_export_results_creates_csv():
    """Test that export_results creates a valid CSV with correct columns."""
    ensure_directories()
    test_data = [
        {"log_id": "1", "drift_score": 0.1, "review_flag": "false"},
        {"log_id": "2", "drift_score": 2.0, "review_flag": "true"},
        {"log_id": "3", "drift_score": 0.5, "review_flag": "false"}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_drift_scores.csv")
        result_path = export_results(test_data, output_path)
        
        assert os.path.exists(result_path)
        df = pd.read_csv(result_path)
        
        assert "log_id" in df.columns
        assert "drift_score" in df.columns
        assert "review_flag" in df.columns
        assert len(df) == 3
        
        assert df.iloc[0]["log_id"] == "1"
        assert df.iloc[0]["drift_score"] == 0.1
        assert df.iloc[0]["review_flag"] == "false"

def test_export_results_empty_list():
    """Test export with empty list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "empty_drift_scores.csv")
        result_path = export_results([], output_path)
        
        assert os.path.exists(result_path)
        df = pd.read_csv(result_path)
        assert len(df) == 0
        assert "log_id" in df.columns

def test_export_results_path_generation():
    """Test that default path is generated correctly."""
    ensure_directories()
    test_data = [
        {"log_id": "1", "drift_score": 0.1, "review_flag": "false"}
    ]
    # This test relies on the config to define the output path.
    # We just verify it doesn't crash and returns a string.
    result_path = export_results(test_data)
    assert isinstance(result_path, str)
    assert "drift_scores.csv" in result_path
    assert os.path.exists(result_path)
