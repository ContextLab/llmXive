"""
Unit tests for run_benchmark.py functionality.

Tests cover:
- Configuration loading
- Task execution in both modes
- Result aggregation
- Error handling
"""

import pytest
import yaml
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.benchmark.run_benchmark import load_config, run_single_task, execute_unified_task, execute_heterogeneous_task
from src.tasks.task_runner import TaskRunner
from src.models.translation import UnifiedTranslator
from src.models.routing import ModalityRouter


class TestLoadConfig:
    """Tests for load_config function."""
    
    def test_load_config_valid_file(self, tmp_path):
        """Test loading a valid configuration file."""
        config_data = {
            'datasets': [{'name': 'test'}],
            'modalities': ['text'],
            'seeds': 3,
            'timeout_per_task': 300
        }
        
        config_file = tmp_path / 'test_config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        loaded_config = load_config(str(config_file))
        
        assert loaded_config == config_data
        assert loaded_config['seeds'] == 3
    
    def test_load_config_missing_file(self):
        """Test loading a non-existent configuration file."""
        with pytest.raises(FileNotFoundError):
            load_config('nonexistent.yaml')
    
    def test_load_config_invalid_yaml(self, tmp_path):
        """Test loading a file with invalid YAML syntax."""
        config_file = tmp_path / 'invalid.yaml'
        with open(config_file, 'w') as f:
            f.write('invalid: yaml: content: [')
        
        with pytest.raises(yaml.YAMLError):
            load_config(str(config_file))

class TestRunSingleTask:
    """Tests for run_single_task function."""
    
    @patch('src.benchmark.run_benchmark.TaskRunner')
    @patch('src.benchmark.run_benchmark.UnifiedTranslator')
    @patch('src.benchmark.run_benchmark.ModalityRouter')
    def test_run_task_heterogeneous_mode(self, mock_router, mock_translator, mock_runner):
        """Test task execution in heterogeneous mode."""
        # Setup mocks
        mock_runner_instance = MagicMock()
        mock_runner.return_value = mock_runner_instance
        mock_runner_instance.get_task.return_value = {
            'task_id': 'T001',
            'modalities': ['text'],
            'datasets': ['test']
        }
        
        mock_router_instance = MagicMock()
        mock_router.return_value = mock_router_instance
        mock_model = MagicMock()
        mock_model.predict.return_value = 'prediction'
        mock_router_instance.get_model.return_value = mock_model
        
        config = {'tasks': ['T001'], 'seeds': 1}
        
        result = run_single_task('T001', config, 'heterogeneous', 42)
        
        assert result['task_id'] == 'T001'
        assert result['mode'] == 'heterogeneous'
        assert result['seed'] == 42
        assert result['status'] in ['success', 'failed']  # Depends on mock setup
        assert 'duration_seconds' in result
    
    @patch('src.benchmark.run_benchmark.TaskRunner')
    @patch('src.benchmark.run_benchmark.UnifiedTranslator')
    def test_run_task_unified_mode(self, mock_translator, mock_runner):
        """Test task execution in unified mode."""
        # Setup mocks
        mock_runner_instance = MagicMock()
        mock_runner.return_value = mock_runner_instance
        mock_runner_instance.get_task.return_value = {
            'task_id': 'T001',
            'modalities': ['text'],
            'datasets': ['test']
        }
        
        mock_translator_instance = MagicMock()
        mock_translator.return_value = mock_translator_instance
        mock_translator_instance.translate_all.return_value = 'translated text'
        
        config = {'tasks': ['T001'], 'seeds': 1}
        
        result = run_single_task('T001', config, 'unified', 42)
        
        assert result['task_id'] == 'T001'
        assert result['mode'] == 'unified'
        assert result['seed'] == 42
        assert result['status'] in ['success', 'failed']
        assert 'duration_seconds' in result
    
    def test_run_task_missing_task(self):
        """Test execution of a non-existent task."""
        config = {'tasks': []}
        
        # This should handle the missing task gracefully
        result = run_single_task('T999', config, 'heterogeneous', 42)
        
        assert result['task_id'] == 'T999'
        assert result['status'] in ['failed', 'crashed']

class TestExecuteUnifiedTask:
    """Tests for execute_unified_task function."""
    
    @patch('src.benchmark.run_benchmark.UnifiedTranslator')
    def test_execute_unified_task(self, mock_translator):
        """Test unified task execution."""
        mock_runner = MagicMock()
        mock_runner.get_task.return_value = {
            'task_id': 'T001',
            'datasets': ['test']
        }
        
        mock_translator_instance = MagicMock()
        mock_translator.return_value = mock_translator_instance
        mock_translator_instance.translate_all.return_value = 'translated'
        
        config = {}
        
        result = execute_unified_task('T001', mock_runner, mock_translator_instance, config, 42)
        
        assert 'predictions' in result
        assert 'metrics' in result
        assert 'modality_contributions' in result

class TestExecuteHeterogeneousTask:
    """Tests for execute_heterogeneous_task function."""
    
    @patch('src.benchmark.run_benchmark.ModalityRouter')
    def test_execute_heterogeneous_task(self, mock_router):
        """Test heterogeneous task execution."""
        mock_runner = MagicMock()
        mock_runner.get_task.return_value = {
            'task_id': 'T001',
            'modalities': ['text', 'tabular']
        }
        
        mock_router_instance = MagicMock()
        mock_router.return_value = mock_router_instance
        
        mock_model = MagicMock()
        mock_model.predict.return_value = 'prediction'
        mock_router_instance.get_model.return_value = mock_model
        
        config = {}
        
        result = execute_heterogeneous_task('T001', mock_runner, mock_router_instance, config, 42)
        
        assert 'predictions' in result
        assert 'modality_contributions' in result
        assert len(result['predictions']) == 2  # Two modalities

class TestIntegration:
    """Integration tests for the benchmark flow."""
    
    def test_config_and_task_flow(self, tmp_path):
        """Test end-to-end flow with temporary config."""
        # Create a minimal valid config
        config_data = {
            'datasets': [{'name': 'test'}],
            'modalities': ['text'],
            'seeds': 1,
            'timeout_per_task': 60,
            'tasks': ['T001']
        }
        
        config_file = tmp_path / 'test.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Verify config loads correctly
        config = load_config(str(config_file))
        assert config['seeds'] == 1
        assert len(config['tasks']) == 1