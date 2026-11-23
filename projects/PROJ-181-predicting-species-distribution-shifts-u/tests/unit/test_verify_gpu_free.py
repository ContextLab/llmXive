"""
Unit tests for verify_gpu_free.py logic.
"""
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.verify_gpu_free import check_environment_gpu_status, verify_training_script_cpu_usage

class TestCheckEnvironmentGPUStatus:
    def test_no_torch_no_tf(self):
        """Test when neither torch nor tf is installed."""
        with patch.dict('sys.modules', {'torch': None, 'tensorflow': None}):
            # Simulate ImportError
            with patch('builtins.__import__', side_effect=ImportError("No module")):
                issues = check_environment_gpu_status()
                # Should not raise, should return empty or log info
                assert isinstance(issues, list)

    def test_torch_cuda_available(self):
        """Test when PyTorch detects CUDA."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 4
        
        with patch.dict('sys.modules', {'torch': mock_torch}):
            with patch('builtins.__import__', return_value=mock_torch):
                issues = check_environment_gpu_status()
                assert any("PyTorch detects CUDA" in issue for issue in issues)

    def test_torch_cuda_not_available(self):
        """Test when PyTorch does not detect CUDA."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        
        with patch.dict('sys.modules', {'torch': mock_torch}):
            with patch('builtins.__import__', return_value=mock_torch):
                issues = check_environment_gpu_status()
                assert not any("PyTorch detects CUDA" in issue for issue in issues)

    def test_tf_gpus_detected(self):
        """Test when TensorFlow detects GPUs."""
        mock_tf = MagicMock()
        mock_gpus = [MagicMock(), MagicMock()]
        mock_tf.config.list_physical_devices.return_value = mock_gpus
        
        with patch.dict('sys.modules', {'tensorflow': mock_tf}):
            with patch('builtins.__import__', return_value=mock_tf):
                issues = check_environment_gpu_status()
                assert any("TensorFlow detects" in issue for issue in issues)

    def test_tf_no_gpus(self):
        """Test when TensorFlow detects no GPUs."""
        mock_tf = MagicMock()
        mock_tf.config.list_physical_devices.return_value = []
        
        with patch.dict('sys.modules', {'tensorflow': mock_tf}):
            with patch('builtins.__import__', return_value=mock_tf):
                issues = check_environment_gpu_status()
                assert not any("TensorFlow detects" in issue for issue in issues)

class TestVerifyTrainingScriptCPUUsage:
    def test_script_missing(self):
        """Test when train.py is missing."""
        with patch('pathlib.Path.exists', return_value=False):
            issues = verify_training_script_cpu_usage()
            assert any("train.py not found" in issue for issue in issues)

    def test_script_has_cuda_device(self):
        """Test when script explicitly sets CUDA device."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "device = 'cuda'"
        
        with patch('pathlib.Path', return_value=mock_path):
            issues = verify_training_script_cpu_usage()
            assert any("train.py explicitly sets device to CUDA" in issue for issue in issues)

    def test_script_cpu_safe(self):
        """Test when script is CPU safe."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "device = 'cpu'\nn_jobs=2"
        
        with patch('pathlib.Path', return_value=mock_path):
            issues = verify_training_script_cpu_usage()
            assert not any("train.py explicitly sets device to CUDA" in issue for issue in issues)