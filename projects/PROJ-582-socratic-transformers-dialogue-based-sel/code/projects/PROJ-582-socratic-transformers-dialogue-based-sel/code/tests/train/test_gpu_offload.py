"""
Tests for the GPU Offload Orchestrator (T022).
"""
import subprocess
import sys
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path

# Adjust path to import the module
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.train.gpu_offload import main, run_cpu_training, run_gpu_training, EXIT_OOM, EXIT_SUCCESS

class TestGpuOffloadOrchestrator:
    def test_cpu_success_no_offload(self, capsys):
        """
        Test that if CPU training succeeds (exit code 0), the GPU offload is NOT triggered.
        """
        with patch("src.train.gpu_offload.run_cpu_training") as mock_cpu:
            mock_cpu.return_value = EXIT_SUCCESS
            
            with patch("src.train.gpu_offload.run_gpu_training") as mock_gpu:
                result = main()
                
                # Verify CPU was called
                mock_cpu.assert_called_once()
                # Verify GPU was NOT called
                mock_gpu.assert_not_called()
                assert result == EXIT_SUCCESS
                
        captured = capsys.readouterr()
        assert "No offload needed" in captured.out

    def test_cpu_oom_triggers_gpu(self, capsys):
        """
        Test that if CPU training fails with OOM (exit code 1), GPU offload IS triggered.
        """
        with patch("src.train.gpu_offload.run_cpu_training") as mock_cpu:
            mock_cpu.return_value = EXIT_OOM
            
            with patch("src.train.gpu_offload.run_gpu_training") as mock_gpu:
                mock_gpu.return_value = EXIT_SUCCESS
                
                result = main()
                
                # Verify CPU was called
                mock_cpu.assert_called_once()
                # Verify GPU was called
                mock_gpu.assert_called_once()
                assert result == EXIT_SUCCESS
                
        captured = capsys.readouterr()
        assert "Triggering automatic GPU offload" in captured.out

    def test_gpu_failure_propagates(self):
        """
        Test that if GPU offload also fails, the failure code is returned.
        """
        with patch("src.train.gpu_offload.run_cpu_training") as mock_cpu:
            mock_cpu.return_value = EXIT_OOM
            
            with patch("src.train.gpu_offload.run_gpu_training") as mock_gpu:
                mock_gpu.return_value = 1  # Simulate GPU failure
                
                result = main()
                
                assert result == 1

    def test_unexpected_cpu_failure(self):
        """
        Test that unexpected CPU failure codes (non-0, non-1) abort the process.
        """
        with patch("src.train.gpu_offload.run_cpu_training") as mock_cpu:
            mock_cpu.return_value = 2  # Unexpected error
            
            with patch("src.train.gpu_offload.run_gpu_training") as mock_gpu:
                result = main()
                
                # GPU should NOT be called for unexpected errors
                mock_gpu.assert_not_called()
                assert result == 2