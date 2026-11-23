"""
Unit tests for the Inference Optimizer (T035).
"""

import os
import sys
import pytest
import torch
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.inference_optimizer import InferenceOptimizer
from models.gru_estimator import GRUEstimator


@pytest.fixture
def sample_model():
    """Creates a dummy GRU model for testing."""
    model = GRUEstimator(input_size=10, hidden_size=16, num_layers=1)
    model.eval()
    return model


@pytest.fixture
def sample_data():
    """Creates a dummy DataFrame for tuning."""
    data = {
        'f1': np.random.rand(100, 10).astype(np.float32),
        'f2': np.random.rand(100, 10).astype(np.float32),
        'f3': np.random.rand(100, 10).astype(np.float32),
        'f4': np.random.rand(100, 10).astype(np.float32),
        'f5': np.random.rand(100, 10).astype(np.float32),
        'timestamp': range(100),
        'turn_label': [0] * 50 + [1] * 50,
        'priority': ['low'] * 50 + ['high'] * 50
    }
    # Flatten for simplicity if needed, but model expects (batch, seq, feat)
    # We will simulate a structure that the optimizer can slice
    df = pd.DataFrame({
        'feat_0': np.random.rand(100),
        'feat_1': np.random.rand(100),
        'feat_2': np.random.rand(100),
        'feat_3': np.random.rand(100),
        'feat_4': np.random.rand(100),
        'feat_5': np.random.rand(100),
        'feat_6': np.random.rand(100),
        'feat_7': np.random.rand(100),
        'feat_8': np.random.rand(100),
        'feat_9': np.random.rand(100),
        'timestamp': range(100),
        'turn_label': [0] * 50 + [1] * 50,
        'priority': ['low'] * 50 + ['high'] * 50
    })
    return df


def test_optimizer_initialization(sample_model):
    """Test that the optimizer initializes correctly."""
    opt = InferenceOptimizer(sample_model, device="cpu")
    assert opt.device == "cpu"
    assert opt.best_batch_size == 1
    assert opt.optimized_model is None


def test_ensure_contiguous(sample_model):
    """Test that tensors are made contiguous."""
    opt = InferenceOptimizer(sample_model, device="cpu")
    dummy = torch.randn(2, 3, 4)
    # Make it non-contiguous
    non_contig = dummy.transpose(1, 2)
    assert not non_contig.is_contiguous()

    result = opt._ensure_contiguous([non_contig])
    assert result[0].is_contiguous()


@patch('utils.inference_optimizer.time.perf_counter')
def test_measure_latency(mock_time, sample_model, sample_data):
    """Test latency measurement logic."""
    opt = InferenceOptimizer(sample_model, device="cpu")

    # Mock time to return predictable values
    mock_time.side_effect = [0.0, 0.1] # start, end -> 0.1s total

    dummy_input = torch.randn(1, 10, 10)
    latency = opt._measure_latency(1, dummy_input, num_runs=1)

    # 0.1 seconds = 100 ms
    assert latency == 100.0


def test_tune_batch_size(sample_model, sample_data, tmp_path):
    """Test batch size tuning."""
    opt = InferenceOptimizer(sample_model, device="cpu", max_batch_size=4)
    best_bs = opt.tune_batch_size(sample_data)
    assert best_bs in [1, 2, 4]
    assert len(opt.latency_history) > 0


def test_compile_model(sample_model):
    """Test TorchScript compilation."""
    opt = InferenceOptimizer(sample_model, device="cpu")
    opt.compile_model()
    # If compilation succeeds, optimized_model should be set (or fallback)
    assert opt.optimized_model is not None


def test_optimize_inference_pipeline(sample_model, sample_data, tmp_path):
    """Test the full optimization pipeline."""
    # Save sample data
    data_path = tmp_path / "sample.parquet"
    sample_data.to_parquet(data_path)
    stats_path = tmp_path / "stats.json"

    opt = InferenceOptimizer(sample_model, device="cpu", max_batch_size=4)
    stats = opt.optimize_inference_pipeline(str(data_path), str(stats_path))

    assert "optimal_batch_size" in stats
    assert "model_compiled" in stats
    assert os.path.exists(stats_path)