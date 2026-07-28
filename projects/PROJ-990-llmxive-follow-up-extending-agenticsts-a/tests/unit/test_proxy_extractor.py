"""
Unit tests for code/proxy_extractor.py (T007c).
"""

import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from code.proxy_extractor import (
    load_validation_ids,
    load_metrics_master,
    extract_static_proxy,
    save_proxy_json,
    main
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_validation_ids_file(temp_dir):
    """Create a mock validation_set_ids.json file."""
    file_path = temp_dir / "validation_set_ids.json"
    data = ["traj_001", "traj_002", "traj_003"]
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

@pytest.fixture
def mock_metrics_file(temp_dir):
    """Create a mock metrics_with_moves.csv file."""
    file_path = temp_dir / "metrics_with_moves.csv"
    data = {
        "trajectory_id": ["traj_001", "traj_001", "traj_001", "traj_002", "traj_002", "traj_003", "traj_004"],
        "layer_id": ["layer_A", "layer_B", "layer_A", "layer_A", "layer_B", "layer_C", "layer_A"],
        "health_ratio": [0.5, 0.6, 0.7, 0.8, 0.9, 0.4, 0.5],
        "threat_level": [1, 2, 1, 3, 2, 1, 1],
        "deck_size": [10, 10, 10, 10, 10, 10, 10],
        "move_entropy": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return file_path

def test_load_validation_ids_success(mock_validation_ids_file, temp_dir):
    """Test successful loading of validation IDs."""
    # Mock the global path
    with patch('code.proxy_extractor.VALIDATION_IDS_FILE', mock_validation_ids_file):
        ids = load_validation_ids()
        assert ids == ["traj_001", "traj_002", "traj_003"]

def test_load_validation_ids_missing_file(temp_dir):
    """Test error when validation IDs file is missing."""
    missing_path = temp_dir / "nonexistent.json"
    with patch('code.proxy_extractor.VALIDATION_IDS_FILE', missing_path):
        with pytest.raises(FileNotFoundError):
            load_validation_ids()

def test_load_validation_ids_empty(temp_dir):
    """Test error when validation IDs file is empty."""
    file_path = temp_dir / "empty.json"
    with open(file_path, 'w') as f:
        json.dump([], f)
    
    with patch('code.proxy_extractor.VALIDATION_IDS_FILE', file_path):
        with pytest.raises(ValueError, match="empty or invalid"):
            load_validation_ids()

def test_load_metrics_master_success(mock_metrics_file, temp_dir):
    """Test successful loading of metrics master."""
    with patch('code.proxy_extractor.METRICS_FILE', mock_metrics_file):
        df = load_metrics_master()
        assert len(df) == 7
        assert 'trajectory_id' in df.columns
        assert 'layer_id' in df.columns

def test_load_metrics_master_missing_file(temp_dir):
    """Test error when metrics file is missing."""
    missing_path = temp_dir / "nonexistent.csv"
    with patch('code.proxy_extractor.METRICS_FILE', missing_path):
        with pytest.raises(FileNotFoundError):
            load_metrics_master()

def test_extract_static_proxy_logic(mock_metrics_file, mock_validation_ids_file, temp_dir):
    """Test the core logic of proxy extraction."""
    # Setup
    with patch('code.proxy_extractor.METRICS_FILE', mock_metrics_file):
        with patch('code.proxy_extractor.VALIDATION_IDS_FILE', mock_validation_ids_file):
            metrics_df = load_metrics_master()
            validation_ids = load_validation_ids()
            
            result = extract_static_proxy(metrics_df, validation_ids)
            
            # Expected:
            # traj_001: 3 turns (A, B, A) -> A: 2/3, B: 1/3
            # traj_002: 2 turns (A, B) -> A: 1/2, B: 1/2
            # traj_003: 1 turn (C) -> C: 1/1
            # traj_004 is NOT in validation set, so should be excluded.
            
            assert len(result) == 5  # 2 for traj_001, 2 for traj_002, 1 for traj_003
            
            # Verify specific scores
            scores = { (r['trajectory_id'], r['layer_id']): r['utility_score'] for r in result }
            
            assert abs(scores[('traj_001', 'layer_A')] - 2/3) < 0.001
            assert abs(scores[('traj_001', 'layer_B')] - 1/3) < 0.001
            assert abs(scores[('traj_002', 'layer_A')] - 0.5) < 0.001
            assert abs(scores[('traj_002', 'layer_B')] - 0.5) < 0.001
            assert abs(scores[('traj_003', 'layer_C')] - 1.0) < 0.001
            
            # Ensure traj_004 is not present
            assert ('traj_004', 'layer_A') not in scores

def test_extract_static_proxy_no_match(mock_metrics_file, temp_dir):
    """Test extraction when no IDs match."""
    # Create a validation file with IDs not in metrics
    file_path = temp_dir / "validation_ids.json"
    with open(file_path, 'w') as f:
        json.dump(["traj_999"], f)
    
    with patch('code.proxy_extractor.METRICS_FILE', mock_metrics_file):
        with patch('code.proxy_extractor.VALIDATION_IDS_FILE', file_path):
            metrics_df = load_metrics_master()
            validation_ids = load_validation_ids()
            result = extract_static_proxy(metrics_df, validation_ids)
            
            assert result == []

def test_save_proxy_json(temp_dir):
    """Test saving proxy data to JSON."""
    data = [
        {"trajectory_id": "t1", "layer_id": "l1", "utility_score": 0.5},
        {"trajectory_id": "t1", "layer_id": "l2", "utility_score": 0.5}
    ]
    output_path = temp_dir / "test_proxy.json"
    
    save_proxy_json(data, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    
    assert len(loaded) == 2
    assert loaded[0]['trajectory_id'] == 't1'