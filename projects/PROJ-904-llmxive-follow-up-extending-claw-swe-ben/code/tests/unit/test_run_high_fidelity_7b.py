"""
Unit tests for T027: 7B High-Fidelity Execution Script.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from experiments.run_high_fidelity_7b import (
    load_filtered_instances,
    process_instance,
    get_strategy_function
)
from config import StrategyType
from experiments.batch_executor import ExecutionStatus

class TestRunHighFidelity7B:
    
    def test_get_strategy_function_valid(self):
        """Test that valid strategies return the correct function."""
        assert get_strategy_function(StrategyType.TF_IDF) is not None
        assert get_strategy_function(StrategyType.DIFF_AWARE) is not None
        assert get_strategy_function(StrategyType.SEMANTIC_SUMMARY) is not None
        assert get_strategy_function(StrategyType.NAIVE_TRUNCATION) is not None
    
    def test_get_strategy_function_invalid(self):
        """Test that invalid strategy raises ValueError."""
        with pytest.raises(ValueError):
            get_strategy_function("INVALID_STRATEGY")

    @patch('experiments.run_high_fidelity_7b.process_context')
    @patch('experiments.run_high_fidelity_7b.ModelRunner')
    def test_process_instance_success(self, mock_runner_class, mock_process_context):
        """Test successful processing of an instance."""
        # Setup mocks
        mock_instance = {
            'instance_id': 'test-123',
            'problem_statement': 'Fix bug X',
            'file_history': [{'path': 'a.py', 'content': 'def x(): pass'}]
        }
        mock_config = MagicMock()
        mock_snippets = MagicMock()
        mock_snippets.get_full_text.return_value = "Code context here"
        mock_process_context.return_value = mock_snippets
        
        mock_runner = MagicMock()
        mock_runner.generate.return_value = ("Fixed code here", {'time': 1.0})
        mock_runner_class.return_value = mock_runner
        
        # Call function
        result = process_instance(mock_instance, mock_runner, StrategyType.TF_IDF, timeout_per_instance=3600)
        
        # Assertions
        assert result['status'] == ExecutionStatus.SUCCESS.value
        assert result['instance_id'] == 'test-123'
        assert result['strategy'] == StrategyType.TF_IDF.value
        assert result['prediction'] == "Fixed code here"
        assert result['duration'] is not None
        assert result['duration'] >= 0

    @patch('experiments.run_high_fidelity_7b.process_context')
    @patch('experiments.run_high_fidelity_7b.ModelRunner')
    def test_process_instance_timeout(self, mock_runner_class, mock_process_context):
        """Test that timeout is handled correctly."""
        mock_instance = {
            'instance_id': 'test-timeout',
            'problem_statement': 'Fix bug',
            'file_history': []
        }
        mock_snippets = MagicMock()
        mock_snippets.get_full_text.return_value = "Context"
        mock_process_context.return_value = mock_snippets
        
        mock_runner = MagicMock()
        # Simulate slow generation
        mock_runner.generate.return_value = ("Slow code", {'time': 7200})
        mock_runner_class.return_value = mock_runner
        
        result = process_instance(mock_instance, mock_runner, StrategyType.TF_IDF, timeout_per_instance=60)
        
        assert result['status'] == ExecutionStatus.TIMEOUT.value
        assert result['duration'] > 60

    @patch('experiments.run_high_fidelity_7b.process_context')
    @patch('experiments.run_high_fidelity_7b.ModelRunner')
    def test_process_instance_empty_context(self, mock_runner_class, mock_process_context):
        """Test fallback or skip when context is empty."""
        mock_instance = {
            'instance_id': 'test-empty',
            'problem_statement': 'Fix bug',
            'file_history': []
        }
        mock_snippets = MagicMock()
        mock_snippets.snippets = [] # Empty
        mock_process_context.return_value = mock_snippets
        
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner
        
        result = process_instance(mock_instance, mock_runner, StrategyType.TF_IDF, timeout_per_instance=3600)
        
        assert result['status'] == ExecutionStatus.SKIPPED.value
        assert 'error' in result