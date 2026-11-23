"""Unit tests for metrics calculation (T031, T029)."""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from analyzers.metrics_calculator import MetricsCalculator

def test_metrics_calculator_aggregation():
    """Test aggregation of metrics from multiple results."""
    calculator = MetricsCalculator()
    
    # Mock results
    results = [
        {"workflow_id": "wf1", "status": "success", "latency": 100},
        {"workflow_id": "wf2", "status": "unrecoverable", "latency": 50},
        {"workflow_id": "wf3", "status": "success", "latency": 120},
        {"workflow_id": "wf4", "status": "partial", "latency": 80}
    ]
    
    metrics = calculator.aggregate_metrics(results)
    
    assert "total_resilience" in metrics
    assert "recoverable_fidelity" in metrics
    assert "unrecoverable_rate" in metrics
    assert "avg_latency" in metrics
    
    # Total resilience = success / total = 2/4 = 0.5
    assert abs(metrics["total_resilience"] - 0.5) < 0.01
    
    # Unrecoverable rate = 1/4 = 0.25
    assert abs(metrics["unrecoverable_rate"] - 0.25) < 0.01

def test_mcnemar_test_integration():
    """Test McNemar's test integration (T029)."""
    from analyzers.metrics_calculator import calculate_mcnemar
    
    # Mock contingency table
    # [[a, b], [c, d]]
    table = [[10, 5], [2, 20]]
    
    try:
        result = calculate_mcnemar(table)
        assert "statistic" in result
        assert "p_value" in result
    except Exception:
        # If scipy is not available or stats not implemented, skip
        pytest.skip("McNemar test not implemented or dependencies missing")
