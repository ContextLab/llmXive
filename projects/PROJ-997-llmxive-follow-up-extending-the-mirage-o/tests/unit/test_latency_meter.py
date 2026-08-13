import pytest
import numpy as np
from unittest.mock import patch, MagicMock, mock_open
import json
import time
from pathlib import Path

from src.services.latency_meter import (
    LatencyMetrics,
    measure_policy_evaluation_latency,
    measure_quantized_inference_latency,
    run_latency_comparison,
    main
)

@pytest.fixture
def mock_ridge_model():
    model = MagicMock()
    model.predict = MagicMock(return_value=np.array([0.5, 0.6, 0.7]))
    return model

@pytest.fixture
def sample_features():
    return [np.array([1.0, 2.0]), np.array([1.1, 2.1]), np.array([1.2, 2.2])]

@pytest.fixture
def sample_prompts():
    return ["prompt 1", "prompt 2", "prompt 3"]

def test_measure_policy_evaluation_latency(mock_ridge_model, sample_features):
    """Test that policy evaluation latency is measured correctly."""
    with patch('time.perf_counter') as mock_time:
        # Simulate start and end times
        mock_time.side_effect = [0.0, 1.0] # 1 second duration per run
        
        # Run 2 times
        result = measure_policy_evaluation_latency(mock_ridge_model, sample_features, num_runs=2)
        
        assert result == 0.5 # 1.0 second / 2 runs
        assert mock_ridge_model.predict.call_count == 2

def test_measure_policy_evaluation_latency_empty_features(mock_ridge_model):
    """Test behavior with empty feature list."""
    with patch('src.services.latency_meter.logger') as mock_logger:
        result = measure_policy_evaluation_latency(mock_ridge_model, [], num_runs=1)
        assert result == 0.0
        mock_logger.warning.assert_called_once()

def test_run_latency_comparison_creates_file(tmp_path, mock_ridge_model, sample_features, sample_prompts):
    """Test that run_latency_comparison writes the correct JSON file."""
    output_path = tmp_path / "latency_metrics.json"
    
    # Mock the quantized inference function to return instantly
    with patch('src.services.latency_meter.load_quantized_model') as mock_load:
        with patch('src.services.latency_meter.run_quantized_inference') as mock_run:
            with patch('joblib.load', return_value=mock_ridge_model):
                # Mock time to ensure we get predictable values
                with patch('time.perf_counter') as mock_time:
                    # Proxy: 0.1s, Baseline: 1.0s
                    mock_time.side_effect = [0.0, 0.1, 1.0, 2.0] # 2 runs for baseline (1s each), 1 run for proxy (0.1s)
                    
                    metrics = run_latency_comparison(
                        feature_vectors=sample_features,
                        prompts=sample_prompts,
                        model_path="fake_model.gguf",
                        predictor_path="fake_predictor.pkl",
                        quantization_level="INT4",
                        output_path=str(output_path)
                    )
                    
                    assert isinstance(metrics, LatencyMetrics)
                    assert metrics.sample_count == 3
                    assert metrics.reduction_percentage > 0
                    
                    # Verify file was written
                    assert output_path.exists()
                    with open(output_path, 'r') as f:
                        data = json.load(f)
                    
                    assert 'proxy_time' in data
                    assert 'baseline_time' in data
                    assert 'reduction_percentage' in data
                    assert data['quantization_level'] == 'INT4'

def test_run_latency_comparison_zero_baseline_raises():
    """Test that zero baseline time raises an error."""
    with patch('src.services.latency_meter.load_quantized_model'):
        with patch('src.services.latency_meter.run_quantized_inference'):
            with patch('joblib.load'):
                with patch('time.perf_counter') as mock_time:
                    # Proxy: 0.1s, Baseline: 0.0s (simulated error case)
                    mock_time.side_effect = [0.0, 0.1, 0.0, 0.0]
                    
                    with pytest.raises(ValueError, match="Baseline time must be greater than zero"):
                        run_latency_comparison(
                            feature_vectors=[np.array([1.0])],
                            prompts=["test"],
                            model_path="fake",
                            predictor_path="fake",
                            output_path="fake.json"
                        )