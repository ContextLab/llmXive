import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

# Import the functions to test
from models.log_hyperparameters import (
    load_hyperparameter_log, 
    format_hyperparameter_entry, 
    generate_hyperparameter_log
)

@pytest.fixture
def sample_results():
    return [
        {
            "config_id": 1,
            "config": {
                "learning_rate": 0.001,
                "hidden_dim": 128,
                "dropout": 0.1
            },
            "metrics": {
                "r2_val": 0.95,
                "mae_val": 0.05
            }
        },
        {
            "config_id": 2,
            "config": {
                "learning_rate": 0.01,
                "hidden_dim": 64,
                "dropout": 0.2
            },
            "metrics": {
                "r2_val": 0.88,
                "mae_val": 0.12
            }
        },
        {
            "config_id": 3,
            "config": {
                "learning_rate": 0.0001,
                "hidden_dim": 256,
                "dropout": 0.05
            },
            "metrics": {
                "r2_val": 0.92,
                "mae_val": 0.08
            }
        }
    ]

@pytest.fixture
def temp_log_file(sample_results):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_results, f)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_hyperparameter_log(temp_log_file):
    results = load_hyperparameter_log(temp_log_file)
    assert isinstance(results, list)
    assert len(results) == 3
    assert results[0]["config_id"] == 1

def test_load_hyperparameter_log_missing_file():
    with pytest.raises(FileNotFoundError):
        load_hyperparameter_log(Path("/nonexistent/path.json"))

def test_format_hyperparameter_entry():
    entry = {
        "config_id": 5,
        "config": {"learning_rate": 0.05, "hidden_dim": 100, "dropout": 0.3},
        "metrics": {"r2_val": 0.99, "mae_val": 0.01}
    }
    formatted = format_hyperparameter_entry(entry, 0)
    
    assert formatted["config_id"] == 5
    assert formatted["learning_rate"] == 0.05
    assert formatted["hidden_dim"] == 100
    assert formatted["dropout"] == 0.3
    assert formatted["r2_val"] == 0.99
    assert formatted["mae_val"] == 0.01

def test_generate_hyperparameter_log_top_n(temp_log_file, temp_output_dir):
    output_path = temp_output_dir / "hyperparameter_search.csv"
    
    generate_hyperparameter_log(
        load_hyperparameter_log(temp_log_file), 
        output_path, 
        top_n=2
    )
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        lines = f.readlines()
    
    # Header + 2 rows
    assert len(lines) == 3
    
    # Check header
    assert "config_id" in lines[0]
    assert "r2_val" in lines[0]
    
    # Check that the top 2 (by R2) are selected: 0.95 and 0.92
    # 0.95 is row 1, 0.92 is row 3. 0.88 should be excluded.
    assert "0.95" in lines[1]
    assert "0.92" in lines[2]

def test_generate_hyperparameter_log_full_set(temp_log_file, temp_output_dir):
    output_path = temp_output_dir / "hyperparameter_search.csv"
    
    generate_hyperparameter_log(
        load_hyperparameter_log(temp_log_file), 
        output_path, 
        top_n=10
    )
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        lines = f.readlines()
    
    # Header + 3 rows
    assert len(lines) == 4
    # Sorted by R2 desc: 0.95, 0.92, 0.88
    assert "0.95" in lines[1]
    assert "0.92" in lines[2]
    assert "0.88" in lines[3]
