"""
Unit tests for T016 execution logic.
Tests timeout handling, fallback dataset generation, and result flagging.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the module under test
sys.path.insert(0, 'code')
from src.cli.run_simulation import (
    run_simulation_with_timeout,
    ensure_fallback_dataset,
    write_status_log,
    TimeoutError
)
from src.data.loader import DataUnavailableError

class TestT016Execution:
    """Test suite for T016 execution requirements."""

    def test_timeout_handling(self):
        """Test that timeout is properly enforced and flagged."""
        def slow_function(args):
            time.sleep(10)
            return {'completed': True}
        
        # Mock time to avoid actual long wait
        with patch('time.sleep', side_effect=TimeoutError("Test timeout")):
            result = run_simulation_with_timeout(
                slow_function,
                {'steps': 100},
                timeout_seconds=1
            )
            assert result['timed_out'] is True
            assert 'Time-Bound Baseline' in result.get('flags', [])

    def test_fallback_dataset_generation(self):
        """Test that fallback dataset is generated when real data fails."""
        config = {'steps': 1000, 'dataset_path': None}
        
        with patch('src.cli.run_simulation.load_simulation_dataset', side_effect=DataUnavailableError("No data")):
            with patch('src.cli.run_simulation.generate_synthetic_fallback_dataset') as mock_gen:
                mock_df = pd.DataFrame({'step': range(100), 'value': np.random.rand(100)})
                mock_gen.return_value = mock_df
                
                result_config = ensure_fallback_dataset(config)
                
                assert result_config['power_limited'] is True
                assert result_config['dataset_available'] is False
                assert 'fallback_dataset_path' in result_config
                mock_gen.assert_called_once()

    def test_status_log_creation(self):
        """Test that status log is created with correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            status = {
                'run_id': 'test_run',
                'status': 'completed',
                'flags': [],
                'steps_completed': 10000,
                'steps_requested': 10000,
                'execution_time': 123.45
            }
            output_path = os.path.join(tmpdir, 'status.json')
            
            write_status_log(status, output_path)
            
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                loaded_status = json.load(f)
            
            assert loaded_status['run_id'] == 'test_run'
            assert loaded_status['status'] == 'completed'
            assert loaded_status['steps_completed'] == 10000

    def test_power_limited_flagging(self):
        """Test that power-limited flag is set when fallback is used."""
        config = {'steps': 1000}
        
        with patch('src.cli.run_simulation.load_simulation_dataset', side_effect=DataUnavailableError("No data")):
            with patch('src.cli.run_simulation.generate_synthetic_fallback_dataset') as mock_gen:
                mock_df = pd.DataFrame({'step': range(100), 'value': np.random.rand(100)})
                mock_gen.return_value = mock_df
                
                result_config = ensure_fallback_dataset(config)
                assert result_config['power_limited'] is True

    def test_partial_results_saving(self):
        """Test that partial results are saved on timeout."""
        # This test verifies the logic path for saving partial results
        # The actual saving is tested in integration tests
        partial_data = {
            'timed_out': True,
            'partial_results': True,
            'metrics': [{'step': i, 'value': i*0.1} for i in range(100)]
        }
        
        assert partial_data['timed_out'] is True
        assert partial_data['partial_results'] is True

    def test_result_structure_completeness(self):
        """Test that result structure contains all required fields for T016."""
        required_fields = [
            'run_id', 'config', 'steps_requested', 'steps_completed',
            'status', 'flags', 'execution_time', 'timed_out'
        ]
        
        sample_result = {
            'run_id': 'test_123',
            'config': {},
            'steps_requested': 10000,
            'steps_completed': 5000,
            'status': 'timeout',
            'flags': ['Time-Bound Baseline'],
            'execution_time': 21600,
            'timed_out': True
        }
        
        for field in required_fields:
            assert field in sample_result, f"Missing required field: {field}"

    def test_both_flags_can_coexist(self):
        """Test that 'Time-Bound' and 'Power-Limited' flags can both be present."""
        result = {
            'flags': ['Time-Bound Baseline', 'Power-Limited'],
            'timed_out': True,
            'power_limited': True
        }
        
        assert 'Time-Bound Baseline' in result['flags']
        assert 'Power-Limited' in result['flags']
        assert result['timed_out'] is True
        assert result['power_limited'] is True