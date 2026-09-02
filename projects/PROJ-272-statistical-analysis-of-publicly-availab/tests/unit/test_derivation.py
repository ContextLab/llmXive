import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import yaml

from derivation import load_interim_data, generate_derivation_log, finalize_dataset

def test_generate_derivation_log():
    """Test that derivation log contains required metadata."""
    data = {
        "participant_id": ["P1", "P2"],
        "text": ["Hello world", "Test string"],
        "label": ["Control", "AD"]
    }
    df = pd.DataFrame(data)
    input_file = Path("dummy.csv")
    
    log = generate_derivation_log(df, input_file)
    
    assert "timestamp" in log
    assert log["input_rows"] == 2
    assert log["input_columns"] == ["participant_id", "text", "label"]
    assert "steps_applied" in log
    assert len(log["steps_applied"]) == 4
    assert "final_stats" in log

def test_finalize_dataset_writes_files(tmp_path):
    """Test that finalize_dataset writes CSV and YAML."""
    data = {
        "participant_id": ["P1"],
        "text": ["Sample text"],
        "label": ["Control"]
    }
    df = pd.DataFrame(data)
    
    # Mock config to use tmp_path
    import config
    original_get_path = config.get_path
    
    def mock_get_path(base, sub):
        if base == "data" and sub == "interim":
            return tmp_path
        if base == "data" and sub == "raw":
            return tmp_path / "raw"
        return Path(tmp_path)
    
    config.get_path = mock_get_path
    
    try:
        log_entry = {
            "timestamp": "2023-01-01",
            "source_file": "test.csv",
            "input_rows": 1,
            "steps_applied": ["test"]
        }
        
        csv_path, log_path = finalize_dataset(df, log_entry)
        
        assert csv_path.exists()
        assert log_path.exists()
        
        # Verify CSV content
        loaded_df = pd.read_csv(csv_path)
        assert len(loaded_df) == 1
        assert loaded_df["label"].iloc[0] == "Control"
        
        # Verify Log content
        with open(log_path, "r") as f:
            loaded_log = yaml.safe_load(f)
        assert loaded_log["input_rows"] == 1
    finally:
        config.get_path = original_get_path
