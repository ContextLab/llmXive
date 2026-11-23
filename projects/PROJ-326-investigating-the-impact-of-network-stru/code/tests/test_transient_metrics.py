"""
Unit tests for transient phase metric extraction (T027b).
"""
import pytest
import json
import numpy as np
import networkx as nx
from pathlib import Path
import tempfile

from code.src.simulation.metrics import (
    extract_transient_metrics,
    save_transient_metrics,
    compute_energy_density_profile,
    compute_spatial_variance
)


@pytest.fixture
def sample_history():
    """Create a sample history list for testing."""
    history = []
    nodes = 10
    graph = nx.erdos_renyi_graph(nodes, 0.3, seed=42)
    
    for step in range(20):
        spins = np.random.choice([-1, 1], size=nodes)
        energy_density = compute_energy_density_profile(spins, graph)
        variance = compute_spatial_variance(energy_density)
        
        history.append({
            "step": step,
            "spatial_variance": variance,
            "energy_density_profile": energy_density.tolist()
        })
    
    return history


def test_extract_transient_metrics_basic(sample_history):
    """Test basic extraction of transient metrics."""
    transient_steps = 5
    result = extract_transient_metrics(sample_history, transient_steps)
    
    assert result["transient_steps"] == transient_steps
    assert result["steps_analyzed"] == transient_steps
    assert "spatial_variance" in result
    assert "mean" in result["spatial_variance"]
    assert "std" in result["spatial_variance"]
    assert "min" in result["spatial_variance"]
    assert "max" in result["spatial_variance"]
    assert len(result["raw_transient_data"]) == transient_steps


def test_extract_transient_metrics_empty_history():
    """Test extraction with empty history."""
    result = extract_transient_metrics([], 10)
    
    assert result["steps_analyzed"] == 0
    assert result["spatial_variance"]["mean"] == 0.0
    assert len(result["raw_transient_data"]) == 0


def test_extract_transient_metrics_no_transient_data(sample_history):
    """Test extraction when transient_steps is 0 or no matching steps."""
    result = extract_transient_metrics(sample_history, 0)
    
    assert result["steps_analyzed"] == 0
    assert len(result["raw_transient_data"]) == 0


def test_extract_transient_metrics_larger_than_history(sample_history):
    """Test extraction when transient_steps exceeds history length."""
    result = extract_transient_metrics(sample_history, 100)
    
    assert result["steps_analyzed"] == len(sample_history)
    assert len(result["raw_transient_data"]) == len(sample_history)


def test_save_transient_metrics(tmp_path):
    """Test saving transient metrics to a file."""
    history = [
        {"step": 0, "spatial_variance": 1.0, "energy_density_profile": [1, 2]},
        {"step": 1, "spatial_variance": 2.0, "energy_density_profile": [3, 4]}
    ]
    result = extract_transient_metrics(history, 5)
    
    output_file = tmp_path / "transient_test.json"
    save_transient_metrics(result, str(output_file))
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded["steps_analyzed"] == 2
    assert loaded["spatial_variance"]["mean"] == 1.5


def test_extract_transient_metrics_statistics_accuracy(sample_history):
    """Verify that the calculated statistics are mathematically correct."""
    transient_steps = 5
    result = extract_transient_metrics(sample_history, transient_steps)
    
    variances = [entry["spatial_variance"] for entry in result["raw_transient_data"]]
    
    expected_mean = np.mean(variances)
    expected_std = np.std(variances)
    expected_min = np.min(variances)
    expected_max = np.max(variances)
    
    assert abs(result["spatial_variance"]["mean"] - expected_mean) < 1e-6
    assert abs(result["spatial_variance"]["std"] - expected_std) < 1e-6
    assert abs(result["spatial_variance"]["min"] - expected_min) < 1e-6
    assert abs(result["spatial_variance"]["max"] - expected_max) < 1e-6