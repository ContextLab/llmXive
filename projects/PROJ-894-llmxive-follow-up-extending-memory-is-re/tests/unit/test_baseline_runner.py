"""
Unit tests for the baseline runner (T013).
"""
import pytest
import os
import sys
import json
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from strategies.baseline_runner import evaluate_task, load_tasks, ensure_output_dirs
from runner import TimeoutError

class TestBaselineRunner:
    """Tests for the baseline runner functionality."""

    def test_evaluate_task_accuracy_match(self):
        """Test that accuracy is 1.0 for exact string match."""
        task = {
            'task_id': 'test_1',
            'question': 'What is 2+2?',
            'context': 'Simple math problem.',
            'answer': '4'
        }
        
        # Mock the strategy to return a matching answer
        mock_strategy_result = {
            'answer': '4',
            'nodes_visited': 5,
            'status': 'completed'
        }
        
        with patch('strategies.baseline_runner.FullTraversal') as mock_strategy_class:
            mock_instance = MagicMock()
            mock_instance.run.return_value = mock_strategy_result
            mock_strategy_class.return_value = mock_instance
            
            result = evaluate_task(task, timeout=10)
            
            assert result['task_id'] == 'test_1'
            assert result['accuracy'] == 1.0
            assert result['status'] == 'completed'
            assert result['nodes_visited'] == 5

    def test_evaluate_task_accuracy_mismatch(self):
        """Test that accuracy is 0.0 for non-matching answers."""
        task = {
            'task_id': 'test_2',
            'question': 'What is 2+2?',
            'context': 'Simple math problem.',
            'answer': '4'
        }
        
        mock_strategy_result = {
            'answer': 'five',
            'nodes_visited': 3,
            'status': 'completed'
        }
        
        with patch('strategies.baseline_runner.FullTraversal') as mock_strategy_class:
            mock_instance = MagicMock()
            mock_instance.run.return_value = mock_strategy_result
            mock_strategy_class.return_value = mock_instance
            
            result = evaluate_task(task, timeout=10)
            
            assert result['accuracy'] == 0.0
            assert result['status'] == 'completed'

    def test_evaluate_task_timeout(self):
        """Test that timeout status is set correctly."""
        task = {
            'task_id': 'test_3',
            'question': 'Complex question?',
            'context': 'Context.',
            'answer': 'answer'
        }
        
        with patch('strategies.baseline_runner.FullTraversal') as mock_strategy_class:
            mock_instance = MagicMock()
            mock_instance.run.side_effect = TimeoutError("Task timed out")
            mock_strategy_class.return_value = mock_instance
            
            result = evaluate_task(task, timeout=1)
            
            assert result['status'] == 'timeout'
            assert result['latency_ms'] > 0

    def test_evaluate_task_degenerate_graph(self):
        """Test handling of degenerate graphs."""
        task = {
            'task_id': 'test_4',
            'question': 'Question?',
            'context': '',
            'answer': 'answer'
        }
        
        with patch('strategies.baseline_runner.FullTraversal') as mock_strategy_class:
            mock_instance = MagicMock()
            mock_instance.run.side_effect = Exception("Degenerate graph detected")
            mock_strategy_class.return_value = mock_instance
            
            result = evaluate_task(task, timeout=10)
            
            assert result['status'] == 'degenerate'

    def test_load_tasks_from_csv(self, tmp_path):
        """Test loading tasks from a CSV file."""
        # Create a temporary CSV file
        csv_file = tmp_path / "locomo.csv"
        csv_content = """task_id,question,context,answer
        task_1,What is X?,Context 1,Answer 1
        task_2,What is Y?,Context 2,Answer 2
        """
        csv_file.write_text(csv_content)
        
        # Mock the path check
        with patch('strategies.baseline_runner.project_root') as mock_root:
            mock_root.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = csv_file
            mock_root.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value.exists.return_value = True
            
            tasks = load_tasks(num_tasks=1)
            
            assert len(tasks) == 1
            assert tasks[0]['task_id'] == 'task_1'
            assert tasks[0]['question'] == 'What is X?'

    def test_output_schema(self):
        """Test that output matches required schema."""
        task = {
            'task_id': 'schema_test',
            'question': 'Test?',
            'context': 'Test context',
            'answer': 'test'
        }
        
        mock_result = {
            'answer': 'test',
            'nodes_visited': 10,
            'status': 'completed'
        }
        
        with patch('strategies.baseline_runner.FullTraversal') as mock_strategy_class:
            mock_instance = MagicMock()
            mock_instance.run.return_value = mock_result
            mock_strategy_class.return_value = mock_instance
            
            result = evaluate_task(task)
            
            # Check all required fields exist and have correct types
            assert isinstance(result['task_id'], str)
            assert isinstance(result['accuracy'], float)
            assert isinstance(result['nodes_visited'], int)
            assert isinstance(result['latency_ms'], float)
            assert isinstance(result['status'], str)
            
            # Check status values
            valid_statuses = ['completed', 'timeout', 'degenerate', 'unresolved']
            assert result['status'] in valid_statuses