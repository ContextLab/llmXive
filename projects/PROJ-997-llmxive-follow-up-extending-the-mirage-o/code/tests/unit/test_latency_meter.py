import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np
import sys

# Ensure parent is in path
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.latency_meter import (
    LatencyMetrics,
    load_test_data,
    load_predictor,
    measure_proxy_policy_evaluation_time,
    measure_baseline_policy_evaluation_time,
    calculate_latency_reduction,
    write_metrics,
    run_latency_analysis
)

@pytest.fixture
def mock_test_data():
    return [
        {"input_id": "1", "gradient_norms": 0.5, "local_curvature": 0.2},
        {"input_id": "2", "gradient_norms": 0.6, "local_curvature": 0.3},
    ]

@pytest.fixture
def mock_baseline_metrics():
    return {
        "acceptance_rate": 0.8,
        "reasoning_score": 0.9,
        "timing_metadata": {
            "total_time": 100.0,
            "inference_only_time": 50.0
        }
    }

@pytest.fixture
def mock_predictor():
    mock = MagicMock()
    mock.predict.return_value = np.array([0.05, 0.06])
    return mock

def test_calculate_latency_reduction_success():
    """Test reduction calculation when proxy is much faster."""
    proxy_time = 5.0
    baseline_time = 50.0
    reduction, target_met = calculate_latency_reduction(proxy_time, baseline_time)
    
    # (50 - 5) / 50 * 100 = 90%
    assert abs(reduction - 90.0) < 1e-5
    assert target_met is True

def test_calculate_latency_reduction_below_target():
    """Test reduction calculation when proxy is not fast enough."""
    proxy_time = 20.0
    baseline_time = 50.0
    reduction, target_met = calculate_latency_reduction(proxy_time, baseline_time)
    
    # (50 - 20) / 50 * 100 = 60%
    assert abs(reduction - 60.0) < 1e-5
    assert target_met is False

def test_calculate_latency_reduction_zero_baseline():
    """Test that zero baseline time raises an error."""
    with pytest.raises(ValueError, match="Baseline time must be positive"):
        calculate_latency_reduction(1.0, 0.0)

def test_write_metrics(tmp_path):
    """Test writing metrics to JSON."""
    metrics = LatencyMetrics(
        proxy_prediction_time=5.0,
        baseline_inference_time=50.0,
        reduction_percentage=90.0,
        target_met=True
    )
    output_path = tmp_path / "latency_metrics.json"
    
    write_metrics(metrics, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['proxy_prediction_time'] == 5.0
    assert data['reduction_percentage'] == 90.0
    assert data['target_met'] is True

def test_measure_proxy_policy_evaluation_time(mock_predictor):
    """Test proxy time measurement."""
    samples = [
        {"gradient_norms": 0.1, "local_curvature": 0.1},
        {"gradient_norms": 0.2, "local_curvature": 0.2}
    ]
    
    # Mock time.perf_counter to ensure deterministic result or just check it runs
    with patch('src.services.latency_meter.time.perf_counter') as mock_time:
        mock_time.side_effect = [0.0, 0.1] # 0.1s elapsed
        
        duration = measure_proxy_policy_evaluation_time(samples, mock_predictor)
        
        assert duration == 0.1
        mock_predictor.predict.assert_called()

def test_measure_baseline_policy_evaluation_time(tmp_path, mock_baseline_metrics):
    """Test reading baseline time from file."""
    metrics_path = tmp_path / "baseline.json"
    with open(metrics_path, 'w') as f:
        json.dump(mock_baseline_metrics, f)
    
    time_val = measure_baseline_policy_evaluation_time(metrics_path)
    assert time_val == 50.0

def test_run_latency_analysis(tmp_path, mock_test_data, mock_baseline_metrics, mock_predictor):
    """Test full pipeline execution."""
    # Setup temp files
    test_path = tmp_path / "test.json"
    with open(test_path, 'w') as f:
        json.dump(mock_test_data, f)
    
    predictor_path = tmp_path / "predictor.pkl"
    with open(predictor_path, 'wb') as f:
        import pickle
        pickle.dump(mock_predictor, f)
    
    baseline_path = tmp_path / "baseline.json"
    with open(baseline_path, 'w') as f:
        json.dump(mock_baseline_metrics, f)
    
    output_path = tmp_path / "latency_result.json"
    
    with patch('src.services.latency_meter.time.perf_counter') as mock_time:
        mock_time.side_effect = [0.0, 0.1] # Proxy time 0.1s
        
        metrics = run_latency_analysis(
            test_data_path=test_path,
            predictor_path=predictor_path,
            baseline_metrics_path=baseline_path,
            output_path=output_path
        )
    
    assert metrics.baseline_inference_time == 50.0
    assert metrics.proxy_prediction_time == 0.1
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        result = json.load(f)
    assert result['target_met'] is True # (50-0.1)/50 > 90%
