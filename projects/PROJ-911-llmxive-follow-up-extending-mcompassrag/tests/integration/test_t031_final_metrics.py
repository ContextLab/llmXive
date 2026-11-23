"""
Integration test for T031: Final Metrics Writer.

Verifies that final_metrics_writer.py correctly aggregates results from
previous tasks and writes valid output files.
"""

import json
import csv
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from code.config import RESULTS_DIR
from code.final_metrics_writer import (
    load_spearman_correlation_results,
    load_latency_metrics,
    load_recall_metrics,
    load_correlation_data_for_csv,
    write_metrics_json,
    write_correlation_csv,
    run_pipeline
)

# Create a temporary directory for test artifacts
@pytest.fixture
def temp_results_dir(tmp_path):
    """Create a temporary directory simulating RESULTS_DIR."""
    # Mock the RESULTS_DIR constant for the duration of the test
    with mock.patch('code.final_metrics_writer.RESULTS_DIR', tmp_path):
        yield tmp_path

@pytest.fixture
def mock_spearman_data(temp_results_dir):
    """Create mock Spearman correlation data file."""
    data = {
        "r": 0.75,
        "p_value": 0.001,
        "n_samples": 360,
        "method": "spearman"
    }
    file_path = temp_results_dir / 'spearman_results.json'
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return data

@pytest.fixture
def mock_latency_data(temp_results_dir):
    """Create mock latency metrics data file."""
    data = {
        "graph_latency_ms": 120.5,
        "neural_latency_ms": 450.2,
        "reduction_percent": 73.2,
        "status": "complete"
    }
    file_path = temp_results_dir / 'latency_metrics.json'
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return data

@pytest.fixture
def mock_recall_data(temp_results_dir):
    """Create mock recall metrics data file."""
    data = {
        "graph_recall_at_10": 0.65,
        "neural_recall_at_10": 0.72,
        "graph_recall_at_5": 0.55,
        "neural_recall_at_5": 0.60
    }
    file_path = temp_results_dir / 'recall_metrics.json'
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return data

@pytest.fixture
def mock_correlation_csv(temp_results_dir):
    """Create mock correlation data CSV file."""
    data = [
        {
            "query_id": "q1",
            "modularity": 0.45,
            "avg_path_length": 2.3,
            "degree_centrality_mean": 0.12,
            "betweenness_centrality_mean": 0.05,
            "recall_at_10": 0.65,
            "correlation_coefficient": 0.72
        },
        {
            "query_id": "q2",
            "modularity": 0.52,
            "avg_path_length": 2.1,
            "degree_centrality_mean": 0.15,
            "betweenness_centrality_mean": 0.07,
            "recall_at_10": 0.70,
            "correlation_coefficient": 0.68
        }
    ]
    file_path = temp_results_dir / 'correlation_data.csv'
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return data

def test_load_spearman_correlation_results(mock_spearman_data, temp_results_dir):
    """Test loading Spearman correlation results."""
    result = load_spearman_correlation_results()
    assert result is not None
    assert result['r'] == 0.75
    assert result['p_value'] == 0.001

def test_load_latency_metrics(mock_latency_data, temp_results_dir):
    """Test loading latency metrics."""
    result = load_latency_metrics()
    assert result is not None
    assert result['graph_latency_ms'] == 120.5
    assert result['reduction_percent'] == 73.2

def test_load_recall_metrics(mock_recall_data, temp_results_dir):
    """Test loading recall metrics."""
    result = load_recall_metrics()
    assert result is not None
    assert result['graph_recall_at_10'] == 0.65

def test_load_correlation_data_for_csv(mock_correlation_csv, temp_results_dir):
    """Test loading correlation data for CSV."""
    result = load_correlation_data_for_csv()
    assert len(result) == 2
    assert result[0]['query_id'] == 'q1'
    assert result[1]['correlation_coefficient'] == 0.68

def test_write_metrics_json_all_data_present(
    temp_results_dir, mock_spearman_data, mock_latency_data, mock_recall_data
):
    """Test writing metrics.json when all data is present."""
    write_metrics_json(mock_spearman_data, mock_latency_data, mock_recall_data)
    
    metrics_path = temp_results_dir / 'metrics.json'
    assert metrics_path.exists()
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    assert metrics['task_id'] == 'T031'
    assert metrics['spearman_correlation']['r'] == 0.75
    assert metrics['latency_reduction']['reduction_percent'] == 73.2
    assert metrics['recall_metrics']['graph_recall_at_10'] == 0.65
    assert metrics['summary']['hypothesis_supported'] is True  # r > 0.6

def test_write_metrics_json_missing_data(temp_results_dir):
    """Test writing metrics.json when data is missing."""
    write_metrics_json(None, None, None)
    
    metrics_path = temp_results_dir / 'metrics.json'
    assert metrics_path.exists()
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    assert metrics['spearman_correlation']['status'] == 'no_data'
    assert metrics['summary']['hypothesis_supported'] is False

def test_write_correlation_csv(temp_results_dir, mock_correlation_csv):
    """Test writing correlation CSV."""
    write_correlation_csv(mock_correlation_csv)
    
    csv_path = temp_results_dir / 'correlation.csv'
    assert csv_path.exists()
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]['query_id'] == 'q1'
    assert float(rows[0]['modularity']) == 0.45

def test_write_correlation_csv_empty_data(temp_results_dir):
    """Test writing correlation CSV with empty data."""
    write_correlation_csv([])
    
    csv_path = temp_results_dir / 'correlation.csv'
    assert csv_path.exists()
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Should have headers but no data rows
    assert len(rows) == 0

def test_run_pipeline_integration(
    temp_results_dir, mock_spearman_data, mock_latency_data, 
    mock_recall_data, mock_correlation_csv
):
    """Test the full pipeline execution."""
    run_pipeline()
    
    # Verify both output files exist
    metrics_path = temp_results_dir / 'metrics.json'
    csv_path = temp_results_dir / 'correlation.csv'
    
    assert metrics_path.exists()
    assert csv_path.exists()
    
    # Verify content
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    assert metrics['task_id'] == 'T031'
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2