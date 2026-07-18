"""
Unit tests for the executor module.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from benchmarks.executor import Executor, ExecutionResult, FIXED_ITERATIONS
from benchmarks.config import BenchmarkConfig, ConfigManager

class TestExecutor:
    """Tests for the Executor class."""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock config manager."""
        manager = Mock(spec=ConfigManager)
        manager.get_current_config.return_value = BenchmarkConfig(
            config_id="test_config",
            kernel_type="matmul",
            compiler_flags=["-O2"],
            tensor_dim=(512, 512)
        )
        return manager
    
    @pytest.fixture
    def executor(self, mock_config_manager):
        """Create an executor instance."""
        return Executor(mock_config_manager)
    
    def test_detect_memory_error_positive(self, executor):
        """Test memory error detection with known error messages."""
        error_messages = [
            "cannot allocate memory",
            "out of memory",
            "std::bad_alloc",
            "memory allocation failed"
        ]
        
        for msg in error_messages:
            assert executor._detect_memory_error(msg) is True
    
    def test_detect_memory_error_negative(self, executor):
        """Test memory error detection with non-error messages."""
        non_error_messages = [
            "execution completed successfully",
            "no errors detected",
            "normal termination"
        ]
        
        for msg in non_error_messages:
            assert executor._detect_memory_error(msg) is False
    
    def test_calculate_statistics_empty(self, executor):
        """Test statistics calculation with empty samples."""
        median, p95 = executor._calculate_statistics([])
        assert median == 0.0
        assert p95 == 0.0
    
    def test_calculate_statistics_single(self, executor):
        """Test statistics calculation with single sample."""
        median, p95 = executor._calculate_statistics([1.0])
        assert median == 1.0
        assert p95 == 1.0
    
    def test_calculate_statistics_multiple(self, executor):
        """Test statistics calculation with multiple samples."""
        samples = [1.0, 2.0, 3.0, 4.0, 5.0]
        median, p95 = executor._calculate_statistics(samples)
        assert median == 3.0
        assert p95 == 5.0  # p95 of 5 samples is the 5th value
    
    def test_calculate_cv_zero_mean(self, executor):
        """Test CV calculation with zero mean."""
        cv = executor._calculate_cv([0.0, 0.0, 0.0])
        assert cv == float('inf')
    
    def test_calculate_cv_normal(self, executor):
        """Test CV calculation with normal values."""
        # CV = std / mean
        samples = [1.0, 1.1, 0.9]  # mean=1.0, std≈0.1
        cv = executor._calculate_cv(samples)
        assert 0.05 < cv < 0.15  # Approximate range
    
    @patch('subprocess.run')
    def test_run_binary_success(self, mock_run, executor):
        """Test successful binary execution."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Iteration 1: 0.001 ms\nIteration 2: 0.002 ms"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        
        latencies, exit_code, stderr = executor._run_binary(
            Path("/fake/binary"), (512, 512), "matmul"
        )
        
        assert exit_code == 0
        assert len(latencies) == 2
        assert stderr == ""
    
    @patch('subprocess.run')
    def test_run_binary_memory_error(self, mock_run, executor):
        """Test binary execution with memory error."""
        mock_process = Mock()
        mock_process.returncode = 139  # Segmentation fault
        mock_process.stdout = ""
        mock_process.stderr = "cannot allocate memory"
        mock_run.return_value = mock_process
        
        latencies, exit_code, stderr = executor._run_binary(
            Path("/fake/binary"), (512, 512), "matmul"
        )
        
        assert exit_code == 139
        assert len(latencies) == 0
        assert "cannot allocate memory" in stderr
    
    def test_save_results(self, executor):
        """Test saving results to file."""
        result = ExecutionResult(
            median=0.001,
            p95=0.002,
            iterations=100,
            config_id="test_config",
            downsampled_flag=False,
            latency_samples=[0.001] * 100,
            memory_fallback_triggered=False,
            exit_code=0
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            executor.raw_logs_dir = Path(tmpdir)
            output_file = executor.save_results(result)
            
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                data = json.loads(f.readline())
                
            assert data['median'] == 0.001
            assert data['p95'] == 0.002
            assert data['config_id'] == 'test_config'
            assert data['downsampled_flag'] == False
    
    def test_execute_configuration_memory_fallback(self, executor, mock_config_manager):
        """Test execution with memory fallback."""
        with patch.object(executor, '_run_binary') as mock_run:
            # First call: memory error
            mock_run.side_effect = [
                ([], 139, "cannot allocate memory"),
                ([0.001] * 100, 0, "")
            ]
            
            config = BenchmarkConfig(
                config_id="test_config",
                kernel_type="matmul",
                compiler_flags=["-O2"],
                tensor_dim=(768, 768)
            )
            
            result = executor.execute_configuration(config, Path("/fake/binary"))
            
            assert result.downsampled_flag is True
            assert result.memory_fallback_triggered is True
            assert result.exit_code == 0
            assert len(result.latency_samples) == 100
    
    def test_execute_configuration_adaptive_stop(self, executor, mock_config_manager):
        """Test execution with adaptive stopping."""
        with patch.object(executor, '_run_binary') as mock_run:
            # Return enough samples to trigger adaptive stop
            mock_run.return_value = ([0.001] * 50, 0, "")
            
            config = BenchmarkConfig(
                config_id="test_config",
                kernel_type="matmul",
                compiler_flags=["-O2"],
                tensor_dim=(512, 512)
            )
            
            result = executor.execute_configuration(config, Path("/fake/binary"))
            
            # Should have collected at least some iterations
            assert result.iterations > 0
            assert result.median > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
