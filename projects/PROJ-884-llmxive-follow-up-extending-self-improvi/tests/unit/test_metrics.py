"""
Unit tests for code/analysis/metrics.py
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from code.analysis.metrics import (
    load_experiment_logs,
    calculate_metrics_from_logs,
    save_metrics_to_csv,
    ExperimentMetrics
)

@pytest.fixture
def sample_logs():
    return [
        {"experiment_id": "exp_001", "success": True, "wall_clock": 10.0, "method": "symbolic"},
        {"experiment_id": "exp_001", "success": True, "wall_clock": 12.0, "method": "symbolic"},
        {"experiment_id": "exp_001", "success": False, "wall_clock": 15.0, "method": "symbolic"},
        {"experiment_id": "exp_001", "success": True, "wall_clock": 11.0, "method": "neural"},
    ]

@pytest.fixture
def temp_log_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test_log.json"
        logs = [
            {"success": True, "wall_clock": 5.0, "method": "test"},
            {"success": False, "wall_clock": 8.0, "method": "test"}
        ]
        with open(log_file, 'w') as f:
            json.dump(logs, f)
        yield tmpdir

def test_load_experiment_logs(temp_log_dir):
    logs = load_experiment_logs(temp_log_dir)
    assert len(logs) == 2
    assert logs[0]['success'] is True

def test_calculate_metrics_from_logs_success_rate(sample_logs):
    metrics = calculate_metrics_from_logs(sample_logs, method="symbolic")
    # Only symbolic logs should be counted if we filter, but the function takes all
    # The function calculates based on the list passed.
    # 3 symbolic logs: 2 success, 1 fail -> 66.6%
    # But the function doesn't filter by method internally, it just labels the result.
    # Let's test with only symbolic logs
    symbolic_logs = [l for l in sample_logs if l['method'] == 'symbolic']
    metrics = calculate_metrics_from_logs(symbolic_logs, method="symbolic")
    
    assert metrics.total_runs == 3
    assert metrics.successful_runs == 2
    assert abs(metrics.success_rate - 2/3) < 0.001

def test_calculate_metrics_from_logs_energy(sample_logs):
    # With 3 symbolic logs: 10, 12, 15 seconds
    # Power assumed 65W
    symbolic_logs = [l for l in sample_logs if l['method'] == 'symbolic']
    metrics = calculate_metrics_from_logs(symbolic_logs, method="symbolic")
    
    total_time = 10 + 12 + 15
    expected_energy = total_time * 65.0
    
    assert abs(metrics.total_energy_joules - expected_energy) < 0.001
    assert abs(metrics.avg_energy_joules - (expected_energy / 3)) < 0.001

def test_save_metrics_to_csv(sample_logs):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metrics.csv"
        metrics = calculate_metrics_from_logs(sample_logs, method="test")
        save_metrics_to_csv([metrics], str(output_path))
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
            assert "experiment_id" in content
            assert "success_rate" in content
            assert "0.75" in content or "0.7500" in content # 3/4 success in full list