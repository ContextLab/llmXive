"""
Unit tests for the latency_meter service (T030).
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np

from src.services.latency_meter import (
    LatencyMetrics,
    load_test_data,
    measure_proxy_policy_evaluation_time,
    measure_baseline_policy_evaluation_time,
    calculate_latency_reduction,
    write_metrics,
    run_latency_analysis
)

@pytest.fixture
def mock_test_data():
    return [
        {"input_id": "1", "gradient_norms": 0.5, "local_curvature": 0.2, "prompt": "test prompt 1"},
        {"input_id": "2", "gradient_norms": 0.6, "local_curvature": 0.3, "prompt": "test prompt 2"},
    ]

@pytest.fixture
def mock_baseline_metrics():
    return {"acceptance_rate": 0.8, "reasoning_score": 0.9}

@pytest.fixture
def mock_predictor():
    mock = MagicMock()
    mock.predict.return_value = np.array([0.1, 0.2])
    return mock

def test_calculate_latency_reduction_success():
    proxy_time = 0.1
    baseline_time = 1.0
    reduction, target_met = calculate_latency_reduction(proxy_time, baseline_time)
    
    assert reduction == 90.0
    assert target_met is True

def test_calculate_latency_reduction_below_target():
    proxy_time = 0.5
    baseline_time = 1.0
    reduction, target_met = calculate_latency_reduction(proxy_time, baseline_time)
    
    assert reduction == 50.0
    assert target_met is False

def test_calculate_latency_reduction_zero_baseline():
    with pytest.raises(ValueError):
        calculate_latency_reduction(0.1, 0.0)

def test_write_metrics(tmp_path):
    metrics = LatencyMetrics(
        proxy_policy_eval_time=0.1,
        baseline_policy_eval_time=1.0,
        reduction_percentage=90.0,
        target_met=True
    )
    
    output_path = tmp_path / "latency_metrics.json"
    write_metrics(metrics, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        data = json.load(f)
        
    assert data['proxy_policy_eval_time'] == 0.1
    assert data['baseline_policy_eval_time'] == 1.0
    assert data['reduction_percentage'] == 90.0
    assert data['target_met'] is True

@patch('src.services.latency_meter.joblib')
@patch('src.services.latency_meter.logger')
def test_measure_proxy_policy_evaluation_time(mock_logger, mock_joblib, mock_test_data, mock_predictor, tmp_path):
    predictor_path = tmp_path / "predictor.pkl"
    mock_joblib.load.return_value = mock_predictor
    
    # Create a dummy file so Path.exists() returns True
    predictor_path.touch()
    
    time_taken = measure_proxy_policy_evaluation_time(mock_test_data, str(predictor_path))
    
    assert time_taken > 0
    mock_predictor.predict.assert_called_once()

@patch('src.services.latency_meter.load_quantized_model')
@patch('src.services.latency_meter.logger')
def test_measure_baseline_policy_evaluation_time(mock_logger, mock_load_model, mock_test_data, mock_baseline_metrics, tmp_path):
    mock_model = MagicMock()
    mock_model.return_value = "response"
    mock_load_model.return_value = mock_model
    
    time_taken = measure_baseline_policy_evaluation_time(mock_test_data, mock_baseline_metrics)
    
    assert time_taken > 0
    assert mock_model.call_count == len(mock_test_data)

@patch('src.services.latency_meter.load_test_data')
@patch('src.services.latency_meter.measure_proxy_policy_evaluation_time')
@patch('src.services.latency_meter.measure_baseline_policy_evaluation_time')
@patch('src.services.latency_meter.write_metrics')
def test_run_latency_analysis(
    mock_write, 
    mock_measure_baseline, 
    mock_measure_proxy, 
    mock_load, 
    mock_test_data, 
    mock_baseline_metrics,
    tmp_path
):
    mock_load.return_value = (mock_test_data, mock_baseline_metrics)
    mock_measure_proxy.return_value = 0.1
    mock_measure_baseline.return_value = 1.0
    
    output_path = tmp_path / "latency_metrics.json"
    
    result = run_latency_analysis(
        test_parquet_path="dummy.parquet",
        predictor_path="dummy.pkl",
        baseline_metrics_path="dummy.json",
        output_path=str(output_path)
    )
    
    assert result.proxy_policy_eval_time == 0.1
    assert result.baseline_policy_eval_time == 1.0
    assert result.reduction_percentage == 90.0
    assert result.target_met is True
    mock_write.assert_called_once()