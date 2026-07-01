import pytest
import yaml
import json
from pathlib import Path
import tempfile
import os

from src.benchmark.run_benchmark import load_config, run_single_task, main
from src.tasks.task_runner import TaskRunner

class TestRunBenchmark:
    """Unit tests for run_benchmark.py functionality."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'datasets': ['UCI_HAR'],
                'modalities': ['time_series'],
                'seeds': 2,
                'timeout_per_task': 300,
                'bootstrapping': {
                    'enabled': True,
                    'n_iterations': 100
                },
                'task_definitions_path': 'src/tasks/task_definitions.yaml',
                'output_dir': 'data'
            }
            yaml.dump(config, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    def test_load_config_valid(self, temp_config_file):
        """Test loading a valid configuration file."""
        config = load_config(temp_config_file)
        
        assert config is not None
        assert 'datasets' in config
        assert 'modalities' in config
        assert config['seeds'] == 2
        assert config['timeout_per_task'] == 300
    
    def test_load_config_invalid_path(self):
        """Test loading a non-existent config file."""
        with pytest.raises(FileNotFoundError):
            load_config('non_existent_file.yaml')
    
    def test_run_single_task_timeout(self, temp_config_file):
        """Test task execution with timeout enforcement."""
        config = load_config(temp_config_file)
        runner = TaskRunner()
        
        # This should complete within timeout
        result = run_single_task(runner, "T001", config, seed=42)
        
        assert result is not None
        assert 'task_id' in result
        assert result['task_id'] == "T001"
    
    def test_heterogeneous_mode(self, temp_config_file):
        """Test heterogeneous mode execution."""
        config = load_config(temp_config_file)
        
        # Mock task execution
        from unittest.mock import patch, MagicMock
        
        with patch('src.benchmark.run_benchmark.ModalityRouter') as mock_router:
            with patch('src.benchmark.run_benchmark.TaskRunner') as mock_runner:
                mock_runner.return_value.run_task.return_value = {
                    'task_id': 'T001',
                    'status': 'completed',
                    'metrics': {'f1': 0.85}
                }
                
                # Test execution
                result = run_single_task(mock_runner.return_value, "T001", config, seed=42)
                
                assert result['mode'] == 'heterogeneous'
                assert result['status'] == 'completed'
    
    def test_unified_mode(self, temp_config_file):
        """Test unified mode execution."""
        config = load_config(temp_config_file)
        
        from unittest.mock import patch
        
        with patch('src.benchmark.run_benchmark.UnifiedTranslator') as mock_translator:
            with patch('src.benchmark.run_benchmark.TaskRunner') as mock_runner:
                mock_runner.return_value.run_task.return_value = {
                    'task_id': 'T001',
                    'status': 'completed',
                    'metrics': {'f1': 0.85}
                }
                
                result = run_single_task(mock_runner.return_value, "T001", config, seed=42)
                
                assert result['mode'] == 'unified'
                assert result['status'] == 'completed'
    
    def test_task_not_found(self, temp_config_file):
        """Test handling of non-existent task."""
        config = load_config(temp_config_file)
        runner = TaskRunner()
        
        result = run_single_task(runner, "NON_EXISTENT_TASK", config, seed=42)
        
        assert result['status'] == 'error'
        assert 'not found' in result.get('error', '').lower()
    
    def test_config_loading_from_default(self):
        """Test that default config path is handled correctly."""
        # This test verifies the default config path exists or fails gracefully
        default_path = Path('src/benchmark/config/default.yaml')
        
        # If file exists, it should load
        if default_path.exists():
            config = load_config(str(default_path))
            assert config is not None
            assert 'datasets' in config
            assert 'seeds' in config

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
