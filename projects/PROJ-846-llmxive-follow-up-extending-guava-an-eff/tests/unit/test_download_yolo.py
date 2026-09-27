"""
Unit tests for T015a: download_yolo.py
"""
import os
import sys
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.download_yolo import (
    calculate_sha256,
    verify_checksum,
    EXPECTED_SHA256,
    MODEL_FILENAME
)
from utils.errors import DatasetUnavailableError


class TestChecksum:
    def test_calculate_sha256(self, tmp_path):
        """Test SHA256 calculation on a known string."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_sha256(test_file)

        assert actual_hash == expected_hash

    def test_verify_checksum_valid(self, tmp_path):
        """Test checksum verification with valid hash."""
        test_file = tmp_path / "test.bin"
        content = b"test data"
        test_file.write_bytes(content)
        valid_hash = hashlib.sha256(content).hexdigest()

        assert verify_checksum(test_file, valid_hash) is True

    def test_verify_checksum_invalid(self, tmp_path):
        """Test checksum verification with invalid hash."""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test data")
        bad_hash = "0" * 64

        assert verify_checksum(test_file, bad_hash) is False


class TestDownloadLogic:
    @patch('code.data.download_yolo.hf_hub_download')
    def test_download_success(self, mock_download, tmp_path):
        """Test successful download flow."""
        mock_download.return_value = str(tmp_path / MODEL_FILENAME)
        
        # Create a dummy file to simulate download
        dummy_file = tmp_path / MODEL_FILENAME
        dummy_file.write_bytes(b"dummy model data")

        from code.data.download_yolo import download_model
        result = download_model(tmp_path)

        assert result.exists()
        mock_download.assert_called_once()

    @patch('code.data.download_yolo.hf_hub_download')
    def test_download_failure(self, mock_download, tmp_path):
        """Test download failure raises DatasetUnavailableError."""
        mock_download.side_effect = Exception("Network error")

        from code.data.download_yolo import download_model

        with pytest.raises(DatasetUnavailableError):
            download_model(tmp_path)

class TestLatencyConstraint:
    """
    Note: Actual latency testing requires a real ONNX model and runtime.
    This test mocks the latency to ensure the logic handles pass/fail correctly.
    """
    @patch('code.data.download_yolo.ort.InferenceSession')
    @patch('code.data.download_yolo.time.perf_counter')
    def test_latency_pass(self, mock_time, mock_session, tmp_path):
        """Test that latency under threshold passes."""
        # Mock session
        mock_sess = MagicMock()
        mock_sess.get_inputs.return_value = [MagicMock(shape=[1, 3, 640, 640])]
        mock_session.return_value = mock_sess

        # Mock time to return low latency
        mock_time.side_effect = [0.0, 0.01, 0.02, 0.03] # 10ms per run

        from code.data.download_yolo import benchmark_latency, MAX_LATENCY_MS

        mean_lat, std_lat = benchmark_latency(tmp_path / "dummy.onnx")

        assert mean_lat < MAX_LATENCY_MS

    @patch('code.data.download_yolo.ort.InferenceSession')
    @patch('code.data.download_yolo.time.perf_counter')
    def test_latency_fail(self, mock_time, mock_session, tmp_path):
        """Test that latency over threshold fails."""
        mock_sess = MagicMock()
        mock_sess.get_inputs.return_value = [MagicMock(shape=[1, 3, 640, 640])]
        mock_session.return_value = mock_sess

        # Mock time to return high latency
        mock_time.side_effect = [0.0, 0.2, 0.4, 0.6] # 200ms per run

        from code.data.download_yolo import benchmark_latency, MAX_LATENCY_MS

        mean_lat, std_lat = benchmark_latency(tmp_path / "dummy.onnx")

        assert mean_lat > MAX_LATENCY_MS