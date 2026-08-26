"""
Unit tests for the performance profiler module.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code to path if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.performance_profiler import (
    check_kaggle_gpu,
    profile_inference_step,
    profile_feature_extraction,
    enable_gpu_offload_if_kaggle,
    run_full_profiling_pipeline
)

@patch('src.utils.performance_profiler.TORCH_AVAILABLE', True)
@patch('src.utils.performance_profiler.os.environ.get')
def test_check_kaggle_gpu_kaggle_env(mock_env, mock_torch):
    """Test detection of Kaggle GPU environment."""
    mock_env.return_value = "K80" # Simulating KAGGLE_KERNEL_RUN_TYPE
    
    with patch('src.utils.performance_profiler.torch.cuda.is_available', return_value=True):
        result = check_kaggle_gpu()
        assert result is True

@patch('src.utils.performance_profiler.TORCH_AVAILABLE', True)
@patch('src.utils.performance_profiler.os.environ.get')
def test_check_kaggle_gpu_no_kaggle(mock_env, mock_torch):
    """Test non-Kaggle environment."""
    mock_env.return_value = None
    
    with patch('src.utils.performance_profiler.torch.cuda.is_available', return_value=True):
        result = check_kaggle_gpu()
        assert result is False

@patch('src.utils.performance_profiler.get_available_ram_gb', return_value=16.0)
@patch('src.utils.performance_profiler.calculate_batch_size', return_value=32)
def test_profile_inference_step(mock_calc_batch, mock_ram):
    """Test inference profiling logic."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "profile.json"
        result = profile_inference_step(output_path=output_path)
        
        assert result["status"] == "profiled"
        assert result["recommended_batch_size"] == 32
        assert output_path.exists()
        
        with open(output_path) as f:
            data = json.load(f)
            assert data["recommended_batch_size"] == 32

@patch('src.utils.performance_profiler.get_available_ram_gb', return_value=16.0)
def test_profile_feature_extraction(mock_ram):
    """Test feature extraction profiling logic."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "profile.json"
        result = profile_feature_extraction(output_path=output_path)
        
        assert result["status"] == "profiled"
        assert "profile_duration_ms" in result
        assert output_path.exists()

@patch('src.utils.performance_profiler.check_kaggle_gpu', return_value=True)
def test_enable_gpu_offload_kaggle(mock_check):
    """Test GPU offload enablement when Kaggle GPU is detected."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "gpu.json"
        result = enable_gpu_offload_if_kaggle(output_path=output_path)
        
        assert result["kaggle_gpu_detected"] is True
        assert result["device"] == "cuda"
        assert result["action_taken"] == "enabled_gpu_offload"
        assert output_path.exists()

@patch('src.utils.performance_profiler.check_kaggle_gpu', return_value=False)
def test_enable_gpu_offload_no_kaggle(mock_check):
    """Test GPU offload when no Kaggle GPU is detected."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "gpu.json"
        result = enable_gpu_offload_if_kaggle(output_path=output_path)
        
        assert result["kaggle_gpu_detected"] is False
        assert result["device"] == "cpu"
        assert result["action_taken"] == "none"
        assert output_path.exists()

@patch('src.utils.performance_profiler.get_available_ram_gb', return_value=16.0)
@patch('src.utils.performance_profiler.calculate_batch_size', return_value=16)
@patch('src.utils.performance_profiler.check_kaggle_gpu', return_value=True)
def test_run_full_profiling_pipeline(mock_gpu, mock_calc, mock_ram):
    """Test the full profiling pipeline orchestration."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir)
        results = run_full_profiling_pipeline(output_path)
        
        assert "inference" in results
        assert "feature_extraction" in results
        assert "gpu_offload" in results
        assert "summary" in results
        
        # Check summary content
        assert results["summary"]["gpu_available"] is True
        assert results["summary"]["device"] == "cuda"
        
        # Check files created
        assert (output_path / "performance_profile_summary.json").exists()
        assert (output_path / "inference_profile.json").exists()
        assert (output_path / "feature_extraction_profile.json").exists()
        assert (output_path / "gpu_offload_status.json").exists()