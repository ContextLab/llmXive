"""
Unit tests for the run_benchmark.py entry point.

These tests verify that the benchmark runner correctly:
1. Parses command line arguments
2. Loads and validates configuration
3. Handles timeout enforcement
4. Generates output files
"""
import os
import sys
import tempfile
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
import argparse

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.benchmark.run_benchmark import (
    parse_args,
    load_config,
    setup_directories,
    run_single_seed,
    main
)
from src.utils.timeout import TimeoutError
from src.tasks.task_runner import TaskRunner

class TestParseArgs:
    """Tests for argument parsing."""
    
    def test_default_arguments(self):
        """Test that default arguments are set correctly."""
        with patch('sys.argv', ['run_benchmark.py']):
            args = parse_args()
            assert args.config == "src/benchmark/config/default.yaml"
            assert args.mode == "heterogeneous"
            assert args.seeds == 5
            assert args.timeout == 14400
    
    def test_custom_arguments(self):
        """Test that custom arguments override defaults."""
        test_args = [
            'run_benchmark.py',
            '--config', 'custom.yaml',
            '--mode', 'unified',
            '--seeds', '10',
            '--timeout', '7200'
        ]
        with patch('sys.argv', test_args):
            args = parse_args()
            assert args.config == 'custom.yaml'
            assert args.mode == 'unified'
            assert args.seeds == 10
            assert args.timeout == 7200
    
    def test_invalid_mode(self):
        """Test that invalid mode raises error."""
        with patch('sys.argv', ['run_benchmark.py', '--mode', 'invalid']):
            with pytest.raises(SystemExit):
                parse_args()

class TestLoadConfig:
    """Tests for configuration loading."""
    
    def test_load_valid_config(self, tmp_path):
        """Test loading a valid configuration file."""
        config_data = {
            "datasets": ["UCI_HAR"],
            "modalities": ["timeseries"],
            "seeds": 5,
            "timeout_per_task": 300,
            "bootstrap_resamples": 1000
        }
        config_file = tmp_path / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_config(str(config_file))
        assert config["datasets"] == ["UCI_HAR"]
        assert config["seeds"] == 5
        assert config["timeout_per_task"] == 300
    
    def test_missing_required_key(self, tmp_path):
        """Test that missing required keys raise ValueError."""
        config_data = {
            "datasets": ["UCI_HAR"],
            "modalities": ["timeseries"]
            # Missing seeds, timeout_per_task, bootstrap_resamples
        }
        config_file = tmp_path / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        with pytest.raises(ValueError, match="Missing required configuration key"):
            load_config(str(config_file))
    
    def test_file_not_found(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("non_existent_file.yaml")

class TestSetupDirectories:
    """Tests for directory setup."""
    
    def test_creates_directories(self, tmp_path):
        """Test that setup_directories creates required directories."""
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            setup_directories()
            assert (tmp_path / "data").exists()
            assert (tmp_path / "logs").exists()
            assert (tmp_path / "state").exists()
            assert (tmp_path / "data" / "processed").exists()
        finally:
            os.chdir(original_cwd)

class TestRunSingleSeed:
    """Tests for single seed execution."""
    
    def test_successful_task_run(self, tmp_path):
        """Test successful execution of a single seed."""
        config = {
            "timeout_per_task": 300,
            "tasks": [{"task_id": "T001"}]
        }
        
        mock_runner = MagicMock(spec=TaskRunner)
        mock_runner.run_task.return_value = {"accuracy": 0.95, "status": "success"}
        
        with patch('src.benchmark.run_benchmark.log_random_seed'):
            results = run_single_seed(42, config, "heterogeneous", mock_runner)
        
        assert len(results) == 1
        assert results[0]["task_id"] == "T001"
        assert results[0]["status"] == "success"
        assert results[0]["seed"] == 42
        assert results[0]["mode"] == "heterogeneous"
    
    def test_timeout_handling(self, tmp_path):
        """Test that timeout errors are handled gracefully."""
        config = {
            "timeout_per_task": 300,
            "tasks": [{"task_id": "T001"}]
        }
        
        mock_runner = MagicMock(spec=TaskRunner)
        mock_runner.run_task.side_effect = TimeoutError("Task timed out")
        
        with patch('src.benchmark.run_benchmark.log_random_seed'):
            results = run_single_seed(42, config, "heterogeneous", mock_runner)
        
        assert len(results) == 1
        assert results[0]["status"] == "timeout"
        assert "error" in results[0]

class TestMain:
    """Tests for the main entry point."""
    
    def test_main_execution(self, tmp_path, caplog):
        """Test that main() executes without error."""
        # Create a temporary config file
        config_data = {
            "datasets": ["UCI_HAR"],
            "modalities": ["timeseries"],
            "seeds": 2,
            "timeout_per_task": 300,
            "bootstrap_resamples": 1000,
            "tasks": [{"task_id": "T001"}]
        }
        config_file = tmp_path / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Create required directories
        (tmp_path / "data").mkdir()
        (tmp_path / "logs").mkdir()
        (tmp_path / "state").mkdir()
        
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            with patch('sys.argv', ['run_benchmark.py', '--config', str(config_file), '--seeds', '2']):
                with patch('src.benchmark.run_benchmark.TaskRunner') as mock_runner_class:
                    mock_runner = MagicMock()
                    mock_runner.run_task.return_value = {"accuracy": 0.9, "status": "success"}
                    mock_runner_class.return_value = mock_runner
                    
                    # Mock report generation to avoid actual file writing
                    with patch('src.benchmark.run_benchmark.generate_csv_report'), \
                         patch('src.benchmark.run_benchmark.generate_pdf_report'), \
                         patch('src.benchmark.run_benchmark.update_artifact_timestamp'):
                        
                        main()
                        
                        # Verify TaskRunner was initialized
                        mock_runner_class.assert_called_once()
                        # Verify run_task was called for each seed
                        assert mock_runner.run_task.call_count == 2
        finally:
            os.chdir(original_cwd)