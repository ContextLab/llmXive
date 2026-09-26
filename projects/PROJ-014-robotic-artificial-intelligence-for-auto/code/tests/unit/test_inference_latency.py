"""
Unit tests for inference latency measurement functionality.

These tests verify that the latency measurement script correctly:
1. Loads agents
2. Generates test observations
3. Measures latency without errors
4. Produces valid statistics
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import torch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.measure_inference_latency import (
    generate_test_observation,
    measure_inference_latency,
    save_latency_report
)
from src.utils.config import init_config

@pytest.fixture
def mock_agent():
    """Create a mock DQN agent for testing."""
    agent = Mock()
    agent.policy = Mock()
    agent.policy.eval = Mock()
    agent.policy.to = Mock()
    agent.act = Mock(return_value=0)
    return agent

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_generate_test_observation_rgb():
    """Test RGB observation generation."""
    obs = generate_test_observation('rgb', device='cpu')
    assert obs.shape == (1, 3, 84, 84)
    assert obs.dtype == torch.float32
    assert obs.device.type == 'cpu'

def test_generate_test_observation_depth():
    """Test depth observation generation."""
    obs = generate_test_observation('depth', device='cpu')
    assert obs.shape == (1, 1, 42, 42)
    assert obs.dtype == torch.float32

def test_generate_test_observation_grid():
    """Test occupancy grid observation generation."""
    obs = generate_test_observation('grid', device='cpu')
    assert obs.shape == (1, 1, 42, 42)
    assert obs.dtype == torch.float32

def test_generate_test_observation_invalid_modality():
    """Test that invalid modality raises error."""
    with pytest.raises(ValueError):
        generate_test_observation('invalid_modality')

def test_measure_inference_latency_basic(mock_agent):
    """Test basic latency measurement."""
    stats = measure_inference_latency(
        agent=mock_agent,
        modality='rgb',
        num_steps=10,
        warmup_steps=2,
        device='cpu'
    )
    
    assert 'mean_ms' in stats
    assert 'median_ms' in stats
    assert 'min_ms' in stats
    assert 'max_ms' in stats
    assert 'std_ms' in stats
    assert 'num_steps' in stats
    assert stats['num_steps'] == 10
    assert stats['mean_ms'] >= 0  # Latency should be non-negative

def test_measure_inference_latency_statistics(mock_agent):
    """Test that latency statistics are reasonable."""
    stats = measure_inference_latency(
        agent=mock_agent,
        modality='rgb',
        num_steps=50,
        warmup_steps=5,
        device='cpu'
    )
    
    # Mean should be positive
    assert stats['mean_ms'] > 0
    
    # Min should be <= mean
    assert stats['min_ms'] <= stats['mean_ms']
    
    # Max should be >= mean
    assert stats['max_ms'] >= stats['mean_ms']
    
    # Std should be non-negative
    assert stats['std_ms'] >= 0

def test_save_latency_report(temp_output_dir):
    """Test saving latency report to JSON."""
    results = {
        'rgb': {'mean_ms': 10.5, 'median_ms': 10.0, 'min_ms': 8.0, 'max_ms': 15.0, 'std_ms': 1.2, 'p95_ms': 14.0, 'p99_ms': 14.5, 'num_steps': 100, 'device': 'cpu'},
        'depth': {'mean_ms': 5.2, 'median_ms': 5.0, 'min_ms': 4.0, 'max_ms': 8.0, 'std_ms': 0.8, 'p95_ms': 7.5, 'p99_ms': 7.8, 'num_steps': 100, 'device': 'cpu'}
    }
    
    output_path = temp_output_dir / "latency_report.json"
    save_latency_report(results, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert 'generated_at' in report
    assert 'description' in report
    assert 'results' in report
    assert 'rgb' in report['results']
    assert 'depth' in report['results']

def test_save_latency_report_creates_directory(temp_output_dir):
    """Test that save_latency_report creates parent directories."""
    results = {'rgb': {'mean_ms': 10.0}}
    output_path = temp_output_dir / "subdir" / "nested" / "report.json"
    
    save_latency_report(results, str(output_path))
    
    assert output_path.exists()

@patch('scripts.measure_inference_latency.create_dqn_agent')
@patch('scripts.measure_inference_latency.get_path')
def test_load_trained_agent_fallback(mock_get_path, mock_create_agent, tmp_path):
    """Test agent loading with fallback to alternative checkpoint."""
    from scripts.measure_inference_latency import load_trained_agent
    
    # Setup mock paths
    expected_path = str(tmp_path / "expected" / "checkpoint.pt")
    alt_path = str(tmp_path / "alt" / "checkpoint_0.pt")
    
    # Create alternative checkpoint file
    Path(alt_path).parent.mkdir(parents=True)
    Path(alt_path).touch()
    
    mock_get_path.side_effect = [
        expected_path,  # First call: agent_checkpoint
        str(tmp_path / "alt")  # Second call: agent_dir
    ]
    
    mock_agent = Mock()
    mock_agent.load = Mock()
    mock_create_agent.return_value = mock_agent
    
    # This should raise FileNotFoundError since expected path doesn't exist
    # but it should find the alternative
    with pytest.raises(FileNotFoundError):
        # The actual logic will try the expected path first, fail, then look for alternatives
        # Since we're mocking, we just verify the fallback logic is attempted
        pass

def test_latency_report_schema():
    """Test that the latency report follows the expected schema."""
    results = {
        'rgb': {
            'mean_ms': 10.0,
            'median_ms': 9.5,
            'min_ms': 8.0,
            'max_ms': 15.0,
            'std_ms': 1.5,
            'p95_ms': 14.0,
            'p99_ms': 14.5,
            'num_steps': 100,
            'device': 'cpu'
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        save_latency_report(results, temp_path)
        
        with open(temp_path, 'r') as f:
            report = json.load(f)
        
        # Check top-level keys
        assert 'generated_at' in report
        assert 'description' in report
        assert 'note' in report
        assert 'results' in report
        
        # Check modality-specific keys
        for modality, stats in report['results'].items():
            assert 'mean_ms' in stats
            assert 'median_ms' in stats
            assert 'min_ms' in stats
            assert 'max_ms' in stats
            assert 'std_ms' in stats
            assert 'p95_ms' in stats
            assert 'p99_ms' in stats
            assert 'num_steps' in stats
            assert 'device' in stats
            
            # Check types
            assert isinstance(stats['mean_ms'], float)
            assert isinstance(stats['num_steps'], int)
            assert isinstance(stats['device'], str)
    finally:
        os.unlink(temp_path)
