import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
import math

from parser import parse_turn_data, extract_metrics_from_trajectory, parse_trajectories, validate_data_source

def test_parse_turn_data_basic():
    data = {
        "turn": 0,
        "health": 100,
        "max_health": 100,
        "threat_level": 5,
        "deck_size": 50,
        "legal_moves": ["a", "b", "c"]
    }
    result = parse_turn_data(data)
    
    assert result['turn'] == 0
    assert result['health_ratio'] == 1.0
    assert result['threat_level'] == 5
    assert result['deck_size'] == 50
    # Entropy for 3 moves: log(3)
    expected_entropy = math.log(3)
    assert abs(result['move_entropy'] - expected_entropy) < 1e-6

def test_parse_turn_data_single_move():
    data = {
        "turn": 1,
        "health": 50,
        "max_health": 100,
        "threat_level": 10,
        "deck_size": 40,
        "legal_moves": ["only_move"]
    }
    result = parse_turn_data(data)
    
    assert result['health_ratio'] == 0.5
    assert result['move_entropy'] == 0.0 # log(1) = 0

def test_parse_turn_data_no_moves():
    data = {
        "turn": 2,
        "health": 10,
        "max_health": 100,
        "threat_level": 100,
        "deck_size": 0,
        "legal_moves": []
    }
    result = parse_turn_data(data)
    
    assert result['move_entropy'] == 0.0

def test_extract_metrics_from_trajectory():
    trajectory = {
        "trajectory_id": "test_001",
        "turns": [
            {
                "turn": 0,
                "health": 100,
                "max_health": 100,
                "threat_level": 0,
                "deck_size": 50,
                "legal_moves": ["a", "b"]
            },
            {
                "turn": 1,
                "health": 80,
                "max_health": 100,
                "threat_level": 5,
                "deck_size": 49,
                "legal_moves": ["c"]
            }
        ]
    }
    
    metrics = extract_metrics_from_trajectory(trajectory)
    
    assert len(metrics) == 2
    assert metrics[0]['trajectory_id'] == "test_001"
    assert metrics[0]['turn'] == 0
    assert metrics[0]['move_entropy'] == math.log(2)
    
    assert metrics[1]['trajectory_id'] == "test_001"
    assert metrics[1]['turn'] == 1
    assert metrics[1]['move_entropy'] == 0.0

def test_parse_trajectories_integration(tmp_path):
    # Create sample data
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    output_path = tmp_path / "data" / "processed" / "metrics_with_moves.csv"
    
    sample_data = [
        {
            "trajectory_id": "t1",
            "turns": [
                {"turn": 0, "health": 100, "max_health": 100, "threat_level": 0, "deck_size": 50, "legal_moves": ["a", "b", "c", "d"]}
            ]
        }
    ]
    
    with open(raw_dir / "test.json", 'w') as f:
        json.dump(sample_data, f)
    
    parse_trajectories(raw_dir, output_path)
    
    assert output_path.exists()
    df = pd.read_csv(output_path)
    
    assert len(df) == 1
    assert df['trajectory_id'].iloc[0] == "t1"
    # Entropy for 4 moves: log(4)
    assert abs(df['move_entropy'].iloc[0] - math.log(4)) < 1e-6
    assert list(df.columns) == ['trajectory_id', 'turn', 'health_ratio', 'threat_level', 'deck_size', 'move_entropy']

def test_validate_data_source_missing():
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(FileNotFoundError):
            validate_data_source(Path(tmp_dir) / "nonexistent")

def test_validate_data_source_empty_files(tmp_path):
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "empty.json").touch()
    
    with pytest.raises(FileNotFoundError):
        validate_data_source(raw_dir)