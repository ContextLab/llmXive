"""
Unit tests for aggregate_metrics.py
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from cli.aggregate_metrics import load_raw_logs, aggregate_metrics, write_aggregated_csv

def test_load_raw_logs_empty_directory():
    """Test loading from an empty directory raises FileNotFoundError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            load_raw_logs(Path(tmpdir))

def test_load_raw_logs_valid():
    """Test loading valid JSONL logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.jsonl"
        data = [
            {"config_hash": "abc123", "coherence_score": 0.8, "step_latency": 10.0},
            {"config_hash": "abc123", "coherence_score": 0.9, "step_latency": 12.0},
            {"config_hash": "def456", "coherence_score": 0.5, "step_latency": 20.0}
        ]
        with open(log_file, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        
        records = load_raw_logs(Path(tmpdir))
        assert len(records) == 3
        assert records[0]['config_hash'] == "abc123"
        assert '_source_file' in records[0]

def test_aggregate_metrics_basic():
    """Test basic aggregation logic."""
    records = [
        {"config_hash": "abc123", "coherence_score": 0.8, "diversity_score": 0.4, "step_latency": 10.0, "model_type": "CA"},
        {"config_hash": "abc123", "coherence_score": 0.8, "diversity_score": 0.4, "step_latency": 10.0, "model_type": "CA"},
        {"config_hash": "def456", "coherence_score": 0.5, "diversity_score": 0.6, "step_latency": 20.0, "model_type": "Neural"}
    ]
    
    aggregated = aggregate_metrics(records)
    
    assert len(aggregated) == 2
    
    # Find the CA group
    ca_group = next((g for g in aggregated if g['config_hash'] == "abc123"), None)
    assert ca_group is not None
    assert ca_group['coherence_mean'] == 0.8
    assert ca_group['coherence_std'] == 0.0
    assert ca_group['total_steps'] == 2
    assert ca_group['model_type'] == "CA"

def test_aggregate_metrics_missing_values():
    """Test aggregation handles missing metric values gracefully."""
    records = [
        {"config_hash": "abc123", "coherence_score": 0.8, "step_latency": 10.0},
        {"config_hash": "abc123", "step_latency": 12.0}, # Missing coherence
        {"config_hash": "abc123", "coherence_score": 0.9} # Missing latency
    ]
    
    aggregated = aggregate_metrics(records)
    assert len(aggregated) == 1
    # Coherence should have count 2, Latency count 2
    assert aggregated[0]['coherence_mean'] is not None
    assert aggregated[0]['latency_mean_ms'] is not None

def test_write_aggregated_csv(tmp_path):
    """Test writing aggregated data to CSV."""
    aggregated = [
        {
            'config_key': 'abc123',
            'config_hash': 'abc123',
            'coherence_mean': 0.8,
            'latency_mean_ms': 10.0,
            'total_steps': 100
        }
    ]
    
    output_file = tmp_path / "test_agg.csv"
    write_aggregated_csv(aggregated, output_file)
    
    assert output_file.exists()
    content = output_file.read_text()
    assert 'config_key' in content
    assert 'abc123' in content
    assert '0.8' in content