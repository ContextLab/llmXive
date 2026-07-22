import pytest
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Import the functions to test
from parser import (
    compute_file_checksum,
    validate_data_source,
    parse_turn_data,
    extract_metrics_from_trajectory,
    parse_trajectories,
    extract_static_log_proxy
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_trajectory_file(temp_dir):
    """Create a sample trajectory file."""
    trajectory_data = {
        "trajectory_id": "test_traj_001",
        "turns": [
            {
                "turn_index": 0,
                "health": 100,
                "threat_level": 10,
                "deck_size": 20,
                "legal_moves": ["move_a", "move_b"],
                "move_probabilities": [0.6, 0.4]
            },
            {
                "turn_index": 1,
                "health": 90,
                "threat_level": 15,
                "deck_size": 18,
                "legal_moves": ["move_c"],
                "move_probabilities": [1.0]
            },
            {
                "turn_index": 2,
                "health": 80,
                "threat_level": 20,
                "deck_size": 15,
                "legal_moves": [],
                "move_probabilities": []
            }
        ]
    }
    
    file_path = temp_dir / "trajectory_test_traj_001.json"
    with open(file_path, 'w') as f:
        json.dump(trajectory_data, f)
    
    return file_path

@pytest.fixture
def sample_trajectory_file_uniform(temp_dir):
    """Create a sample trajectory file without explicit probabilities."""
    trajectory_data = {
        "trajectory_id": "test_traj_002",
        "turns": [
            {
                "turn_index": 0,
                "health": 100,
                "threat_level": 10,
                "deck_size": 20,
                "legal_moves": ["move_a", "move_b", "move_c"]
                # No move_probabilities - should default to uniform
            }
        ]
    }
    
    file_path = temp_dir / "trajectory_test_traj_002.json"
    with open(file_path, 'w') as f:
        json.dump(trajectory_data, f)
    
    return file_path

def test_compute_file_checksum(temp_dir):
    """Test SHA256 checksum computation."""
    test_file = temp_dir / "test.txt"
    test_content = "Hello, World!"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    checksum = compute_file_checksum(test_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)

def test_validate_data_source_no_files(temp_dir):
    """Test validation when no files exist."""
    with pytest.raises(FileNotFoundError):
        validate_data_source(temp_dir)

def test_validate_data_source_empty_file(temp_dir):
    """Test validation skips empty files."""
    empty_file = temp_dir / "empty.json"
    empty_file.touch()
    
    with pytest.raises(FileNotFoundError):
        validate_data_source(temp_dir)

def test_validate_data_source_valid_file(temp_dir, sample_trajectory_file):
    """Test validation with valid file."""
    files = validate_data_source(temp_dir)
    assert len(files) == 1
    assert sample_trajectory_file in files

def test_parse_turn_data_with_probabilities():
    """Test parsing turn data with explicit probabilities."""
    turn_data = {
        "turn_index": 0,
        "health": 100,
        "threat_level": 10,
        "deck_size": 20,
        "legal_moves": ["move_a", "move_b"],
        "move_probabilities": [0.6, 0.4]
    }
    
    metrics = parse_turn_data(turn_data)
    
    assert metrics['health'] == 100
    assert metrics['threat_level'] == 10
    assert metrics['deck_size'] == 20
    assert metrics['num_legal_moves'] == 2
    
    # Check move distribution is normalized
    dist = json.loads(metrics['move_distribution_json'])
    assert len(dist) == 2
    assert abs(sum(dist) - 1.0) < 1e-6
    assert abs(dist[0] - 0.6) < 1e-6
    assert abs(dist[1] - 0.4) < 1e-6

def test_parse_turn_data_uniform_probabilities():
    """Test parsing turn data without explicit probabilities (uniform)."""
    turn_data = {
        "turn_index": 0,
        "health": 100,
        "threat_level": 10,
        "deck_size": 20,
        "legal_moves": ["move_a", "move_b", "move_c"]
    }
    
    metrics = parse_turn_data(turn_data)
    
    assert metrics['num_legal_moves'] == 3
    
    # Check uniform distribution
    dist = json.loads(metrics['move_distribution_json'])
    assert len(dist) == 3
    assert abs(sum(dist) - 1.0) < 1e-6
    for p in dist:
        assert abs(p - 1/3) < 1e-6

def test_parse_turn_data_no_moves():
    """Test parsing turn data with no legal moves."""
    turn_data = {
        "turn_index": 0,
        "health": 100,
        "threat_level": 10,
        "deck_size": 20,
        "legal_moves": [],
        "move_probabilities": []
    }
    
    metrics = parse_turn_data(turn_data)
    
    assert metrics['num_legal_moves'] == 0
    assert metrics['move_distribution_json'] == json.dumps([])

def test_extract_metrics_from_trajectory(sample_trajectory_file):
    """Test extracting metrics from a trajectory file."""
    metrics = extract_metrics_from_trajectory(sample_trajectory_file)
    
    assert len(metrics) == 3  # 3 turns
    assert metrics[0]['turn_index'] == 0
    assert metrics[1]['turn_index'] == 1
    assert metrics[2]['turn_index'] == 2
    assert metrics[0]['trajectory_id'] == 'test_traj_001'

def test_parse_trajectories(temp_dir, sample_trajectory_file, sample_trajectory_file_uniform):
    """Test parsing multiple trajectory files to CSV."""
    output_file = temp_dir / "output.csv"
    
    parse_trajectories(temp_dir, output_file)
    
    assert output_file.exists()
    
    df = pd.read_csv(output_file)
    assert len(df) == 4  # 3 turns from first file + 1 from second
    assert 'trajectory_id' in df.columns
    assert 'turn_index' in df.columns
    assert 'health' in df.columns
    assert 'move_distribution_json' in df.columns

def test_extract_static_log_proxy(temp_dir, sample_trajectory_file):
    """Test extracting static log proxy."""
    output_csv = temp_dir / "metrics.csv"
    parse_trajectories(temp_dir, output_csv)
    
    proxy_output = temp_dir / "proxy.json"
    extract_static_log_proxy(output_csv, proxy_output)
    
    assert proxy_output.exists()
    
    with open(proxy_output, 'r') as f:
        proxy_data = json.load(f)
    
    assert len(proxy_data) > 0
    assert 'layer_id' in proxy_data[0]
    assert 'retrieval_frequency' in proxy_data[0]

def test_extract_static_log_proxy_with_validation_filter(temp_dir, sample_trajectory_file):
    """Test extracting static log proxy with validation ID filter."""
    output_csv = temp_dir / "metrics.csv"
    parse_trajectories(temp_dir, output_csv)
    
    proxy_output = temp_dir / "proxy_filtered.json"
    validation_ids = ['test_traj_001']
    extract_static_log_proxy(output_csv, proxy_output, validation_ids)
    
    assert proxy_output.exists()
    
    with open(proxy_output, 'r') as f:
        proxy_data = json.load(f)
    
    # Should only contain data from test_traj_001
    assert len(proxy_data) > 0
    assert all(item['retrieval_frequency'] > 0 for item in proxy_data)
