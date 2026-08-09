import json
import os
import tempfile
import random
import pytest
from unittest.mock import patch, mock_open

from sampling import (
    load_comparison_logs,
    filter_wasted_calls,
    load_sample_config,
    select_simple_random_sample,
    run_sampling_pipeline
)
from config import get_config

@pytest.fixture
def mock_logs():
    return [
        {"pair_id": "p1", "cosine_sim": 0.98, "doc1_id": "d1", "doc2_id": "d2"},
        {"pair_id": "p2", "cosine_sim": 0.85, "doc1_id": "d3", "doc2_id": "d4"},
        {"pair_id": "p3", "cosine_sim": 0.99, "doc1_id": "d5", "doc2_id": "d6"},
        {"pair_id": "p4", "cosine_sim": 0.50, "doc1_id": "d7", "doc2_id": "d8"},
        {"pair_id": "p5", "cosine_sim": 0.96, "doc1_id": "d9", "doc2_id": "d10"},
    ]

@pytest.fixture
def temp_log_file(mock_logs):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        for item in mock_logs:
            f.write(json.dumps(item) + '\n')
        return f.name

@pytest.fixture
def temp_config_file():
    config = {
        "total_flagged_count": 100,
        "sample_size": 2,
        "skip_validation": False
    }
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(config, f)
        return f.name

def test_filter_wasted_calls(mock_logs):
    flagged = filter_wasted_calls(mock_logs, threshold=0.95)
    assert len(flagged) == 3
    assert all(item['cosine_sim'] > 0.95 for item in flagged)
    assert {item['pair_id'] for item in flagged} == {'p1', 'p3', 'p5'}

def test_filter_wasted_calls_empty(mock_logs):
    flagged = filter_wasted_calls(mock_logs, threshold=0.99)
    assert len(flagged) == 1
    assert flagged[0]['pair_id'] == 'p3'

def test_select_simple_random_sample():
    items = [{"id": i} for i in range(100)]
    sample_size = 10
    seed = 42
    
    sampled, indices = select_simple_random_sample(items, sample_size, seed)
    
    assert len(sampled) == sample_size
    assert len(indices) == sample_size
    assert all(0 <= idx < 100 for idx in indices)
    assert len(set(indices)) == sample_size  # No duplicates
    
    # Verify reproducibility
    sampled2, indices2 = select_simple_random_sample(items, sample_size, seed)
    assert indices == indices2

def test_select_simple_random_sample_all():
    items = [{"id": i} for i in range(5)]
    sampled, indices = select_simple_random_sample(items, 10, 42)
    assert len(sampled) == 5
    assert indices == [0, 1, 2, 3, 4]

def test_run_sampling_pipeline(tmp_path, mock_logs, temp_config_file):
    # Setup temp log file
    log_path = tmp_path / "comparison_log.json"
    with open(log_path, 'w') as f:
        for item in mock_logs:
            f.write(json.dumps(item) + '\n')
    
    output_path = tmp_path / "consensus_sample.json"
    
    # Mock get_config to return a specific seed
    with patch('sampling.get_config') as mock_get_config:
        mock_get_config.return_value = {"RANDOM_SEED": 42}
        
        result = run_sampling_pipeline(
            log_path=str(log_path),
            config_path=temp_config_file,
            output_path=str(output_path)
        )
    
    assert result['status'] == 'completed'
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'sample_indices' in data
    assert 'sample_size' in data
    assert data['sample_size'] == 2
    assert 'pair_ids' in data
    assert len(data['pair_ids']) == 2

def test_run_sampling_pipeline_skip_validation(tmp_path, mock_logs):
    log_path = tmp_path / "comparison_log.json"
    with open(log_path, 'w') as f:
        for item in mock_logs:
            f.write(json.dumps(item) + '\n')
    
    config = {"sample_size": 2, "skip_validation": True}
    config_path = tmp_path / "sample_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f)
    
    output_path = tmp_path / "consensus_sample.json"
    
    with patch('sampling.get_config') as mock_get_config:
        mock_get_config.return_value = {"RANDOM_SEED": 42}
        
        result = run_sampling_pipeline(
            log_path=str(log_path),
            config_path=str(config_path),
            output_path=str(output_path)
        )
    
    assert result['status'] == 'skipped'
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        assert json.load(f) == []

def test_run_sampling_pipeline_no_flagged(tmp_path):
    # Create a log with no flagged pairs
    log_path = tmp_path / "comparison_log.json"
    logs = [
        {"pair_id": "p1", "cosine_sim": 0.80},
        {"pair_id": "p2", "cosine_sim": 0.90},
    ]
    with open(log_path, 'w') as f:
        for item in logs:
            f.write(json.dumps(item) + '\n')
    
    config = {"sample_size": 2, "skip_validation": False}
    config_path = tmp_path / "sample_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f)
    
    output_path = tmp_path / "consensus_sample.json"
    
    with patch('sampling.get_config') as mock_get_config:
        mock_get_config.return_value = {"RANDOM_SEED": 42}
        
        result = run_sampling_pipeline(
            log_path=str(log_path),
            config_path=str(config_path),
            output_path=str(output_path)
        )
    
    assert result['status'] == 'completed'
    assert result['total_flagged'] == 0
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        assert json.load(f) == []
