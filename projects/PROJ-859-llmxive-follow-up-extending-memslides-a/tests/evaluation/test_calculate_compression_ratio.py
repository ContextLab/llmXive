"""
Tests for calculate_compression_ratio.py
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.calculate_compression_ratio import CompressionRatioCalculator, calculate_compression_ratios
from config import get_config


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock config with necessary paths."""
    processed_dir = tmp_path / "processed"
    rules_dir = processed_dir / "rules"
    sweeps_dir = rules_dir / "sweeps"
    held_out_dir = tmp_path / "held_out"
    
    processed_dir.mkdir(parents=True)
    rules_dir.mkdir()
    sweeps_dir.mkdir()
    held_out_dir.mkdir()

    return {
        'data_paths': {
            'processed': str(processed_dir),
            'held_out': str(held_out_dir)
        },
        'seed': 42,
        'sweep_sample_size': 10
    }


@pytest.fixture
def mock_sweep_files(mock_config):
    """Create mock sweep rule files."""
    sweeps_dir = Path(mock_config['data_paths']['processed']) / 'rules' / 'sweeps'
    
    # Create a few mock rule sets
    for i, thresh in enumerate([0.1, 0.5, 0.9]):
        rules = [{'id': j, 'support': i} for j in range(10 - i)] # Varying sizes
        data = {
            'threshold': thresh,
            'rules': rules,
            'original_rule_count': 10
        }
        with open(sweeps_dir / f"rules_thresh_{i}.json", 'w') as f:
            json.dump(data, f)

    # Create global rules
    global_rules_path = Path(mock_config['data_paths']['processed']) / 'rules' / 'global_rules.json'
    with open(global_rules_path, 'w') as f:
        json.dump({'rules': [{'id': j} for j in range(10)]}, f)


@pytest.fixture
def mock_held_out_traces(mock_config):
    """Create mock held-out traces."""
    held_out_dir = Path(mock_config['data_paths']['held_out'])
    
    # Create 10 mock traces
    for i in range(10):
        trace_data = {
            'trace_id': f'trace_{i}',
            'exact_tool_sequence': [f'tool_{j}' for j in range(3)],
            'final_state': {'slide_id': i}
        }
        with open(held_out_dir / f'session_{i}.json', 'w') as f:
            json.dump(trace_data, f)


def test_calculator_initialization(mock_config):
    """Test that the calculator initializes correctly."""
    calc = CompressionRatioCalculator(mock_config)
    assert calc.config == mock_config
    assert calc.output_path.exists() is False # File created on save
    assert calc.output_path.parent.exists()


def test_load_sweep_results(mock_config, mock_sweep_files):
    """Test loading sweep results."""
    calc = CompressionRatioCalculator(mock_config)
    results = calc.load_sweep_results()
    
    assert len(results) == 3
    assert all('threshold' in r for r in results)
    assert all('rules' in r for r in results)


def test_load_sample_traces(mock_config, mock_held_out_traces):
    """Test loading sample traces."""
    calc = CompressionRatioCalculator(mock_config)
    traces = calc.load_sample_traces(sample_size=5)
    
    assert len(traces) == 5
    assert all('trace_id' in t for t in traces)


def test_compression_ratio_calculation():
    """Test the compression ratio math."""
    calc = CompressionRatioCalculator({})
    
    assert calc.calculate_compression_ratio(100, 50) == 0.5
    assert calc.calculate_compression_ratio(100, 100) == 1.0
    assert calc.calculate_compression_ratio(100, 0) == 0.0
    assert calc.calculate_compression_ratio(0, 0) == 1.0 # Edge case


@patch('evaluation.calculate_compression_ratio.CompressedAgent')
def test_run_agent_evaluation(mock_agent_class, mock_config, mock_held_out_traces):
    """Test running the agent evaluation."""
    # Mock the agent instance
    mock_agent = MagicMock()
    mock_agent_class.return_value = mock_agent
    
    # Mock the run method to return a successful result
    mock_trace = {
        'trace_id': 'test',
        'exact_tool_sequence': ['tool_a', 'tool_b'],
        'final_state': {}
    }
    mock_agent.run.return_value = {
        'edit_sequence': ['tool_a', 'tool_b']
    }
    
    calc = CompressionRatioCalculator(mock_config)
    accuracy, count = calc.run_agent_evaluation(mock_agent, [mock_trace])
    
    assert accuracy == 1.0
    assert count == 1


@patch('evaluation.calculate_compression_ratio.CompressedAgent')
def test_calculate_trade_off(mock_agent_class, mock_config, mock_sweep_files, mock_held_out_traces):
    """Test the full trade-off calculation flow."""
    # Mock the agent
    mock_agent = MagicMock()
    mock_agent_class.return_value = mock_agent
    
    # Mock run to always succeed for baseline and fail for pruned (to simulate loss)
    mock_agent.run.side_effect = [
        {'edit_sequence': ['tool_a', 'tool_b']}, # Baseline success
        {'edit_sequence': ['tool_a', 'tool_b']}, # Pruned success (100% fidelity)
        {'edit_sequence': ['tool_a']},          # Pruned failure
    ]
    
    calc = CompressionRatioCalculator(mock_config)
    results = calc.calculate_trade_off()
    
    assert len(results) > 0
    assert 'threshold' in results[0]
    assert 'compression_ratio' in results[0]
    assert 'fidelity_loss' in results[0]


def test_save_results(mock_config, mock_sweep_files, mock_held_out_traces):
    """Test saving results to CSV."""
    calc = CompressionRatioCalculator(mock_config)
    
    # Mock the calculate_trade_off to return known data
    mock_results = [
        {'threshold': 0.1, 'compression_ratio': 0.5, 'fidelity_loss': 0.0},
        {'threshold': 0.5, 'compression_ratio': 0.2, 'fidelity_loss': 0.1}
    ]
    
    calc.save_results(mock_results)
    
    assert calc.output_path.exists()
    
    # Read and verify
    with open(calc.output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 2
    assert rows[0]['threshold'] == '0.1'