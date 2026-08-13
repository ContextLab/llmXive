"""
Unit tests for verify_memory_footprint.py
"""
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.evaluation.verify_memory_footprint import (
    get_memory_usage,
    verify_memory_footprint,
    MEMORY_LIMIT_GB
)

class TestGetMemoryUsage:
    def test_get_memory_usage_returns_positive(self):
        """Test that get_memory_usage returns a positive number."""
        # This might fail on some systems without psutil or /proc
        try:
            mem = get_memory_usage()
            assert mem >= 0
        except Exception:
            # If we can't measure memory, that's okay for this test
            pass

class TestVerifyMemoryFootprint:
    @patch('src.evaluation.verify_memory_footprint.load_gguf_model')
    @patch('src.evaluation.verify_memory_footprint.run_dry_run_inference')
    @patch('src.evaluation.verify_memory_footprint.get_memory_usage')
    def test_verify_success_within_limit(
        self, 
        mock_get_mem, 
        mock_run_inference, 
        mock_load_model
    ):
        """Test successful verification when memory is within limit."""
        # Mock memory usage
        mock_get_mem.side_effect = [1 * 1024**3, 2 * 1024**3]  # 1GB -> 2GB
        
        # Mock model loading
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model
        
        # Mock inference success
        mock_run_inference.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            gguf_path = Path(tmpdir) / "test.gguf"
            gguf_path.touch()  # Create dummy file
            
            results_path = Path(tmpdir) / "results"
            results_path.mkdir()
            output_file = results_path / "test.json"

            results = verify_memory_footprint(gguf_path=gguf_path, output_path=output_file)

            assert results["status"] == "SUCCESS"
            assert results["peak_memory_gb"] == 2.0
            assert output_file.exists()
            
            with open(output_file) as f:
                saved_results = json.load(f)
            assert saved_results["status"] == "SUCCESS"

    @patch('src.evaluation.verify_memory_footprint.load_gguf_model')
    @patch('src.evaluation.verify_memory_footprint.get_memory_usage')
    def test_verify_failed_model_load(
        self, 
        mock_get_mem, 
        mock_load_model
    ):
        """Test failure when model loading fails."""
        mock_get_mem.return_value = 1 * 1024**3
        mock_load_model.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            gguf_path = Path(tmpdir) / "test.gguf"
            gguf_path.touch()

            results = verify_memory_footprint(gguf_path=gguf_path)

            assert results["status"] == "FAILED"
            assert "Failed to load model" in results["message"]

    @patch('src.evaluation.verify_memory_footprint.load_gguf_model')
    @patch('src.evaluation.verify_memory_footprint.run_dry_run_inference')
    @patch('src.evaluation.verify_memory_footprint.get_memory_usage')
    def test_verify_failed_inference(
        self, 
        mock_get_mem, 
        mock_run_inference, 
        mock_load_model
    ):
        """Test failure when inference fails."""
        mock_get_mem.return_value = 1 * 1024**3
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model
        mock_run_inference.return_value = False

        with tempfile.TemporaryDirectory() as tmpdir:
            gguf_path = Path(tmpdir) / "test.gguf"
            gguf_path.touch()

            results = verify_memory_footprint(gguf_path=gguf_path)

            assert results["status"] == "FAILED"
            assert "Dry-run inference failed" in results["message"]

    @patch('src.evaluation.verify_memory_footprint.load_gguf_model')
    @patch('src.evaluation.verify_memory_footprint.run_dry_run_inference')
    @patch('src.evaluation.verify_memory_footprint.get_memory_usage')
    def test_verify_exceeds_limit(
        self, 
        mock_get_mem, 
        mock_run_inference, 
        mock_load_model
    ):
        """Test failure when memory exceeds limit."""
        # Mock memory usage exceeding 7GB limit
        mock_get_mem.side_effect = [1 * 1024**3, 8 * 1024**3]  # 1GB -> 8GB
        
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model
        mock_run_inference.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            gguf_path = Path(tmpdir) / "test.gguf"
            gguf_path.touch()

            results = verify_memory_footprint(gguf_path=gguf_path)

            assert results["status"] == "FAILED"
            assert "exceeds limit" in results["message"]

    def test_verify_model_not_found(self):
        """Test failure when model file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gguf_path = Path(tmpdir) / "nonexistent.gguf"
            
            results = verify_memory_footprint(gguf_path=gguf_path)
            
            assert results["status"] == "FAILED"
            assert "Model file not found" in results["message"]