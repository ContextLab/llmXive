import os
import sys
import json
import tempfile
import csv
import pytest
from pathlib import Path

# Add code root to path if not already present
code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from models.log_hyperparameters import (
    load_hyperparameter_log,
    format_hyperparameter_entry,
    generate_hyperparameter_log
)

def test_load_hyperparameter_log_valid():
    """Test loading a valid JSON log file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = [
            {"config_id": 1, "learning_rate": 0.001, "hidden_dim": 64, "dropout": 0.1, "r2_val": 0.9, "mae_val": 0.5},
            {"config_id": 2, "learning_rate": 0.01, "hidden_dim": 128, "dropout": 0.2, "r2_val": 0.85, "mae_val": 0.6}
        ]
        json.dump(data, f)
        temp_path = f.name

    try:
        results = load_hyperparameter_log(temp_path)
        assert len(results) == 2
        assert results[0]['config_id'] == 1
        assert results[1]['r2_val'] == 0.85
    finally:
        os.unlink(temp_path)

def test_load_hyperparameter_log_missing_file():
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_hyperparameter_log("non_existent_file.json")

def test_load_hyperparameter_log_invalid_format():
    """Test loading a JSON file that is not a list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"key": "value"}, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError):
            load_hyperparameter_log(temp_path)
    finally:
        os.unlink(temp_path)

def test_format_hyperparameter_entry():
    """Test formatting a single entry."""
    entry = {
        "config_id": 5,
        "learning_rate": 0.005,
        "hidden_dim": 256,
        "dropout": 0.3,
        "r2_val": 0.95,
        "mae_val": 0.4
    }
    formatted = format_hyperparameter_entry(entry)
    
    assert formatted['config_id'] == 5
    assert formatted['learning_rate'] == 0.005
    assert formatted['hidden_dim'] == 256
    assert formatted['dropout'] == 0.3
    assert formatted['r2_val'] == 0.95
    assert formatted['mae_val'] == 0.4

def test_generate_hyperparameter_log():
    """Test generating the CSV with top N configurations."""
    # Create temporary input JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f_in:
        data = [
            {"config_id": 1, "learning_rate": 0.001, "hidden_dim": 64, "dropout": 0.1, "r2_val": 0.9, "mae_val": 0.5},
            {"config_id": 2, "learning_rate": 0.01, "hidden_dim": 128, "dropout": 0.2, "r2_val": 0.85, "mae_val": 0.6},
            {"config_id": 3, "learning_rate": 0.0001, "hidden_dim": 32, "dropout": 0.05, "r2_val": 0.92, "mae_val": 0.45},
            {"config_id": 4, "learning_rate": 0.05, "hidden_dim": 256, "dropout": 0.3, "r2_val": 0.88, "mae_val": 0.55},
        ]
        json.dump(data, f_in)
        input_path = f_in.name

    # Create temporary output CSV path
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f_out:
        output_path = f_out.name
    
    # Clean up the created temp file, we just need the path
    os.unlink(output_path)

    try:
        generate_hyperparameter_log(input_path, output_path, top_n=2)
        
        # Verify file exists
        assert os.path.exists(output_path)
        
        # Read CSV and verify content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        # Check sorting: highest R2 first
        assert float(rows[0]['r2_val']) == 0.92  # Config 3
        assert float(rows[1]['r2_val']) == 0.90  # Config 1
        
        # Check columns
        expected_cols = {'config_id', 'learning_rate', 'hidden_dim', 'dropout', 'r2_val', 'mae_val'}
        assert set(rows[0].keys()) == expected_cols
        
    finally:
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_generate_hyperparameter_log_empty():
    """Test generating CSV when input is empty."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f_in:
        json.dump([], f_in)
        input_path = f_in.name

    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f_out:
        output_path = f_out.name
    os.unlink(output_path)

    try:
        generate_hyperparameter_log(input_path, output_path, top_n=5)
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 0
    finally:
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)