import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

# Mock the config module to use a temporary directory
@pytest.fixture
def temp_project_root(tmp_path):
    # Create necessary subdirectories
    (tmp_path / "logs").mkdir(exist_ok=True)
    return tmp_path

@pytest.fixture
def setup_mock_config(temp_project_root):
    with patch('code.utils.logging.get_project_root', return_value=temp_project_root):
        with patch('code.utils.config.get_project_root', return_value=temp_project_root):
            yield temp_project_root

def test_log_excluded_molecules(setup_mock_config, temp_project_root):
    """Test that excluded molecules are logged correctly in JSON format."""
    from code.utils.logging import log_excluded_molecules
    
    test_smiles = ["CCO", "invalid_smiles", "C1=CC=CC=C1"]
    count = len(test_smiles)
    
    log_excluded_molecules(count, test_smiles)
    
    log_path = temp_project_root / "logs" / "excluded_molecules.log"
    assert log_path.exists(), "Log file should be created"
    
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    assert len(lines) == 1, "Should have one log entry"
    
    entry = json.loads(lines[0])
    assert entry["type"] == "excluded_molecules"
    assert entry["count"] == count
    assert entry["smiles_list"] == test_smiles

def test_log_errors(setup_mock_config, temp_project_root):
    """Test that errors are logged correctly in JSON format."""
    from code.utils.logging import log_errors
    
    test_errors = [
        {"smiles": "invalid1", "reason": "syntax_error", "line": 1},
        {"smiles": "invalid2", "reason": "valence_error", "line": 5}
    ]
    
    log_errors(test_errors)
    
    log_path = temp_project_root / "logs" / "ingestion_errors.log"
    assert log_path.exists(), "Log file should be created"
    
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    assert len(lines) == 2, "Should have two log entries"
    
    for i, line in enumerate(lines):
        entry = json.loads(line)
        assert entry == test_errors[i]

def test_log_dataset_statistics(setup_mock_config, temp_project_root):
    """Test that dataset statistics are logged correctly."""
    from code.utils.logging import log_dataset_statistics
    
    test_stats = {
        "total_molecules": 1000,
        "valid_molecules": 950,
        "invalid_molecules": 50,
        "avg_molecular_weight": 250.5
    }
    
    log_dataset_statistics(test_stats)
    
    log_path = temp_project_root / "logs" / "dataset_statistics.log"
    assert log_path.exists(), "Log file should be created"
    
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    assert len(lines) == 1, "Should have one log entry"
    
    entry = json.loads(lines[0])
    assert entry["type"] == "dataset_statistics"
    assert entry["statistics"] == test_stats

def test_log_split_statistics(setup_mock_config, temp_project_root):
    """Test that split statistics are logged correctly."""
    from code.utils.logging import log_split_statistics
    
    test_stats = {
        "train_size": 800,
        "test_size": 200,
        "train_mean_mw": 245.3,
        "test_mean_mw": 258.7
    }
    
    log_split_statistics(test_stats)
    
    log_path = temp_project_root / "logs" / "split_statistics.log"
    assert log_path.exists(), "Log file should be created"
    
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    assert len(lines) == 1, "Should have one log entry"
    
    entry = json.loads(lines[0])
    assert entry["type"] == "split_statistics"
    assert entry["statistics"] == test_stats

def test_log_multiple_entries(setup_mock_config, temp_project_root):
    """Test that multiple log entries are appended correctly."""
    from code.utils.logging import log_excluded_molecules, log_errors
    
    # First log
    log_excluded_molecules(3, ["CCO", "C1", "invalid"])
    
    # Second log
    log_errors([{"smiles": "bad1", "reason": "error"}])
    
    # Third log
    log_excluded_molecules(2, ["C2", "C3"])
    
    excluded_path = temp_project_root / "logs" / "excluded_molecules.log"
    errors_path = temp_project_root / "logs" / "ingestion_errors.log"
    
    with open(excluded_path, "r", encoding="utf-8") as f:
        excluded_lines = f.readlines()
    
    with open(errors_path, "r", encoding="utf-8") as f:
        error_lines = f.readlines()
    
    assert len(excluded_lines) == 2, "Should have two excluded molecule entries"
    assert len(error_lines) == 1, "Should have one error entry"