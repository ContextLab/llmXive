"""
Unit tests for JaCoText CPU verification module.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.jacotext_cpu import get_model_size_mb, verify_cpu_tractability

class TestModelSize:
    def test_get_model_size_mb_file(self, tmp_path):
        """Test size calculation for a single file."""
        file_path = tmp_path / "model.bin"
        file_path.write_bytes(b"0" * 1024)  # 1KB
        
        size_mb = get_model_size_mb(str(file_path))
        assert size_mb == 1024 / (1024 * 1024)
    
    def test_get_model_size_mb_dir(self, tmp_path):
        """Test size calculation for a directory."""
        file1 = tmp_path / "file1.bin"
        file1.write_bytes(b"0" * 1024)
        file2 = tmp_path / "file2.bin"
        file2.write_bytes(b"0" * 2048)
        
        size_mb = get_model_size_mb(str(tmp_path))
        assert size_mb == (1024 + 2048) / (1024 * 1024)
    
    def test_get_model_size_mb_not_found(self):
        """Test error handling for missing path."""
        with pytest.raises(FileNotFoundError):
            get_model_size_mb("/nonexistent/path")

class TestVerification:
    @patch('models.jacotext_cpu.load_model')
    @patch('models.jacotext_cpu.run_inference')
    @patch('models.jacotext_cpu.HfApi')
    def test_verify_success(self, mock_api, mock_inference, mock_load):
        """Test successful verification."""
        # Mock HF API
        mock_info = MagicMock()
        mock_info.siblings = [MagicMock(size=500 * 1024 * 1024)] # 500MB
        mock_api.return_value.model_info.return_value = mock_info
        
        # Mock load
        mock_load.return_value = (MagicMock(), MagicMock())
        
        # Mock inference
        mock_inference.return_value = {
            "success": True,
            "time_seconds": 10.0,
            "tokens_generated": 10
        }
        
        result = verify_cpu_tractability("fake-model")
        
        assert result["status"] == "passed"
        assert result["checks"]["size_check"]["passed"] is True
        assert result["checks"]["inference_check"]["passed"] is True

    @patch('models.jacotext_cpu.load_model')
    @patch('models.jacotext_cpu.HfApi')
    def test_verify_size_exceeded(self, mock_api, mock_load):
        """Test failure when model size > 1GB."""
        # Mock HF API with large model
        mock_info = MagicMock()
        mock_info.siblings = [MagicMock(size=2 * 1024 * 1024 * 1024)] # 2GB
        mock_api.return_value.model_info.return_value = mock_info
        
        result = verify_cpu_tractability("fake-model")
        
        assert result["status"] == "failed_size"
        assert result["checks"]["size_check"]["passed"] is False

    @patch('models.jacotext_cpu.load_model')
    @patch('models.jacotext_cpu.HfApi')
    def test_verify_load_failure(self, mock_api, mock_load):
        """Test failure when model load fails."""
        # Mock HF API
        mock_info = MagicMock()
        mock_info.siblings = [MagicMock(size=500 * 1024 * 1024)]
        mock_api.return_value.model_info.return_value = mock_info
        
        # Mock load failure
        mock_load.side_effect = RuntimeError("Load error")
        
        result = verify_cpu_tractability("fake-model")
        
        assert result["status"] == "failed_load"
        assert result["checks"]["load_check"]["passed"] is False